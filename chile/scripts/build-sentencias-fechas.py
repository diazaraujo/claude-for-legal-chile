#!/usr/bin/env python3
"""Construye sentencias_fechas desde los page-*.json.gz de pjud.

sent_id (CorrelativoDocumentoId, = nombre del .txt) → fecha exacta de la
sentencia, rol, era, sala, caratulado, tipo_recurso, resultado, tribunal (dir).
Da la dimensión temporal al árbol normativo (citas × fecha) y a cualquier
análisis de evolución. Idempotente (INSERT OR REPLACE). Va a
citas_normativas.sqlite3 para no tocar corpus.fts mientras embebe.
"""
import gzip, json, re, sqlite3, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
PJUD = ROOT / "data/pjud"
OUT = ROOT / "data/_index/citas_normativas.sqlite3"

FIELDS = {
    "fecha": re.compile(r"<Fecha_Sentencia>([^<]+)<"),
    "rol": re.compile(r"<Rol>([^<]+)<"),
    "era": re.compile(r"<Era>([^<]+)<"),
    "sala": re.compile(r"<Sala>([^<]+)<"),
    "caratulado": re.compile(r"<Caratulado>([^<]+)<"),
    "tipo_recurso": re.compile(r"<TipoRecurso>([^<]+)<"),
    "resultado": re.compile(r"<ResultadoRecurso>([^<]+)<"),
}
RX_ID = re.compile(r"<CorrelativoDocumentoId>(\d+)<")


def _first(v):
    return v[0] if isinstance(v, list) and v else (v if v not in ([], "") else None)


def parse_page(path: str):
    tribunal = Path(path).parent.name
    rows = []
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        for doc in data.get("response", {}).get("docs", []):
            xml = doc.get("TEXTO_ETIQUETADO_t")
            xml = xml[0] if isinstance(xml, list) and xml else (xml or "")
            mid = RX_ID.search(xml)
            if mid:
                # esquema XML embebido (Corte Suprema / Apelaciones)
                vals = {k: (rx.search(xml).group(1).strip() if rx.search(xml) else None)
                        for k, rx in FIELDS.items()}
                fecha = (vals["fecha"] or "")[:10] or None
                rows.append((mid.group(1), fecha, vals["rol"], vals["era"], vals["sala"],
                             vals["caratulado"], vals["tipo_recurso"], vals["resultado"], tribunal))
                continue
            # esquema Solr plano (Laborales/Civiles/Familia/Cobranza/Penales…)
            sid = doc.get("crr_documento_id_i") or doc.get("id")
            if sid is None:
                continue
            fecha = (_first(doc.get("fec_sentencia_sup_dt")) or "")[:10] or None
            mat = doc.get("gls_materia_s")
            mat = "; ".join(mat) if isinstance(mat, list) else mat
            rows.append((str(sid), fecha, _first(doc.get("rol_era_sup_s")),
                         str(_first(doc.get("era_sup_i")) or "") or None,
                         _first(doc.get("gls_juz_s")), _first(doc.get("caratulado_s")),
                         mat, None, tribunal))
    except Exception as e:
        return path, str(e), []
    return path, None, rows


def main():
    files = sorted(str(p) for p in PJUD.rglob("page-*.json.gz"))
    print(f"páginas: {len(files)}", flush=True)
    conn = sqlite3.connect(str(OUT), timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias_fechas ("
        "sent_id TEXT PRIMARY KEY, fecha TEXT, rol TEXT, era TEXT, sala TEXT,"
        "caratulado TEXT, tipo_recurso TEXT, resultado TEXT, tribunal TEXT)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fechas_progreso (path TEXT PRIMARY KEY, n INTEGER, err TEXT)")
    done = {r[0] for r in conn.execute("SELECT path FROM fechas_progreso WHERE err IS NULL")}
    todo = [f for f in files if f not in done]
    print(f"pendientes: {len(todo)}", flush=True)

    t0, n, nerr = time.time(), 0, 0
    with ProcessPoolExecutor(max_workers=6) as pool:
        for i, (path, err, rows) in enumerate(pool.map(parse_page, todo, chunksize=20), 1):
            if rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO sentencias_fechas VALUES (?,?,?,?,?,?,?,?,?)", rows)
            conn.execute("INSERT OR REPLACE INTO fechas_progreso VALUES (?,?,?)",
                         (path, len(rows), err))
            n += len(rows)
            if err:
                nerr += 1
            if i % 500 == 0:
                conn.commit()
                el = time.time() - t0
                print(f"  [{i}/{len(todo)}] sentencias={n} err_pages={nerr} | {i/el:.0f} pages/s", flush=True)
    conn.commit()
    print(f"[DONE] {n} sentencias_fechas · páginas con error: {nerr} (quedan en fechas_progreso.err)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
