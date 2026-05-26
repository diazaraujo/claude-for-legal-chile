#!/usr/bin/env python3
"""Re-embed con texto completo (hasta 30k chars vs 1.5k del primer pass).

El build-embeddings-index.py original trunca a MAX_CHARS=1500 (~375 tokens)
para velocidad. bge-m3 acepta hasta 8192 tokens (~30k chars español).
Para fuentes con razonamiento jurídico extenso (sentencias TC, TDLC, TDPI,
tribunales-ambientales) el truncado pierde 95% del contenido.

Este script re-embede docs de las sources indicadas usando max_chars=30000.
INSERT OR REPLACE en tabla `embeddings` — sobrescribe el embedding viejo.

Idempotente por mtime: si el embedding existente tiene mtime >= file mtime
y model_marker == 'bge-m3-fulltext', se considera ya hecho y se skipea.
Para forzar re-embed, usar --force.

Usage:
  python3 reembed-fulltext.py --sources tc,tc-moderno --workers 2
  python3 reembed-fulltext.py --sources tc --max 50 --force  # smoke
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
MODEL_MARKER = "bge-m3-fulltext"  # distingue del bge-m3 truncated
MAX_CHARS = 30000  # ~7500 tokens, safe vs 8192 max bge-m3
_STATS = {"ok": 0, "skip": 0, "err": 0}
_LOCK = Lock()


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


def embed_batch(texts: list[str], timeout: int = 300) -> list[list[float]] | None:
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
    except Exception as e:
        print(f"  embed err {type(e).__name__}: {str(e)[:80]}", flush=True)
        return None


def process_batch(items: list[tuple[str, float]], db_path: str) -> int:
    if not items:
        return 0
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
            [(p, MODEL_MARKER, len(v), pack_vec(v), m)
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
    parser.add_argument("--sources", default="tc,tc-moderno",
                        help="comma-separated list")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--batch", type=int, default=8,
                        help="docs por batch (más bajo que 32 porque texts más largos)")
    parser.add_argument("--max", type=int, default=0)
    parser.add_argument("--force", action="store_true",
                        help="re-embed aunque tenga MODEL_MARKER")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    placeholders = ",".join("?" * len(sources))

    conn = sqlite3.connect(args.db, timeout=60)
    if args.force:
        rows = conn.execute(
            f"SELECT d.path, dm.mtime FROM docs d "
            f"JOIN docs_meta dm ON d.path = dm.path "
            f"WHERE d.source IN ({placeholders}) "
            f"ORDER BY dm.mtime DESC",
            sources,
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT d.path, dm.mtime FROM docs d "
            f"JOIN docs_meta dm ON d.path = dm.path "
            f"WHERE d.source IN ({placeholders}) "
            f"AND d.path NOT IN ("
            f"  SELECT path FROM embeddings WHERE model = ? "
            f") "
            f"ORDER BY dm.mtime DESC",
            sources + [MODEL_MARKER],
        ).fetchall()
    conn.close()

    if args.max > 0:
        rows = rows[:args.max]
    print(f"Re-embed pendientes: {len(rows)} | sources={sources}", flush=True)
    print(f"max_chars={MAX_CHARS} | workers={args.workers} batch={args.batch}", flush=True)
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
            if i % 10 == 0 or i == len(batches):
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
    print(f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} "
          f"skip={_STATS['skip']} err={_STATS['err']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
