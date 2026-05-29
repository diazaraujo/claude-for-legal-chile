#!/usr/bin/env python3
"""Indexa boletines TCP (Tribunal de Contratación Pública) en docs FTS.

Lee `data/tcp/boletines/{year}/*.pdf`, extrae texto con pdftotext, los
inserta en `docs` con source='tcp' y path sintético `tcp/boletines/{year}/{stem}.txt`.

Cada boletín es 1 doc (en el futuro podríamos partir por sentencia individual
buscando patrones "ROL Nº" / "RESOLUCIÓN N°").

Idempotente: skip si el path ya está en docs_meta.
"""
from __future__ import annotations
import sqlite3, subprocess, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
TCP_ROOT = _REPO_ROOT / "chile/data/tcp/boletines"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


def pdftotext(pdf: Path) -> str:
    r = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, text=True, timeout=120,
    )
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    if not TCP_ROOT.exists():
        print(f"no existe {TCP_ROOT}", flush=True)
        return 1
    pdfs = sorted(TCP_ROOT.rglob("*.pdf"))
    print(f"PDFs encontrados: {len(pdfs)}", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'tcp/%'"
        )
    )

    n_ok = n_skip = n_err = n_empty = 0
    t0 = time.time()
    now = time.time()
    for pdf in pdfs:
        rel = pdf.relative_to(TCP_ROOT.parent)  # tcp/boletines/.../x.pdf
        path = f"tcp/{rel.as_posix()}".replace(".pdf", ".txt")
        if path in existing:
            n_skip += 1
            continue
        try:
            text = pdftotext(pdf)
        except Exception:
            n_err += 1
            continue
        if len(text) < 200:
            n_empty += 1
            continue
        # Header
        year = rel.parts[1] if len(rel.parts) > 1 else "?"
        header = f"Boletín de Jurisprudencia TCP\nArchivo: {pdf.name}\nAño: {year}\n\n"
        content = header + text.strip()
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "tcp", year, content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        print(f"  ok: {path} ({len(content):,} bytes)", flush=True)
    corpus.commit()
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} "
          f"err={n_err} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
