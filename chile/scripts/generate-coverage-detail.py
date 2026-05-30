#!/usr/bin/env python3
"""Vista DETALLADA de cobertura temporal por fuente (estilo Mercado Público).

Por fuente con señal de fecha: cobertura anual (docs/año, rango, años faltantes)
+ heatmap de calendario donde la fecha es a nivel día y confiable. Genera
COVERAGE-DETAIL.html + COVERAGE-GAPS.json (gaps levantados). Solo lectura.
"""
from __future__ import annotations
import sqlite3, glob, re, sys, json, datetime, calendar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# por fuente: (columna_fecha, granularidad, confiable_doc_date, organismo)
# confiable=False → la fecha es de scrape/upload (no del documento) → solo informativa
CFG = {
 "diario-oficial":  ("date",          "day",  True,  "Diario Oficial"),
 "cgr-dictamenes":  ("ventana",       "month",True,  "Contraloría (CGR)"),
 "suseso":          ("fecha",         "day",  True,  "SUSESO"),
 "cortes-marciales":("fecha",         "day",  True,  "Cortes Marciales"),
 "fne":             ("date",          "day",  True,  "FNE"),
 "sii-oficios":     ("anio",          "year", True,  "SII oficios"),
 "dt":              ("year",          "year", True,  "Dirección del Trabajo"),
 "cmf":             ("year",          "year", True,  "CMF"),
 "sii":             ("year",          "year", True,  "SII (legacy)"),
 "tdpi":            ("year",          "year", True,  "TDPI"),
 "dga":             ("date_gmt",      "day",  False, "DGA (aguas)"),
 "subtrans":        ("date_gmt",      "day",  False, "SUBTRANS"),
 "tcp":             ("date_gmt",      "day",  False, "Trib. Contratación Púb."),
 "tricel":          ("date_gmt",      "day",  False, "TRICEL"),
 "tdlc":            ("date",          "day",  False, "TDLC"),
 "tc-moderno":      ("fecha",         "day",  False, "TC (moderno)"),
}

# Fuentes cuya fecha REAL del documento está en el filename o título (no en una
# columna fecha confiable del manifest). (modo, regex con grupo de fecha).
CFG_DISK = {
 # DGA: título "Resolucion_N19_de_20230106" → YYYYMMDD
 "dga":            ("title",    r"_de_(\d{8})\b",            "day",  "DGA (aguas)"),
 # SEC: filename "rex_1664-2007.pdf" → año
 "sec":            ("filename", r"-(\d{4})\.",               "year", "SEC"),
 # Trib. Ambientales: filename "R-279-2021_26-07-2023_..." → fecha sentencia
 "tribunales-ambientales": ("filename", r"_(\d{2}-\d{2}-\d{4})_", "day", "Trib. Ambientales"),
}


def parse_date(v):
    """→ (year, month, day) ; month/day None si no aplica. None si no parsea."""
    if v is None: return None
    s = str(v).strip()
    if not s: return None
    if re.fullmatch(r"(19|20)\d\d", s): return (int(s), None, None)
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)          # ISO / YYYY-MM
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
    m = re.match(r"(\d{2})[/-](\d{2})[/-](\d{4})", s)         # DD/MM/YYYY o DD-MM-YYYY
    if m: return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def extract(src, col):
    man = glob.glob(str(DATA / src / "manifest.sqlite*"))
    if not man: return []
    c = sqlite3.connect(f"file:{man[0]}?mode=ro", uri=True)
    t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
         if not r[0].startswith("sqlite")][0]
    out = []
    for (v,) in c.execute(f"SELECT {col} FROM {t} WHERE {col} IS NOT NULL AND {col} != ''"):
        p = parse_date(v)
        if p: out.append(p)
    c.close()
    return out


def extract_disk(src, mode, pattern):
    """Extrae fecha del título (manifest) o del filename con regex."""
    rx = re.compile(pattern)
    out = []
    if mode == "title":
        man = glob.glob(str(DATA / src / "manifest.sqlite*"))
        if not man: return []
        c = sqlite3.connect(f"file:{man[0]}?mode=ro", uri=True)
        t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if not r[0].startswith("sqlite")][0]
        vals = [r[0] for r in c.execute(f"SELECT title FROM {t} WHERE title IS NOT NULL")]
        c.close()
    else:  # filename
        vals = [p.name for p in (DATA / src).rglob("*") if p.is_file()]
    for v in vals:
        m = rx.search(str(v))
        if not m: continue
        s = m.group(1)
        if len(s) == 8 and s.isdigit():      # YYYYMMDD
            p = (int(s[:4]), int(s[4:6]), int(s[6:8]))
        else:
            p = parse_date(s)
        if p: out.append(p)
    return out


def main():
    sources = {}
    gaps = []
    for src, (col, gran, reliable, org) in CFG.items():
        dates = extract(src, col)
        if not dates: continue
        byyear = {}
        for y, m, d in dates:
            byyear[y] = byyear.get(y, 0) + 1
        ys = sorted(byyear)
        # day-level map (ISO->count) si gran==day
        byday = {}
        if gran == "day":
            for y, m, d in dates:
                if m and d:
                    try:
                        byday[datetime.date(y, m, d).isoformat()] = byday.get(datetime.date(y, m, d).isoformat(), 0) + 1
                    except Exception:
                        pass
        sources[src] = dict(org=org, gran=gran, reliable=reliable, byyear=byyear, byday=byday,
                            total=len(dates), ymin=ys[0], ymax=ys[-1])
        # GAPS: años faltantes en el rango + años con pocos docs
        full = set(range(ys[0], ys[-1] + 1))
        missing = sorted(full - set(ys))
        if missing:
            gaps.append(dict(fuente=src, org=org, tipo="años_faltantes",
                             detalle=f"{len(missing)} años sin docs en {ys[0]}-{ys[-1]}: {missing[:8]}"))
        if not reliable:
            gaps.append(dict(fuente=src, org=org, tipo="fecha_no_confiable",
                             detalle=f"fecha es de scrape/upload ({col}), no del documento — cobertura temporal informativa"))

    # Fuentes con fecha REAL en filename/título (override las no-confiables)
    for src, (mode, pattern, gran, org) in CFG_DISK.items():
        dates = extract_disk(src, mode, pattern)
        if not dates: continue
        byyear = {}
        for y, m, d in dates:
            byyear[y] = byyear.get(y, 0) + 1
        ys = sorted(byyear)
        byday = {}
        if gran == "day":
            for y, m, d in dates:
                if m and d:
                    try:
                        iso = datetime.date(y, m, d).isoformat()
                        byday[iso] = byday.get(iso, 0) + 1
                    except Exception:
                        pass
        sources[src] = dict(org=org, gran=gran, reliable=True, byyear=byyear, byday=byday,
                            total=len(dates), ymin=ys[0], ymax=ys[-1])
        # quitar el gap de "fecha_no_confiable" de esta fuente (ahora sí tiene fecha real)
        gaps = [g for g in gaps if not (g["fuente"] == src and g["tipo"] == "fecha_no_confiable")]
        full = set(range(ys[0], ys[-1] + 1))
        missing = sorted(full - set(ys))
        if missing:
            gaps.append(dict(fuente=src, org=org, tipo="años_faltantes",
                             detalle=f"{len(missing)} años sin docs en {ys[0]}-{ys[-1]}: {missing[:8]}"))

    json.dump(gaps, open(ROOT / "COVERAGE-GAPS.json", "w"), ensure_ascii=False, indent=2)
    (ROOT / "COVERAGE-DETAIL.html").write_text(render(sources, gaps))
    print(f"[detail] {len(sources)} fuentes con fecha · {len(gaps)} gaps levantados")
    for g in gaps:
        print(f"  ⚠️ {g['org']}: {g['detalle']}")


def daygrid(byday, y):
    yi = int(y); d0 = datetime.date(yi, 1, 1)
    total = 366 if calendar.isleap(yi) else 365
    cells = []
    for n in range(total):
        d = d0 + datetime.timedelta(days=n); iso = d.isoformat()
        p = byday.get(iso, 0)
        col = "#ebedef" if p == 0 else ("#1a7f37" if p >= 10 else "#3fb950" if p >= 3 else "#90d8a0")
        cells.append(f'<div class="c" style="background:{col};grid-row:{d.weekday()+1};grid-column:{(n+d0.weekday())//7+1}" title="{iso}: {p}"></div>')
    return f'<div class="grid">{"".join(cells)}</div>'


def render(sources, gaps):
    secs = []
    for src, s in sorted(sources.items(), key=lambda kv: -kv[1]["total"]):
        ys = sorted(s["byyear"], reverse=True)
        rel = "" if s["reliable"] else ' <span class="warn">⚠ fecha de scrape, no del doc</span>'
        # resumen anual (barras)
        mx = max(s["byyear"].values())
        bars = "".join(
            f'<div class="yr"><span class="yl">{y}</span>'
            f'<div class="yb"><div class="yf" style="width:{s["byyear"][y]/mx*100:.0f}%"></div></div>'
            f'<span class="yn">{s["byyear"][y]:,}</span></div>' for y in ys)
        # calendario de los 3 años más recientes si day-level confiable
        cal = ""
        if s["gran"] == "day" and s["byday"]:
            for y in ys[:3]:
                con = sum(1 for d, p in s["byday"].items() if d[:4] == str(y) and p > 0)
                tot = 366 if calendar.isleap(int(y)) else 365
                cal += f'<div class="cy"><div class="ch"><b>{y}</b> · {con}/{tot} días ({con/tot*100:.0f}%)</div>{daygrid(s["byday"], y)}</div>'
        secs.append(f"""<div class="card">
<div class="hd"><h2>{s['org']}{rel}</h2><div class="cov">{s['total']:,} docs · {s['ymin']}–{s['ymax']}</div></div>
<div class="cols"><div class="yrs">{bars}</div><div class="cals">{cal}</div></div>
</div>""")
    gaps_html = "".join(f'<tr><td><b>{g["org"]}</b></td><td>{g["tipo"]}</td><td>{g["detalle"]}</td></tr>' for g in gaps)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cobertura temporal detallada · claude-legal-chile</title><style>
body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
.wrap{{max-width:1140px;margin:0 auto;padding:28px}} h1{{font-size:22px;margin:0 0 2px}}
.meta{{color:#57606a;margin-bottom:20px}}
.card{{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:20px 24px;margin-bottom:16px}}
.hd{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}} .hd h2{{margin:0;font-size:18px}}
.cov{{color:#57606a;font-size:13px}} .warn{{color:#bf8700;font-size:11px;font-weight:400}}
.cols{{display:flex;gap:26px}} .yrs{{flex:0 0 360px}} .cals{{flex:1}}
.yr{{display:flex;align-items:center;gap:8px;margin:2px 0;font-size:12px}}
.yl{{width:38px;color:#57606a;text-align:right}} .yb{{flex:1;background:#eaeef2;border-radius:4px;height:13px}}
.yf{{height:100%;background:#0969da;border-radius:4px}} .yn{{width:54px;text-align:right;font-variant-numeric:tabular-nums}}
.cy{{margin-bottom:10px}} .ch{{font-size:12px;color:#57606a;margin-bottom:4px}}
.grid{{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,9px);gap:2px}} .c{{width:9px;height:9px;border-radius:2px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #eaeef2;font-size:13px}}
th{{background:#f6f8fa;font-size:11px;text-transform:uppercase;color:#57606a}}
h3{{margin:26px 0 8px;font-size:15px}}
</style></head><body><div class="wrap">
<h1>Cobertura temporal detallada</h1>
<div class="meta">claude-legal-chile · {len(sources)} fuentes con fecha · barras = docs/año · calendario = días con data (3 años recientes) · generado 2026-05-30</div>
{''.join(secs)}
<h3>⚠️ Gaps levantados</h3>
<table><thead><tr><th>Fuente</th><th>Tipo</th><th>Detalle</th></tr></thead><tbody>{gaps_html}</tbody></table>
</div></body></html>"""


if __name__ == "__main__":
    sys.exit(main())
