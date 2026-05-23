#!/usr/bin/env python3
"""Búsqueda full-text sobre el corpus indexado.

Usage:
  python3 chile/scripts/search.py "uf reajuste"
  python3 chile/scripts/search.py "huelga ilegal" --source dt
  python3 chile/scripts/search.py "patente invención" --source tdpi --limit 5
"""
from __future__ import annotations
import argparse, sqlite3, sys, re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+")
    parser.add_argument("--source", default="",
                        help="Filtrar por fuente (ej. tdpi, dt, fne)")
    parser.add_argument("--year", default="")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--snippet-len", type=int, default=200)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"ERROR: índice no existe en {args.db}")
        print("Correr primero: python3 chile/scripts/build-fts-index.py")
        return 1

    conn = sqlite3.connect(args.db, timeout=30)
    q = " ".join(args.query)

    where_clauses = ["docs MATCH ?"]
    params: list = [q]
    if args.source:
        where_clauses.append("source = ?")
        params.append(args.source)
    if args.year:
        where_clauses.append("year = ?")
        params.append(args.year)
    where = " AND ".join(where_clauses)

    sql = (
        f"SELECT source, year, path, "
        f"snippet(docs, 3, '«', '»', '…', 32) as snip, "
        f"bm25(docs) as score "
        f"FROM docs WHERE {where} "
        f"ORDER BY bm25(docs) LIMIT ?"
    )
    params.append(args.limit)

    print(f"Buscando: {q!r} (source={args.source or '*'}, year={args.year or '*'})\n")
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        print(f"ERROR query: {e}")
        return 2

    if not rows:
        print("0 resultados.")
        return 0

    for i, (source, year, path, snip, score) in enumerate(rows, 1):
        # Hacer path relativo a chile/data para legibilidad
        rel = path
        try:
            rel = str(Path(path).relative_to(_REPO_ROOT))
        except ValueError:
            pass
        print(f"[{i:2d}] {source}/{year or '----'} score={score:.2f}")
        # Original PDF (remove .txt extension)
        pdf_path = rel.replace(".pdf.txt", ".pdf")
        print(f"     PDF: {pdf_path}")
        # Snippet — collapse whitespace
        snip_clean = re.sub(r"\s+", " ", snip).strip()
        print(f"     {snip_clean[:args.snippet_len]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
