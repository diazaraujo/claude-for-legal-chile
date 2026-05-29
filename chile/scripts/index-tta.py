#!/usr/bin/env python3
"""Indexa sentencias TTA en docs FTS (extractos + metadata)."""
from __future__ import annotations
import sqlite3, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = _REPO_ROOT / "chile/data/tta/manifest.sqlite3"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


def main() -> int:
    if not MANIFEST.exists():
        print(f"no existe {MANIFEST}", flush=True)
        return 1
    m = sqlite3.connect(str(MANIFEST), timeout=30)
    rows = m.execute(
        "SELECT expediente, ano, tribunal, rit, ruc, fecha, materia, "
        "caratula, extracto, proceso, servicio, etiquetas FROM sentencias"
    ).fetchall()
    m.close()
    print(f"manifest: {len(rows)} sentencias", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'tta/%'"
        )
    )

    n_ok = n_skip = n_empty = 0
    t0 = time.time()
    now = time.time()
    for r in rows:
        (expediente, ano, tribunal, rit, ruc, fecha, materia,
         caratula, extracto, proceso, servicio, etiquetas) = r
        path = f"tta/{ano or 'sin'}/{expediente}.txt"
        if path in existing:
            n_skip += 1
            continue
        if not extracto or len(extracto) < 50:
            n_empty += 1
            continue
        header = (
            f"TTA — Tribunales Tributarios y Aduaneros\n"
            f"Carátula: {caratula or 'N/A'}\n"
            f"Tribunal: {tribunal or 'N/A'}\n"
            f"RIT: {rit or 'N/A'}    RUC: {ruc or 'N/A'}\n"
            f"Fecha: {fecha or 'N/A'}    Año: {ano or 'N/A'}\n"
            f"Servicio: {servicio or 'N/A'}\n"
            f"Procedimiento: {proceso or 'N/A'}\n"
            f"Materia: {materia or 'N/A'}\n"
            f"Etiquetas: {etiquetas or 'N/A'}\n"
            f"Expediente: {expediente}\n\n"
            f"--- Extracto ---\n"
        )
        content = header + extracto.strip()
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "tta", ano or "?", content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % 1000 == 0:
            corpus.commit()
            print(f"  ok={n_ok} skip={n_skip} empty={n_empty}", flush=True)
    corpus.commit()
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
