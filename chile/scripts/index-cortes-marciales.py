#!/usr/bin/env python3
"""Indexa PDFs Cortes Marciales a docs FTS via pdftotext.

Lee data/cortes-marciales/{tribunal-slug}/*.pdf y crea docs con
source='cortes-marciales' y path sintético cortes-marciales/{tribunal}/{file}.txt.

Metadata adicional (rol, materia, fecha, tribunal) viene del manifest sqlite
generado por el bulk downloader.
"""
from __future__ import annotations
import sqlite3, subprocess, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = _REPO_ROOT / "chile/data/cortes-marciales"
MANIFEST = ROOT / "manifest.sqlite3"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


def pdftotext(pdf: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                       capture_output=True, text=True, timeout=120)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    if not ROOT.exists():
        print(f"no existe {ROOT}", flush=True)
        return 1
    # cargar manifest: file_id → metadata
    meta_map = {}
    if MANIFEST.exists():
        m = sqlite3.connect(str(MANIFEST), timeout=30)
        for r in m.execute(
            "SELECT file_id, tribunal, rol, materia, fecha FROM sentencias"
        ):
            meta_map[r[0]] = {"tribunal": r[1], "rol": r[2],
                              "materia": r[3], "fecha": r[4]}
        m.close()
    print(f"manifest: {len(meta_map)} entries", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'cortes-marciales/%'"
        )
    )
    print(f"already indexed: {len(existing)}", flush=True)

    pdfs = sorted(ROOT.rglob("*.pdf"))
    print(f"PDFs encontrados: {len(pdfs)}", flush=True)

    n_ok = n_skip = n_err = n_empty = 0
    t0 = time.time()
    now = time.time()
    for pdf in pdfs:
        rel = pdf.relative_to(ROOT.parent)
        path = f"{rel.as_posix()}".replace(".pdf", ".txt")
        if path in existing:
            n_skip += 1
            continue
        # parsear file_id del nombre ({id}_{slug}.pdf)
        try:
            file_id = int(pdf.name.split("_", 1)[0])
        except ValueError:
            file_id = None
        meta = meta_map.get(file_id, {}) if file_id else {}
        try:
            text = pdftotext(pdf)
        except Exception:
            n_err += 1
            continue
        if len(text) < 200:
            n_empty += 1
            continue
        # Año del fecha (formato DD-MM-YYYY)
        year = "?"
        if meta.get("fecha"):
            parts = meta["fecha"].split("-")
            if len(parts) == 3 and parts[2].isdigit():
                year = parts[2]
        header = (
            f"Cortes Marciales — {meta.get('tribunal') or 'N/A'}\n"
            f"Rol: {meta.get('rol') or 'N/A'}\n"
            f"Materia: {meta.get('materia') or 'N/A'}\n"
            f"Fecha: {meta.get('fecha') or 'N/A'}\n"
            f"Archivo: {pdf.name}\n\n"
        )
        content = header + text.strip()
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "cortes-marciales", year, content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % 200 == 0:
            corpus.commit()
            print(f"  ok={n_ok} skip={n_skip} err={n_err} empty={n_empty}",
                  flush=True)
    corpus.commit()
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} "
          f"err={n_err} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
