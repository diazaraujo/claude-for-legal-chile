#!/usr/bin/env python3
"""Vista DETALLADA de cobertura temporal (estilo Decide Mercado Público).

Heatmap de calendario por año (un cuadro por día, verde = día con data) +
resumen anual. Fuente daily-natural del corpus: Diario Oficial (una edición por
día). Lee el manifest (date DD-MM-YYYY, downloaded=pubs, status). Solo lectura.
"""
from __future__ import annotations
import sqlite3, sys, datetime, calendar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/diario-oficial/manifest.sqlite3"


def load_days() -> dict:
    """date(YYYY-MM-DD) -> pubs descargadas (0 si sin data)."""
    c = sqlite3.connect(f"file:{MANIFEST}?mode=ro", uri=True)
    days = {}
    for date, dl, status in c.execute("SELECT date, downloaded, status FROM descargas"):
        try:
            d, m, y = date.split("-")
            iso = f"{y}-{m}-{d}"
            days[iso] = max(days.get(iso, 0), dl or 0)
        except Exception:
            pass
    c.close()
    return days


def main():
    days = load_days()
    years = sorted({d[:4] for d in days}, reverse=True)
    # resumen anual
    resumen = []
    for y in years:
        yi = int(y)
        total = 366 if calendar.isleap(yi) else 365
        con = sum(1 for d, p in days.items() if d[:4] == y and p > 0)
        pubs = sum(p for d, p in days.items() if d[:4] == y)
        resumen.append((y, con, total, con/total*100, pubs))
    html = render(days, years, resumen)
    (ROOT / "COVERAGE-DETAIL.html").write_text(html)
    tot_pubs = sum(r[4] for r in resumen)
    print(f"[detail] {len(years)} años · {sum(r[1] for r in resumen)} días con data · "
          f"{tot_pubs:,} pubs → COVERAGE-DETAIL.html")


def year_grid(days: dict, y: str) -> str:
    """Grid de días del año (7 filas = día de semana, columnas = semanas)."""
    yi = int(y)
    d0 = datetime.date(yi, 1, 1)
    total = 366 if calendar.isleap(yi) else 365
    cells = []
    for n in range(total):
        d = d0 + datetime.timedelta(days=n)
        iso = d.isoformat()
        p = days.get(iso, None)
        if p is None:
            col, t = "#ebedef", "sin registro"
        elif p > 0:
            # intensidad por nº de pubs
            col = "#1a7f37" if p >= 15 else ("#3fb950" if p >= 5 else "#90d8a0")
            t = f"{p} pubs"
        else:
            col, t = "#d0d7de", "sin data"
        wd = d.weekday()           # 0=lunes
        wk = (n + d0.weekday()) // 7
        cells.append(f'<div class="c" style="background:{col};grid-row:{wd+1};grid-column:{wk+1}" title="{iso}: {t}"></div>')
    return f'<div class="grid">{"".join(cells)}</div>'


def render(days, years, resumen) -> str:
    cards = []
    for y in years:
        r = next(x for x in resumen if x[0] == y)
        pct = r[3]
        cards.append(f"""<div class="card">
<div class="hd"><h2>{y}</h2><div class="cov">{pct:.1f}% de cobertura · {r[1]} de {r[2]} días con data</div></div>
<p class="hint">Pasa el cursor sobre una celda para ver el día.</p>
{year_grid(days, y)}
</div>""")
    rows = "".join(f"<tr><td>{r[0]}</td><td class='n'>{r[1]}</td><td class='n'>{r[2]}</td>"
                   f"<td class='n' style='color:{'#1a7f37' if r[3]>=99 else '#bf8700' if r[3]>=90 else '#cf222e'}'>{r[3]:.1f}%</td>"
                   f"<td class='n'>{r[4]:,}</td></tr>" for r in resumen)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cobertura temporal · Diario Oficial · claude-legal-chile</title><style>
body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
.wrap{{max-width:1100px;margin:0 auto;padding:28px}}
h1{{font-size:22px;margin:0 0 2px}} .meta{{color:#57606a;margin-bottom:22px}}
.card{{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:22px 26px;margin-bottom:18px}}
.hd{{display:flex;justify-content:space-between;align-items:baseline}} .hd h2{{margin:0;font-size:20px}}
.cov{{color:#57606a;font-size:13px}} .hint{{color:#8c959f;font-size:12px;margin:6px 0 14px}}
.grid{{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,11px);gap:3px}}
.c{{width:11px;height:11px;border-radius:2px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:10px;overflow:hidden;margin-top:10px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #eaeef2;font-size:13px}}
th{{background:#f6f8fa;font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:#57606a}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}
.leg{{margin:14px 0;color:#57606a;font-size:12px}} .sw{{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:middle;margin:0 3px}}
</style></head><body><div class="wrap">
<h1>Cobertura temporal · Diario Oficial</h1>
<div class="meta">claude-legal-chile · días con data por año · generado 2026-05-30</div>
<div class="leg">Cobertura por día:
<span class="sw" style="background:#1a7f37"></span>≥15 pubs
<span class="sw" style="background:#3fb950"></span>5-14
<span class="sw" style="background:#90d8a0"></span>1-4
<span class="sw" style="background:#d0d7de"></span>sin data
<span class="sw" style="background:#ebedef"></span>sin registro</div>
{''.join(cards)}
<div class="card"><h2 style="font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#57606a;margin:0 0 8px">Resumen anual</h2>
<table><thead><tr><th>Año</th><th class="n">Días con data</th><th class="n">Días totales</th><th class="n">% Cobertura</th><th class="n">Pubs capturadas</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</div></body></html>"""


if __name__ == "__main__":
    sys.exit(main())
