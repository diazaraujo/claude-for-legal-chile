#!/usr/bin/env python3
"""Index + embed de una fuente nueva en un índice LOCAL separado.

Por qué separado: el `corpus.fts` master vive en enigma y se rsync-ea de vuelta
(escribirlo local lo sobreescribiría). Esto crea
`chile/data/_index/new-sources.fts.sqlite3` con docs FTS5 + embeddings bge-m3
(vía túnel ollama localhost:11434 → GPU enigma). Mergea al master en enigma
después. Idempotente.

Ej: python embed-new-source.py --src data/cgr-dictamenes/dictamenes --glob '*.txt' --source cgr-dictamenes
"""
from __future__ import annotations
import argparse, json, re, sqlite3, struct, sys, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB = _REPO_ROOT / "chile/data/_index/new-sources.fts.sqlite3"
OLLAMA = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 1500
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_LOCK = Lock()


def to_text(p: Path) -> str:
    raw = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() in (".html", ".htm"):
        raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        raw = _TAG.sub(" ", raw)
    return _WS.sub(" ", raw).strip()


def embed(texts: list[str], timeout=180):
    payload = json.dumps({"model": MODEL, "input": [t[:MAX_CHARS] for t in texts]}).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()).get("embeddings", [])


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB), timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS docs_meta ("
              "path TEXT PRIMARY KEY, source TEXT, chars INTEGER)")
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content)")
    c.execute("CREATE TABLE IF NOT EXISTS embeddings ("
              "path TEXT PRIMARY KEY, model TEXT, dim INTEGER, vec BLOB)")
    c.commit()
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--glob", default="*.txt")
    ap.add_argument("--source", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    c = init_db()
    done = {r[0] for r in c.execute("SELECT path FROM embeddings").fetchall()}
    files = [p for p in sorted((_REPO_ROOT / "chile" / args.src
                                if not Path(args.src).is_absolute() else Path(args.src)).rglob(args.glob))]
    pending = [p for p in files if str(p) not in done]
    print(f"[{args.source}] {len(files)} archivos, {len(pending)} pendientes de embed", flush=True)

    # FTS docs (rápido, local) — solo los que faltan en docs_meta
    have_meta = {r[0] for r in c.execute("SELECT path FROM docs_meta").fetchall()}
    for p in files:
        sp = str(p)
        if sp in have_meta:
            continue
        txt = to_text(p)
        c.execute("INSERT OR IGNORE INTO docs(path, content) VALUES (?,?)", (sp, txt))
        c.execute("INSERT OR IGNORE INTO docs_meta(path, source, chars) VALUES (?,?,?)",
                  (sp, args.source, len(txt)))
    c.commit()

    # Embed en batches vía GPU (túnel)
    t0 = time.time()
    n = 0
    for i in range(0, len(pending), args.batch):
        chunk = pending[i:i + args.batch]
        texts = [to_text(p) for p in chunk]
        try:
            vecs = embed(texts)
        except Exception as e:
            print(f"  embed err @ {i}: {e}", flush=True)
            time.sleep(2)
            continue
        for p, v in zip(chunk, vecs):
            if v:
                c.execute("INSERT OR REPLACE INTO embeddings(path, model, dim, vec) VALUES (?,?,?,?)",
                          (str(p), MODEL, len(v), struct.pack(f"<{len(v)}f", *v)))
        c.commit()
        n += len(chunk)
        if (i // args.batch) % 10 == 0:
            el = time.time() - t0
            rate = n / el if el else 0
            eta = (len(pending) - n) / rate / 60 if rate else 0
            print(f"  embedded={n}/{len(pending)} rate={rate:.1f}/s ETA={eta:.0f}min", flush=True)
    print(f"[DONE] {args.source}: {n} embebidos en {time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
