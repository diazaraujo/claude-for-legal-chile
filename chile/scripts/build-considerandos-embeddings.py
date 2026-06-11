#!/usr/bin/env python3
"""Embed considerandos chunks con bge-m3 para related/semantic search granular.

246k chunks ~ avg 1600 chars cada uno. Cabe en bge-m3 sin trunc.
Tabla nueva: considerandos_embeddings(considerandos_meta_id PK, vec).

Idempotente. ETA estimado ~10-12h con workers=3 batch=32.

Usage:
  python3 build-considerandos-embeddings.py
  python3 build-considerandos-embeddings.py --max 500 --workers 2
"""
from __future__ import annotations
import argparse, json, sqlite3, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"
OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 8000  # promedio chunk 1600, pero algunos llegan a 10k
_STATS = {"ok": 0, "skip": 0, "err": 0}
_LOCK = Lock()


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS considerandos_embeddings (
            considerandos_meta_id INTEGER PRIMARY KEY,
            model TEXT,
            dim INTEGER,
            vec BLOB,
            mtime REAL,
            FOREIGN KEY(considerandos_meta_id) REFERENCES considerandos_meta(id)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_considemb_model "
        "ON considerandos_embeddings(model)"
    )
    conn.commit()
    conn.close()


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


TEI_URL = None  # set en main() con --endpoint tei (mismo bge-m3, coseno 0.999997 vs Ollama)


def embed_batch(texts: list[str], timeout: int = 180) -> list[list[float]] | None:
    inputs = [t[:MAX_CHARS] for t in texts]
    if TEI_URL:
        payload = json.dumps({"inputs": inputs}).encode()
        url = TEI_URL
    else:
        payload = json.dumps({"model": MODEL, "input": inputs}).encode()
        url = OLLAMA_URL
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        if TEI_URL:
            return data if isinstance(data, list) else None
        return data.get("embeddings") or None
    except Exception:
        return None


def process_batch(items: list[tuple[int, str, float]], db_path: str) -> int:
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
            "INSERT OR REPLACE INTO considerandos_embeddings("
            "considerandos_meta_id, model, dim, vec, mtime) "
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
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--max", type=int, default=0)
    parser.add_argument("--endpoint", choices=["ollama", "tei"], default="ollama")
    parser.add_argument("--tei-url", default="http://localhost:18002/embed")
    parser.add_argument("--desc", action="store_true",
                        help="recorre ids DESC (para 2º stream sin pisar al ASC)")
    args = parser.parse_args()
    if args.endpoint == "tei":
        global TEI_URL
        TEI_URL = args.tei_url

    init_table(Path(args.db))

    conn = sqlite3.connect(args.db, timeout=60)
    sql = (
        "SELECT m.id, c.content, m.mtime "
        "FROM considerandos_meta m "
        "JOIN considerandos_chunks c ON c.rowid = m.id "
        "WHERE m.id NOT IN ("
        "  SELECT considerandos_meta_id FROM considerandos_embeddings WHERE model = ?"
        ") "
        "ORDER BY m.id"
    )
    if args.desc:
        sql += " DESC"
    if args.max > 0:
        sql += f" LIMIT {int(args.max)}"
    rows = conn.execute(sql, (MODEL,)).fetchall()
    conn.close()
    print(f"Considerandos pendientes: {len(rows)} | workers={args.workers} batch={args.batch}", flush=True)
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
    print(f"\n[DONE] {elapsed:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
