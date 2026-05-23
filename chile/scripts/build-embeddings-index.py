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


def embed_text(text: str, timeout: int = 60) -> list[float] | None:
    # bge-m3 max 8192 tokens. Truncar a ~4000 chars para safety.
    if len(text) > 8000:
        text = text[:8000]
    payload = json.dumps({"model": MODEL, "input": text}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        embs = data.get("embeddings") or []
        return embs[0] if embs else None
    except Exception:
        return None


def worker(item: tuple[str, float], db_path: str) -> str:
    path_str, mtime = item
    p = Path(path_str)
    try:
        content = p.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "read_err"
    if len(content) < 50:
        with _LOCK: _STATS["skip"] += 1
        return "too_short"

    vec = embed_text(content)
    if not vec:
        with _LOCK: _STATS["err"] += 1
        return "embed_err"

    blob = pack_vec(vec)
    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.execute(
            "INSERT OR REPLACE INTO embeddings(path, model, dim, vec, mtime) "
            "VALUES (?, ?, ?, ?, ?)",
            (path_str, MODEL, len(vec), blob, mtime),
        )
        c.commit()
    finally:
        c.close()
    with _LOCK: _STATS["ok"] += 1
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--workers", type=int, default=2,
                        help="Conservador (default 2) para coexistir con OCR.")
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
    _ = embed_text("warmup")
    print(f"  warmup: {time.time()-t0:.1f}s", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, r, args.db) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 100 == 0 or i == len(rows):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(rows) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(rows)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"err={_STATS['err']} | "
                    f"elapsed={elapsed:.0f}s rate={rate:.1f}/s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} skip={_STATS['skip']} err={_STATS['err']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
