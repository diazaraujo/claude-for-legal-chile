#!/usr/bin/env python3
"""Indexa embeddings bge-m3 vía Ollama local sobre todos los .pdf.txt
del corpus. Output: tabla `embeddings(path, vec BLOB)` en el mismo
SQLite FTS5 que ya tenemos.

Idempotente: skip si ya existe embedding para el path.
Conservador: workers=2 para no saturar mientras OCR corre.
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
_STATS = {"ok": 0, "skip": 0, "err": 0}
_LOCK = Lock()


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS embeddings ("
        "path TEXT PRIMARY KEY, model TEXT, dim INTEGER, "
        "vec BLOB, mtime REAL)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_emb_model ON embeddings(model)"
    )
    conn.commit()
    conn.close()


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


def unpack_vec(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


MAX_CHARS = 1500  # bge-m3 con 1500 chars: ~0.1s/doc vs 1s/doc full

def embed_batch(texts: list[str], timeout: int = 120) -> list[list[float]] | None:
    """Batch embed: pasa hasta N inputs en una sola request a Ollama.
    bge-m3 acepta arrays — 16-32 inputs en <1s típicamente.

    Trunca a MAX_CHARS para no pagar costo CPU de docs largos —
    primeras 1500 chars suelen tener título, partes, materia, fecha:
    suficiente para semantic search/related."""
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


def process_batch(items: list[tuple[str, float]], db_path: str) -> int:
    """Procesa N items en una request Ollama batch + un commit DB."""
    if not items:
        return 0
    # Read texts in parallel-friendly way
    valid: list[tuple[str, float, str]] = []
    for path_str, mtime in items:
        try:
            content = Path(path_str).read_text(
                encoding="utf-8", errors="replace"
            ).strip()
        except Exception:
            with _LOCK: _STATS["err"] += 1
            continue
        if len(content) < 50:
            with _LOCK: _STATS["skip"] += 1
            continue
        valid.append((path_str, mtime, content))
    if not valid:
        return 0

    vecs = embed_batch([t[2] for t in valid])
    if not vecs or len(vecs) != len(valid):
        with _LOCK: _STATS["err"] += len(valid)
        return 0

    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.executemany(
            "INSERT OR REPLACE INTO embeddings(path, model, dim, vec, mtime) "
            "VALUES (?, ?, ?, ?, ?)",
            [(p, MODEL, len(v), pack_vec(v), m)
             for (p, m, _), v in zip(valid, vecs)],
        )
        c.commit()
    finally:
        c.close()
    with _LOCK: _STATS["ok"] += len(valid)
    return len(valid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--workers", type=int, default=2,
                        help="Threads paralelos (batch en cada uno).")
    parser.add_argument("--batch", type=int, default=32,
                        help="Inputs por batch a Ollama (default 32)")
    parser.add_argument("--source", default="",
                        help="Solo indexar una fuente específica (ej. 'tc-moderno')")
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    init_table(Path(args.db))

    # Get list of paths from FTS index that don't have embedding yet
    conn = sqlite3.connect(args.db, timeout=60)
    if args.source:
        rows = conn.execute(
            "SELECT d.path, dm.mtime FROM docs d "
            "JOIN docs_meta dm ON d.path = dm.path "
            "WHERE d.source = ? AND d.path NOT IN "
            "(SELECT path FROM embeddings WHERE model = ?) "
            "ORDER BY dm.mtime DESC", (args.source, MODEL),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT d.path, dm.mtime FROM docs d "
            "JOIN docs_meta dm ON d.path = dm.path "
            "WHERE d.path NOT IN "
            "(SELECT path FROM embeddings WHERE model = ?) "
            "ORDER BY dm.mtime DESC", (MODEL,),
        ).fetchall()
    conn.close()

    if args.max > 0:
        rows = rows[:args.max]
    print(f"Embeddings pendientes: {len(rows)}", flush=True)
    if not rows:
        return 0

    # Warmup Ollama with 1 call
    print("Warmup bge-m3...", flush=True)
    t0 = time.time()
    _ = embed_batch(["warmup"])
    print(f"  warmup: {time.time()-t0:.1f}s", flush=True)

    # Group rows into batches
    batches: list[list[tuple[str, float]]] = []
    for i in range(0, len(rows), args.batch):
        batches.append(rows[i:i + args.batch])
    print(f"Total batches: {len(batches)} x {args.batch} items", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_batch, b, args.db) for b in batches]
        n_done = 0
        for i, fut in enumerate(as_completed(futures), 1):
            try: n = fut.result()
            except Exception: n = 0
            n_done += args.batch  # progress aprox
            if i % 10 == 0 or i == len(batches):
                elapsed = time.time() - start
                done_real = _STATS['ok'] + _STATS['skip'] + _STATS['err']
                rate = done_real / elapsed if elapsed > 0 else 0
                eta = (len(rows) - done_real) / rate if rate > 0 else 0
                print(
                    f"  [batch {i}/{len(batches)}] "
                    f"ok={_STATS['ok']} skip={_STATS['skip']} err={_STATS['err']} | "
                    f"elapsed={elapsed:.0f}s rate={rate:.1f}/s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} skip={_STATS['skip']} err={_STATS['err']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
