#!/usr/bin/env python3
"""Indexa embeddings bge-m3 sobre cada artículo individual de leyes
chilenas. Espejo de build-embeddings-index.py pero a granularidad fina
(218k chunks vs 80k docs completos).

Tabla nueva `articulos_embeddings`:
  articulos_meta_id INTEGER PRIMARY KEY (FK a articulos_meta.id)
  model TEXT, dim INTEGER, vec BLOB, mtime REAL

Idempotente: skip si articulos_meta.id ya tiene embedding.

Usage:
  python3 build-articulos-embeddings.py --batch 32 --workers 2
  python3 build-articulos-embeddings.py --leychile-code 207436 # solo Código Trabajo
"""
from __future__ import annotations
import argparse, json, sqlite3, struct, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"
OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 1500
_STATS = {"ok": 0, "skip": 0, "err": 0}
_LOCK = Lock()


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS articulos_embeddings ("
        "articulos_meta_id INTEGER PRIMARY KEY, "
        "model TEXT, dim INTEGER, vec BLOB, mtime REAL, "
        "FOREIGN KEY(articulos_meta_id) REFERENCES articulos_meta(id))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_artemb_model "
        "ON articulos_embeddings(model)"
    )
    conn.commit()
    conn.close()


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


def embed_batch(texts: list[str], timeout: int = 120) -> list[list[float]] | None:
    inputs = [t[:MAX_CHARS] for t in texts]
    payload = json.dumps({"model": MODEL, "input": inputs}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        return data.get("embeddings") or None
    except Exception:
        return None


def process_batch(items: list[tuple[int, str, float]], db_path: str) -> int:
    """items: list of (articulos_meta_id, content, mtime)."""
    if not items:
        return 0
    valid = [(i, c, m) for (i, c, m) in items if c and len(c) >= 30]
    skipped = len(items) - len(valid)
    if skipped:
        with _LOCK: _STATS["skip"] += skipped
    if not valid:
        return 0

    vecs = embed_batch([c for (_, c, _) in valid])
    if not vecs or len(vecs) != len(valid):
        with _LOCK: _STATS["err"] += len(valid)
        return 0

    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.executemany(
            "INSERT OR REPLACE INTO articulos_embeddings("
            "articulos_meta_id, model, dim, vec, mtime) "
            "VALUES (?, ?, ?, ?, ?)",
            [(i, MODEL, len(v), pack_vec(v), m)
             for (i, _, m), v in zip(valid, vecs)],
        )
        c.commit()
    finally:
        c.close()
    with _LOCK: _STATS["ok"] += len(valid)
    return len(valid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--leychile-code", type=int, default=0,
                        help="Solo indexar artículos de un idNorma")
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    init_table(Path(args.db))

    conn = sqlite3.connect(args.db, timeout=60)
    # Pull articulos sin embedding. content viene del FTS articulos.
    base = (
        "SELECT m.id, a.content, m.mtime "
        "FROM articulos_meta m "
        "JOIN articulos a ON a.rowid = m.id "
        "WHERE m.id NOT IN ("
        "  SELECT articulos_meta_id FROM articulos_embeddings WHERE model = ?"
        ") "
    )
    params: tuple = (MODEL,)
    if args.leychile_code:
        base += "AND m.leychile_code = ? "
        params = (MODEL, args.leychile_code)
    base += "ORDER BY m.id"
    rows = conn.execute(base, params).fetchall()
    conn.close()

    if args.max > 0:
        rows = rows[:args.max]
    print(f"Artículos pendientes: {len(rows)}", flush=True)
    if not rows:
        return 0

    print("Warmup bge-m3...", flush=True)
    t0 = time.time()
    _ = embed_batch(["warmup"])
    print(f"  warmup: {time.time()-t0:.1f}s", flush=True)

    batches = [rows[i:i + args.batch] for i in range(0, len(rows), args.batch)]
    print(f"Total batches: {len(batches)} x {args.batch}", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_batch, b, args.db) for b in batches]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 20 == 0 or i == len(batches):
                elapsed = time.time() - start
                done = _STATS['ok'] + _STATS['skip'] + _STATS['err']
                rate = done / elapsed if elapsed > 0 else 0
                eta = (len(rows) - done) / rate if rate > 0 else 0
                pct = 100.0 * done / len(rows) if rows else 0
                print(
                    f"  [batch {i}/{len(batches)} · {pct:.1f}%] "
                    f"ok={_STATS['ok']} skip={_STATS['skip']} err={_STATS['err']} "
                    f"| {rate:.1f}/s eta={eta/60:.0f}min",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} "
        f"skip={_STATS['skip']} err={_STATS['err']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
