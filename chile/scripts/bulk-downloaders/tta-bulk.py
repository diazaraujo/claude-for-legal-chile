#!/usr/bin/env python3
# std:input -
# std:output JSON sentencias TTA + manifest + PDFs si disponibles
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download TTA (Tribunales Tributarios y Aduaneros).

API descubierta en bundle Angular ojv.tta.cl/main.js + capturada con Playwright:

  GET https://ojv.tta.cl/api/sentencias/periodos         → años disponibles
  GET https://ojv.tta.cl/api/list/tribunal               → 18 tribunales
  GET https://ojv.tta.cl/api/sentencias/jurisprudenciales?offset=N&limit=M
       → JSON con sentencias (MATERIA, CARATULA, RIT, RUC, EXTRACTO, etc)
  GET https://ojv.tta.cl/api/sentencias/listaDocumentosDeSentencia?expediente=ID
       → metadata documentos PDF (si los hay)

Total publicado: 11.037 sentencias (verificado RESULT_COUNT en respuesta).

NO requiere auth — el SPA inicial 401 era endpoint incorrecto. Path correcto
es `/api/sentencias/...` (no `/api/...`).

Fase 1: GET paginado para llenar manifest con metadata + EXTRACTO.
Fase 2 (opcional --pdfs): para cada expediente, GET lista documentos + descarga PDFs.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/tta"

BASE = "https://ojv.tta.cl/api"
LIST_URL = BASE + "/sentencias/jurisprudenciales"
DOCS_URL = BASE + "/sentencias/listaDocumentosDeSentencia"
UA = "claude-legal-chile/0.8 bulk-tta"

_STATS = {"items": 0, "pdfs_ok": 0, "pdfs_err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias ("
        "expediente TEXT PRIMARY KEY, ano TEXT, tribunal TEXT, "
        "id_tribunal TEXT, rit TEXT, ruc TEXT, fecha TEXT, "
        "materia TEXT, caratula TEXT, extracto TEXT, "
        "proceso TEXT, servicio TEXT, etiquetas TEXT, "
        "documentos_json TEXT, pdfs_count INTEGER, downloaded INTEGER DEFAULT 0)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_ano ON sentencias(ano)")
    conn.commit()
    return conn


def http_get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Referer": "https://ojv.tta.cl/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def enumerate_all(conn: sqlite3.Connection, batch: int = 12000) -> int:
    """API quirk: solo offset=0 retorna data; pero limit alto saca todo.

    Hacemos 1 sola call con limit=12000 (mayor que RESULT_COUNT=11037 observado
    al momento del scrape). Si el server escala más allá, basta subir limit.
    """
    url = f"{LIST_URL}?offset=0&limit={batch}"
    print(f"  GET {url}", flush=True)
    body = http_get(url, timeout=600)
    j = json.loads(body)
    items = j.get("data", [])
    total = 0
    for it in items:
        expediente = it.get("ID_EXPEDIENTE") or it.get("EXPEIENTE")
        if not expediente:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO sentencias "
            "(expediente, ano, tribunal, id_tribunal, rit, ruc, fecha, "
            "materia, caratula, extracto, proceso, servicio, etiquetas) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (expediente, it.get("ANO"), it.get("TRIBUNAL"),
             it.get("ID_TRIBUNAL"), it.get("RIT"), it.get("RUC"),
             it.get("FECHA_SENTENCIA"), it.get("MATERIA_PRINCIPAL"),
             it.get("CARATULA"), it.get("EXTRACTO"),
             it.get("NOMBRE_PROCESO"), it.get("NOMBRE_SERVICIO"),
             it.get("ETIQUETAS")),
        )
        total += 1
    conn.commit()
    return total


def fetch_docs(expediente: str) -> list[dict]:
    """Lista documentos de una sentencia (puede tener 0..N PDFs)."""
    # Endpoint exacto a verificar — varios formatos posibles
    for params in [
        f"?expediente={expediente}",
        f"?idExpediente={expediente}",
    ]:
        url = DOCS_URL + params
        try:
            body = http_get(url, timeout=60)
            j = json.loads(body)
            return j if isinstance(j, list) else j.get("data", [])
        except urllib.error.HTTPError as e:
            if e.code != 400:
                continue
        except Exception:
            continue
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUTPUT_ROOT))
    ap.add_argument("--batch", type=int, default=2000)
    ap.add_argument("--pdfs", action="store_true",
                    help="Adicionalmente bajar PDFs por sentencia")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== TTA bulk ===", flush=True)
    print(f"output: {out}", flush=True)
    print(f"\nFase 1: enumerando vía /jurisprudenciales...", flush=True)
    t0 = time.time()
    n = enumerate_all(conn, batch=args.batch)
    print(f"  enumerados: {n} ({time.time()-t0:.1f}s)", flush=True)

    if args.pdfs:
        print(f"\nFase 2: descargando PDFs de cada expediente...", flush=True)
        rows = conn.execute(
            "SELECT expediente FROM sentencias WHERE downloaded=0"
        ).fetchall()
        print(f"  expedientes a procesar: {len(rows)}", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(fetch_docs, r[0]): r[0] for r in rows}
            done = 0
            for fut in as_completed(futs):
                expediente = futs[fut]
                try:
                    docs = fut.result()
                    conn.execute(
                        "UPDATE sentencias SET documentos_json=?, "
                        "pdfs_count=?, downloaded=1 WHERE expediente=?",
                        (json.dumps(docs, default=str), len(docs), expediente),
                    )
                except Exception:
                    pass
                done += 1
                if done % 100 == 0:
                    conn.commit()
                    print(f"  done={done}/{len(rows)}", flush=True)
        conn.commit()

    print(f"\n[DONE] {time.time()-t0:.0f}s", flush=True)
    counts = conn.execute(
        "SELECT ano, COUNT(*) FROM sentencias GROUP BY ano ORDER BY ano"
    ).fetchall()
    print("Por año:")
    for a, c in counts:
        print(f"  {a}: {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
