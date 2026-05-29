#!/usr/bin/env python3
"""Indexa PDFs TRICEL en docs FTS via pdftotext."""
from __future__ import annotations
import sqlite3, subprocess, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = _REPO_ROOT / "chile/data/tricel"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


def pdftotext(pdf: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                       capture_output=True, text=True, timeout=120)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    if not ROOT.exists():
        print(f"no existe {ROOT}", flush=True)
        return 1
    pdfs = sorted(ROOT.rglob("*.pdf"))
    print(f"PDFs encontrados: {len(pdfs)}", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'tricel/%'"
        )
    )
    n_ok = n_skip = n_err = n_empty = 0
    t0 = time.time()
    now = time.time()
    for pdf in pdfs:
        rel = pdf.relative_to(ROOT.parent)
        path = f"{rel.as_posix()}".replace(".pdf", ".txt")
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
        year = rel.parts[1] if len(rel.parts) > 1 else "?"
        header = f"TRICEL — Tribunal Calificador de Elecciones\nArchivo: {pdf.name}\nAño: {year}\n\n"
        content = header + text.strip()
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "tricel", year, content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % 100 == 0:
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
