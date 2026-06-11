#!/usr/bin/env python3
"""Capa administrativa del árbol normativo: citas a normas desde dictámenes/oficios.

Recorre TODAS las fuentes administrativas de data/ (CGR, DT, SII, SUSESO,
superintendencias, etc. — universo completo, sin top-N) y extrae citas normativas
del texto de cada documento, reusando los regex de extract-citas-normativas.py.
Tabla destino: citas_admin en citas_normativas.sqlite3. Reanudable por fuente+doc.

Usage: python3 extract-citas-admin.py [--workers 6]
"""
import argparse, importlib.util, sqlite3, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
OUT = ROOT / "data/_index/citas_normativas.sqlite3"

SOURCES = [
    "aduanas", "cgr", "cgr-dictamenes", "cmf", "cplt", "dga", "dt", "fne",
    "recursos-administrativos", "sag-normativa", "sec", "sernac", "servel",
    "sii", "sii-normativa", "sii-oficios", "siss", "spensiones", "subtel",
    "subtrans", "superdesalud", "supereduc", "superir", "suseso",
]
EXTS = {".txt", ".html", ".htm"}
MAX_CHARS = 400_000

_spec = importlib.util.spec_from_file_location(
    "citas_core", str(ROOT / "scripts/extract-citas-normativas.py"))
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)
extract = _core.extract


def work(args):
    source, paths = args
    res = []
    for p in paths:
        try:
            text = Path(p).read_text(errors="replace")[:MAX_CHARS]
        except Exception:
            continue
        rel = p.replace(str(ROOT / "data") + "/", "")
        for tipo, art, cuerpo, raw in extract(text):
            res.append((rel, source, tipo, art, cuerpo, raw))
    return source, len(paths), res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    out = sqlite3.connect(str(OUT), timeout=120)
    out.execute("PRAGMA journal_mode=WAL")
    out.execute("CREATE TABLE IF NOT EXISTS citas_admin ("
                "doc_path TEXT, source TEXT, tipo_cita TEXT, articulo TEXT, "
                "cuerpo TEXT, raw TEXT, id_norma INTEGER)")
    out.execute("CREATE TABLE IF NOT EXISTS citas_admin_progreso (source TEXT PRIMARY KEY, n_docs INTEGER, n_citas INTEGER)")
    done = {r[0] for r in out.execute("SELECT source FROM citas_admin_progreso")}

    t0 = time.time()
    for source in SOURCES:
        if source in done:
            continue
        d = ROOT / "data" / source
        if not d.exists():
            print(f"  [{source}] sin directorio — registrado en progreso con 0", flush=True)
            out.execute("INSERT OR REPLACE INTO citas_admin_progreso VALUES (?,0,0)", (source,))
            out.commit()
            continue
        files = [str(p) for p in d.rglob("*") if p.suffix.lower() in EXTS]
        # dedup pdf.txt vs pdf: rglob solo agarra .txt asi que ok
        chunks = [files[i:i + 300] for i in range(0, len(files), 300)]
        nc = 0
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for _, ndocs, res in pool.map(work, [(source, ch) for ch in chunks]):
                if res:
                    out.executemany("INSERT INTO citas_admin (doc_path, source, tipo_cita, articulo, cuerpo, raw) VALUES (?,?,?,?,?,?)", res)
                    out.commit()
                    nc += len(res)
        out.execute("INSERT OR REPLACE INTO citas_admin_progreso VALUES (?,?,?)", (source, len(files), nc))
        out.commit()
        print(f"  [{source}] {len(files)} docs → {nc} citas · {time.time()-t0:.0f}s", flush=True)
    tot = out.execute("SELECT count(*) FROM citas_admin").fetchone()[0]
    print(f"[DONE] citas_admin={tot} en {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
