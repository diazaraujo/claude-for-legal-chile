#!/usr/bin/env python3
"""Embed bge-m3 sobre `docs` faltantes en tabla `embeddings`.

Lee `docs.content` directamente. Vía Ollama enigma (SSH tunnel localhost:11434).
Idempotente.
"""
from __future__ import annotations
import argparse, json, queue, sqlite3, struct, sys, threading, time
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"
OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 1500


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS embeddings ("
        "path TEXT PRIMARY KEY, model TEXT, dim INTEGER, "
        "vec BLOB, mtime REAL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_emb_model ON embeddings(model)")
    conn.commit()
    conn.close()


def pack_vec(vec):
    return struct.pack(f"<{len(vec)}f", *vec)


def embed_batch(texts, timeout=180):
    inputs = [(t or "")[:MAX_CHARS] for t in texts]
    payload = json.dumps({"model": MODEL, "input": inputs}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data.get("embeddings") or []


def worker(idx, in_q, out_q, stats, lock):
    while True:
        batch = in_q.get()
        if batch is None:
            in_q.task_done()
            return
        paths = [b[0] for b in batch]
        texts = [b[1] for b in batch]
        try:
            vecs = embed_batch(texts)
        except Exception:
            vecs = []
        if len(vecs) != len(paths):
            with lock:
                stats["err"] += len(batch)
            in_q.task_done()
            continue
        results = [(paths[i], pack_vec(vecs[i]), len(vecs[i])) for i in range(len(paths))]
        out_q.put(results)
        with lock:
            stats["ok"] += len(results)
        in_q.task_done()


def writer(out_q, db_path, stats, lock):
    conn = sqlite3.connect(db_path, timeout=120, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.execute("PRAGMA synchronous=NORMAL")
    while True:
        results = out_q.get()
        if results is None:
            out_q.task_done()
            conn.close()
            return
        now = time.time()
        conn.execute("BEGIN")
        conn.executemany(
            "INSERT OR REPLACE INTO embeddings(path, model, dim, vec, mtime) "
            "VALUES (?,?,?,?,?)",
            [(p, MODEL, d, v, now) for p, v, d in results],
        )
        conn.execute("COMMIT")
        out_q.task_done()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--source-filter", default=None)
    args = ap.parse_args()

    init_table(DB_PATH)
    db_str = str(DB_PATH)

    # Lista de docs faltantes
    where = ""
    params = []
    if args.source_filter:
        where = " AND d.source = ?"
        params.append(args.source_filter)
    limit_sql = f" LIMIT {args.limit}" if args.limit else ""

    reader = sqlite3.connect(db_str, timeout=120)
    reader.execute("PRAGMA busy_timeout=120000")
    total = reader.execute(
        "SELECT COUNT(*) FROM docs d WHERE NOT EXISTS "
        "(SELECT 1 FROM embeddings e WHERE e.path=d.path)" + where, params
    ).fetchone()[0]
    if args.limit: total = min(total, args.limit)
    print(f"=== embed-docs-all ===", flush=True)
    print(f"  batch={args.batch} workers={args.workers} source={args.source_filter}",
          flush=True)
    print(f"  docs faltantes: {total:,}", flush=True)

    # Queues
    in_q = queue.Queue(maxsize=args.workers * 4)
    out_q = queue.Queue(maxsize=args.workers * 4)
    stats = {"ok": 0, "err": 0}
    lock = threading.Lock()

    # Workers
    threads = []
    for i in range(args.workers):
        t = threading.Thread(target=worker, args=(i, in_q, out_q, stats, lock),
                             daemon=True)
        t.start()
        threads.append(t)
    # Writer
    wt = threading.Thread(target=writer, args=(out_q, db_str, stats, lock),
                          daemon=True)
    wt.start()

    # Stream
    cur = reader.execute(
        "SELECT d.path, d.content FROM docs d WHERE NOT EXISTS "
        "(SELECT 1 FROM embeddings e WHERE e.path=d.path)" + where + limit_sql,
        params
    )

    t0 = time.time()
    last_print = t0
    done = 0
    batch = []
    while True:
        row = cur.fetchone()
        if row is None:
            if batch:
                in_q.put(batch)
                done += len(batch)
                batch = []
            break
        batch.append((row[0], row[1] or ""))
        if len(batch) >= args.batch:
            in_q.put(batch)
            done += len(batch)
            batch = []
            if time.time() - last_print > 10:
                with lock:
                    s = dict(stats)
                el = time.time() - t0
                rate = s["ok"] / el if el > 0 else 0
                eta = (total - s["ok"]) / rate / 60 if rate > 0 else 0
                print(f"  submitted={done:,}/{total:,} ok={s['ok']:,} err={s['err']} "
                      f"rate={rate:.0f}/s ETA={eta:.0f}min "
                      f"qIn={in_q.qsize()} qOut={out_q.qsize()}", flush=True)
                last_print = time.time()

    # Drain
    in_q.join()
    for _ in threads:
        in_q.put(None)
    out_q.join()
    out_q.put(None)
    wt.join()
    reader.close()

    el = time.time() - t0
    rate = stats["ok"] / el if el > 0 else 0
    print(f"\n[DONE] {el:.0f}s | ok={stats['ok']:,} err={stats['err']} "
          f"rate={rate:.0f}/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
