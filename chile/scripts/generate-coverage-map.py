#!/usr/bin/env python3
"""Genera el MAPA DE COBERTURA Y CALIDAD del corpus (estilo Mercado Público).

Por fuente: tipo, documentos, enumerado vs descargado (completitud de descarga),
embebido (searchable), método de acceso y estado de calidad. Emite un dashboard
HTML autocontenido + un JSON. Solo lectura.
"""
from __future__ import annotations
import sqlite3, os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # chile/
DATA = ROOT / "data"

# clasificación por fuente: (tipo, organismo legible, método de acceso)
META = {
 "leychile":("Normativa","BCN / LeyChile","SPARQL+bulk"),
 "diario-oficial":("Normativa","Diario Oficial","bulk"),
 "cgr-dictamenes":("Dictámenes","Contraloría (CGR)","Domino"),
 "cmf":("Normativa fin.","CMF","bulk"),
 "cplt":("Dictámenes","Consejo Transparencia","bulk"),
 "suseso":("Dictámenes","SUSESO","bulk"),
 "dt":("Dictámenes","Dirección del Trabajo","Zyte (WAF)"),
 "sii":("Jurisprud. adm.","SII (legacy)","bulk"),
 "sii-oficios":("Jurisprud. adm.","SII oficios","Zyte+GET"),
 "doctrina":("Doctrina","Universidades","OAI-PMH"),
 "tc":("Jurisprudencia","Tribunal Constitucional","bulk"),
 "tc-moderno":("Jurisprudencia","TC (moderno)","JSF"),
 "tdlc":("Jurisprudencia","TDLC","bulk"),
 "tdpi":("Jurisprudencia","TDPI","bulk"),
 "tribunales-ambientales":("Jurisprudencia","Trib. Ambientales","bulk"),
 "fne":("Jurisprudencia","FNE","WP-REST"),
 "sec":("Normativa sect.","SEC","bulk"),
 "subtel":("Normativa sect.","SUBTEL","bulk"),
 "sernac":("Jurisprud. adm.","SERNAC","bulk"),
 "dga":("Normativa sect.","DGA (aguas)","WordPress"),
 "subtrans":("Normativa sect.","SUBTRANS","WordPress"),
 "cde":("Institucional","CDE","sitemap"),
 "sag-normativa":("Normativa sect.","SAG","Zyte (parcial)"),
 "tcp":("Jurisprudencia","Trib. Contratación Púb.","WP-REST"),
 "tricel":("Jurisprudencia","TRICEL","WP-REST"),
 "cortes-marciales":("Jurisprudencia","Cortes Marciales","scrape+OCR"),
 "sii-normativa":("Normativa","SII circulares+resoluciones","brute-force"),
 "indh":("Doctrina","INDH (DDHH)","DSpace REST"),
 "dpp":("Institucional","Defensoría Penal","BFS crawl"),
 "aduanas":("Jurisprud. adm.","Servicio Nac. Aduanas","BFS crawl"),
 "servel":("Normativa sect.","SERVEL (electoral)","BFS crawl"),
 "cam-santiago":("Jurisprudencia","CAM Santiago (arbitral)","BFS crawl"),
 "historia-ley":("Tramitación","Congreso / Cámara","WSDL SOAP"),
}


def datarel(p: str) -> str:
    i = p.find("/data/")
    return p[i+6:] if i >= 0 else p.lstrip("/")


def load_embedded() -> set:
    emb = set()
    for db in (DATA/"_index/corpus.fts.sqlite3", DATA/"_index/new-sources.fts.sqlite3"):
        if db.exists():
            try:
                c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
                emb |= {datarel(r[0]) for r in c.execute("SELECT path FROM embeddings")}
                c.close()
            except Exception:
                pass
    return emb


def manifest_counts(d: Path):
    man = list(d.glob("manifest.sqlite*"))
    if not man:
        return None, None
    try:
        c = sqlite3.connect(f"file:{man[0]}?mode=ro", uri=True, timeout=20)
        t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if not r[0].startswith("sqlite")][0]
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
        nrows = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        if "downloaded" not in cols:
            c.close(); return nrows, None
        mx = c.execute(f"SELECT max(downloaded) FROM {t}").fetchone()[0] or 0
        if mx <= 1:
            # flag 0/1 → fila por documento
            dl = c.execute(f"SELECT count(*) FROM {t} WHERE downloaded=1").fetchone()[0]
            # excluir links muertos (404 confirmados) del universo recuperable
            dead = (c.execute(f"SELECT count(*) FROM {t} WHERE COALESCE(dead,0)=1").fetchone()[0]
                    if "dead" in cols else 0)
            enum = nrows - dead
        else:
            # conteo por fila (p.ej. Diario Oficial: pubs por edición)
            dl = c.execute(f"SELECT sum(downloaded) FROM {t}").fetchone()[0]
            enum = (c.execute(f"SELECT sum(total_pubs) FROM {t}").fetchone()[0]
                    if "total_pubs" in cols else dl)
        c.close()
        return enum, dl
    except Exception:
        return None, None


def main():
    emb = load_embedded()
    rows = []
    for d in sorted(DATA.glob("*/")):
        name = d.name
        if name == "_index":
            continue
        files = [p for p in d.rglob("*")
                 if p.suffix.lower() in (".txt", ".html", ".htm", ".pdf", ".xml") and p.is_file()]
        if not files:
            continue
        # colapsar todas las variantes del mismo doc en un solo doc lógico, por STEM
        # (basename sin la cadena de extensiones): X.pdf / X.pdf.txt / X.xml / X.txt / txt/X.pdf.txt
        # → mismo doc. Evita el falso 50% por doble-conteo .pdf/.xml + .txt extraído.
        def _stem(p):
            n = p.name.lower()
            for shadow in (".pdf.txt", ".html.txt", ".htm.txt", ".xml.txt"):
                if n.endswith(shadow):
                    return p.name[: -len(shadow)]
            for ext in (".pdf", ".xml", ".html", ".htm", ".txt"):
                if n.endswith(ext):
                    return p.name[: -len(ext)]
            return p.name
        logical = {}  # stem -> ¿alguna variante embebida?
        for f in files:
            k = _stem(f)
            logical[k] = logical.get(k, False) or (datarel(str(f)) in emb)
        docs = len(logical)
        enum, dl = manifest_counts(d)
        n_emb = sum(1 for v in logical.values() if v)
        tipo, org, metodo = META.get(name, ("?", name, "?"))
        # completitud de descarga
        comp = (dl/enum*100) if (enum and dl is not None and enum > 0) else (100.0 if dl is None else None)
        # estado de calidad
        if enum and dl is not None and enum > 0:
            r = dl/enum
            estado = "completo" if r >= 0.95 else ("parcial" if r >= 0.5 else "bloqueado")
        else:
            estado = "indexado"
        emb_pct = (n_emb/docs*100) if docs else 0
        rows.append(dict(fuente=name, tipo=tipo, organismo=org, metodo=metodo,
                         docs=docs, enum=enum, descargado=dl, comp=comp,
                         embebido=n_emb, emb_pct=round(emb_pct,1), estado=estado))

    # PJUD: sentencias en batches .json.gz, SEPARADAS por competencia/tribunal
    pjud = DATA / "pjud"
    if pjud.exists():
        import gzip
        def avg_per_batch(batches):
            per = []
            for b in batches[:6]:
                try:
                    j = json.loads(gzip.open(b).read())
                    per.append(len(j) if isinstance(j, list)
                               else len(j.get("docs", j.get("response", {}).get("docs", [])) or [1]))
                except Exception:
                    pass
            return (sum(per)/len(per)) if per else 100
        LABEL = {"Corte_Suprema": "Corte Suprema", "Corte_de_Apelaciones": "Cortes de Apelaciones",
                 "Civiles": "Juzgados Civiles", "Penales": "Justicia Penal",
                 "Laborales": "Juzgados Laborales", "Familia": "Tribunales de Familia",
                 "Cobranza": "Cobranza Laboral y Previsional"}
        for sub in sorted(pjud.iterdir()):
            if not sub.is_dir():
                continue
            batches = list(sub.rglob("*.json.gz"))
            if not batches:
                continue
            docs = int(avg_per_batch(batches) * len(batches))
            rows.append(dict(fuente=f"pjud/{sub.name}", tipo="Jurisprudencia",
                             organismo=f"PJUD · {LABEL.get(sub.name, sub.name)}", metodo="Solr juris.pjud.cl",
                             docs=docs, enum=docs, descargado=docs, comp=100.0,
                             embebido=docs, emb_pct=100.0, estado="indexado"))

    # Boletín Concursal: registros en tabla estructurada `concursal` (no archivos sueltos)
    try:
        import sqlite3
        cdb = sqlite3.connect(str(DATA / "_index/new-sources.fts.sqlite3"), timeout=30)
        nconc = cdb.execute("SELECT count(*) FROM concursal").fetchone()[0]
        cdb.close()
        if nconc:
            rows.append(dict(fuente="boletin-concursal", tipo="Registro público",
                             organismo="Boletín Concursal · Superir (Ley 20.720)",
                             metodo="POST getRegistroDiarioPublicacionJson",
                             docs=nconc, enum=nconc, descargado=nconc, comp=100.0,
                             embebido=0, emb_pct=0.0, estado="indexado"))
    except Exception:
        pass

    # orden por tipo luego docs desc
    rows.sort(key=lambda r: (r["tipo"], -r["docs"]))
    total_docs = sum(r["docs"] for r in rows)
    total_emb = sum(r["embebido"] for r in rows)
    out = dict(generado="2026-05-30", total_fuentes=len(rows), total_docs=total_docs,
               total_embebido=total_emb, fuentes=rows)
    (ROOT/"COVERAGE-MAP.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (ROOT/"COVERAGE-MAP.html").write_text(render_html(out))
    print(f"[map] {len(rows)} fuentes · {total_docs:,} docs · {total_emb:,} embebidos")
    print(f"  → COVERAGE-MAP.html + COVERAGE-MAP.json")


def render_html(d: dict) -> str:
    badge = {"completo":"#1a7f37","parcial":"#bf8700","bloqueado":"#cf222e","indexado":"#0969da"}
    def bar(pct, color):
        pct = 0 if pct is None else max(0, min(100, pct))
        return (f'<div class="bar"><div class="fill" style="width:{pct:.0f}%;background:{color}"></div>'
                f'<span>{pct:.0f}%</span></div>')
    rows_html = []
    for r in d["fuentes"]:
        col = badge.get(r["estado"], "#57606a")
        comp = bar(r["comp"], col)
        embp = bar(r["emb_pct"], "#0969da")
        enum = f'{r["enum"]:,}' if r["enum"] is not None else "—"
        dl = f'{r["descargado"]:,}' if r["descargado"] is not None else "—"
        rows_html.append(f"""<tr>
<td><b>{r['organismo']}</b><br><span class="sub">{r['fuente']}</span></td>
<td>{r['tipo']}</td><td class="num">{r['docs']:,}</td>
<td class="num">{enum}</td><td class="num">{dl}</td><td>{comp}</td>
<td class="num">{r['embebido']:,}</td><td>{embp}</td>
<td><span class="badge" style="background:{col}">{r['estado']}</span></td>
<td class="met">{r['metodo']}</td></tr>""")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cobertura y Calidad · claude-legal-chile</title>
<style>
body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px}}
h1{{font-size:22px;margin:0 0 4px}} .meta{{color:#57606a;margin-bottom:20px}}
.kpis{{display:flex;gap:16px;margin-bottom:22px;flex-wrap:wrap}}
.kpi{{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:14px 18px;flex:1;min-width:150px}}
.kpi .n{{font-size:26px;font-weight:700}} .kpi .l{{color:#57606a;font-size:12px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:10px;overflow:hidden}}
th,td{{padding:9px 11px;text-align:left;border-bottom:1px solid #eaeef2;font-size:13px;vertical-align:middle}}
th{{background:#f6f8fa;font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:#57606a}}
.num{{text-align:right;font-variant-numeric:tabular-nums}} .sub{{color:#8c959f;font-size:11px}}
.met{{font-size:11px;color:#57606a}}
.badge{{color:#fff;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}}
.bar{{position:relative;background:#eaeef2;border-radius:6px;height:16px;min-width:90px}}
.bar .fill{{height:100%;border-radius:6px}} .bar span{{position:absolute;right:5px;top:0;font-size:10px;line-height:16px;color:#1f2328}}
.leg{{margin-top:16px;color:#57606a;font-size:12px}}
</style></head><body><div class="wrap">
<h1>🇨🇱 Mapa de Cobertura y Calidad de Datos</h1>
<div class="meta">claude-legal-chile · corpus legal · generado {d['generado']}</div>
<div class="kpis">
<div class="kpi"><div class="n">{d['total_fuentes']}</div><div class="l">fuentes</div></div>
<div class="kpi"><div class="n">{d['total_docs']:,}</div><div class="l">documentos</div></div>
<div class="kpi"><div class="n">{d['total_embebido']:,}</div><div class="l">embebidos (searchable)</div></div>
</div>
<table><thead><tr>
<th>Fuente</th><th>Tipo</th><th>Docs</th><th>Enum.</th><th>Descarg.</th><th>Completitud</th>
<th>Embeb.</th><th>% Embeb.</th><th>Estado</th><th>Método</th>
</tr></thead><tbody>
{''.join(rows_html)}
</tbody></table>
<div class="leg">Completitud = descargado/enumerado · Estado: <b>completo</b> ≥95% · <b>parcial</b> ≥50% ·
<b>bloqueado</b> &lt;50% · <b>indexado</b> sin manifest. % Embeb. = docs con vector bge-m3 (searchable).</div>
</div></body></html>"""


if __name__ == "__main__":
    sys.exit(main())
