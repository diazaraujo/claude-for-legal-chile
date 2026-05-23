#!/usr/bin/env python3
"""Indexa todos los .pdf.txt del corpus en SQLite FTS5.

Output: chile/data/_index/corpus.fts.sqlite3

Idempotente: usa file path como rowid stable. Re-indexa si el
.pdf.txt tiene mtime más reciente que la entrada FTS.
"""
from __future__ import annotations
import argparse, sqlite3, sys, os, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = _REPO_ROOT / "chile/data"
INDEX_DIR = DATA_ROOT / "_index"


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
            path,
            source UNINDEXED,
            year UNINDEXED,
            content,
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS docs_meta (
            path TEXT PRIMARY KEY,
            mtime REAL,
            size INTEGER
        )
    """)
    conn.commit()
    return conn


def source_from_path(p: Path) -> str:
    """Infiere fuente desde directorio. p.relative_to(DATA_ROOT) gives
    e.g. 'diario-oficial/2024/.../foo.pdf.txt' → 'diario-oficial'"""
    try:
        rel = p.relative_to(DATA_ROOT)
        return rel.parts[0]
    except ValueError:
        return "unknown"


def year_from_path(p: Path) -> str:
    """Busca 4 dígitos consecutivos 19xx/20xx en el path."""
    import re
    for part in p.parts:
        m = re.fullmatch(r"(19[89]\d|20[0-2]\d)", part)
        if m:
            return m.group(1)
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DATA_ROOT))
    parser.add_argument("--db",   default=str(INDEX_DIR / "corpus.fts.sqlite3"))
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.rebuild and db_path.exists():
        db_path.unlink()
        for ext in ("-wal", "-shm"):
            p = db_path.with_name(db_path.name + ext)
            if p.exists():
                p.unlink()
    conn = init_db(db_path)

    root = Path(args.root)
    txts = list(root.rglob("*.pdf.txt"))
    print(f"Archivos .pdf.txt encontrados: {len(txts)}", flush=True)

    existing = {
        row[0]: (row[1], row[2])
        for row in conn.execute("SELECT path, mtime, size FROM docs_meta")
    }

    start = time.time()
    n_added, n_skipped, n_empty = 0, 0, 0
    for i, txt in enumerate(txts, 1):
        path_str = str(txt)
        try:
            stat = txt.stat()
        except OSError:
            continue
        if stat.st_size == 0:
            n_empty += 1
            continue
        if path_str in existing:
            old_mtime, old_size = existing[path_str]
            if old_mtime == stat.st_mtime and old_size == stat.st_size:
                n_skipped += 1
                continue
            conn.execute("DELETE FROM docs WHERE path=?", (path_str,))
        try:
            content = txt.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if len(content) < 50:
            n_empty += 1
            continue
        conn.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path_str, source_from_path(txt), year_from_path(txt), content),
        )
        conn.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path_str, stat.st_mtime, stat.st_size),
        )
        n_added += 1
        if i % 1000 == 0:
            conn.commit()
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(txts) - i) / rate if rate > 0 else 0
            print(
                f"  [{i}/{len(txts)}] added={n_added} skip={n_skipped} "
                f"empty={n_empty} | {elapsed:.0f}s eta={eta:.0f}s rate={rate:.0f}/s",
                flush=True,
            )

    conn.commit()
    total_docs = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    elapsed = time.time() - start

    # Stats by source
    by_source = conn.execute(
        "SELECT source, COUNT(*) FROM docs GROUP BY source ORDER BY 2 DESC"
    ).fetchall()
    print(f"\n[DONE] {elapsed:.0f}s | added={n_added} skipped={n_skipped} empty={n_empty}")
    print(f"\nTotal docs en índice: {total_docs}")
    for src, n in by_source:
        print(f"  {src:25s} {n:>7d}")

    db_size = db_path.stat().st_size / 1024 / 1024
    print(f"\nÍndice: {db_path} ({db_size:.0f} MB)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
