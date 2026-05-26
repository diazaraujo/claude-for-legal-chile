#!/usr/bin/env python3
"""Indexa embeddings bge-m3 sobre metadata de doctrina académica.

Lee chile/normativa/doctrina/{fuente}/*.md (frontmatter Dublin Core) y
construye un texto compacto representativo:
  titulo + tipo + autores + materias + abstract

Embebe con bge-m3 (Ollama local). Tabla nueva:
  doctrina_embeddings(md_path TEXT PK, fuente, model, dim, vec BLOB, mtime)

Idempotente: skip si md_path ya tiene embedding.
Workers paralelos default 3, batch 32.

Usage:
  python3 build-doctrina-embeddings.py                # todas las fuentes
  python3 build-doctrina-embeddings.py --fuentes uch
  python3 build-doctrina-embeddings.py --fuentes uft,uv,uautonoma --max 100
"""
from __future__ import annotations
import argparse, json, re, sqlite3, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTRINA_ROOT = _REPO_ROOT / "chile/normativa/doctrina"
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"
OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 2500  # metadata rica cabe acá
_STATS = {"ok": 0, "skip": 0, "err": 0, "empty": 0}
_LOCK = Lock()


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctrina_embeddings (
            md_path TEXT PRIMARY KEY,
            fuente TEXT,
            model TEXT,
            dim INTEGER,
            vec BLOB,
            mtime REAL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_doctemb_fuente ON doctrina_embeddings(fuente)"
    )
    conn.commit()
    conn.close()


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


def parse_md_for_embed(path: Path) -> str | None:
    """Construye texto compacto representativo desde .md frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # Frontmatter entre --- --- al inicio
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return None
    fm_raw = m.group(1)
    body = m.group(2)

    titulo = ""
    autores: list[str] = []
    tipo = ""
    materias: list[str] = []
    anio = ""

    for line in fm_raw.splitlines():
        line = line.rstrip()
        if line.startswith("titulo:"):
            v = line[len("titulo:"):].strip().strip('"')
            titulo = v
        elif line.startswith("tipo:"):
            tipo = line[len("tipo:"):].strip().strip('"')
        elif line.startswith("anio:"):
            anio = line[len("anio:"):].strip()
        elif line.startswith("  - ") and (titulo and not autores):
            # autores yaml list continuation
            autores.append(line[4:].strip().strip('"'))

    # Materias: yaml list
    mm = re.search(r"\nmaterias:\n((?:  - .+\n)+)", fm_raw)
    if mm:
        for line in mm.group(1).splitlines():
            v = line.strip().lstrip("- ").strip().strip('"')
            if v:
                materias.append(v)

    # Autores: yaml list (separate parse)
    autores = []
    ma = re.search(r"\nautores:\n((?:  - .+\n)+)", fm_raw)
    if ma:
        for line in ma.group(1).splitlines():
            v = line.strip().lstrip("- ").strip().strip('"')
            if v:
                autores.append(v)

    # Abstract (Resumen) en body
    abstract = ""
    abs_m = re.search(r"##\s+Resumen\s*\n\n(.+?)(?:\n##|\Z)", body, re.DOTALL)
    if abs_m:
        abstract = abs_m.group(1).strip()

    parts = []
    if titulo: parts.append(titulo)
    if tipo and anio: parts.append(f"{tipo} ({anio})")
    elif tipo: parts.append(tipo)
    if autores: parts.append("Autores: " + ", ".join(autores[:4]))
    if materias: parts.append("Materias: " + ", ".join(materias[:8]))
    if abstract:
        # Limitar abstract para no dominar el embed
        parts.append(abstract[:1500])

    full = ". ".join(parts)
    return full[:MAX_CHARS] if full else None


def embed_batch(texts: list[str], timeout: int = 120) -> list[list[float]] | None:
    payload = json.dumps({"model": MODEL, "input": texts}).encode()
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


def process_batch(
    items: list[tuple[Path, str, str]], db_path: str
) -> int:
    """items: list of (path, fuente, embed_text)."""
    if not items:
        return 0
    vecs = embed_batch([t[2] for t in items])
    if not vecs or len(vecs) != len(items):
        with _LOCK: _STATS["err"] += len(items)
        return 0
    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.executemany(
            "INSERT OR REPLACE INTO doctrina_embeddings("
            "md_path, fuente, model, dim, vec, mtime) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(str(p), f, MODEL, len(v), pack_vec(v),
              p.stat().st_mtime if p.exists() else 0)
             for (p, f, _), v in zip(items, vecs)],
        )
        c.commit()
    finally:
        c.close()
    with _LOCK: _STATS["ok"] += len(items)
    return len(items)


def collect_pending(fuentes: list[str], db_path: str, max_n: int = 0) -> list[tuple[Path, str, str]]:
    conn = sqlite3.connect(db_path, timeout=60)
    existing = set(row[0] for row in conn.execute(
        "SELECT md_path FROM doctrina_embeddings"
    ))
    conn.close()

    pending: list[tuple[Path, str, str]] = []
    for fuente in fuentes:
        fdir = DOCTRINA_ROOT / fuente
        if not fdir.exists():
            continue
        for md in sorted(fdir.glob("*.md")):
            if str(md) in existing:
                continue
            embed_text = parse_md_for_embed(md)
            if not embed_text or len(embed_text) < 30:
                with _LOCK: _STATS["empty"] += 1
                continue
            pending.append((md, fuente, embed_text))
            if max_n > 0 and len(pending) >= max_n:
                return pending
    return pending


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--fuentes", default="",
                        help="comma-separated (vacío = todas las subdirs de doctrina/)")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    init_table(Path(args.db))

    if args.fuentes:
        fuentes = [f.strip() for f in args.fuentes.split(",") if f.strip()]
    else:
        fuentes = sorted([p.name for p in DOCTRINA_ROOT.iterdir() if p.is_dir()])
    print(f"Fuentes: {fuentes}", flush=True)

    pending = collect_pending(fuentes, args.db, args.max)
    print(f"Pendientes: {len(pending)} | workers={args.workers} batch={args.batch}", flush=True)
    if not pending:
        return 0

    # Warmup
    print("Warmup bge-m3...", flush=True)
    t0 = time.time()
    _ = embed_batch(["warmup"])
    print(f"  warmup: {time.time()-t0:.1f}s", flush=True)

    batches = [pending[i:i + args.batch] for i in range(0, len(pending), args.batch)]
    print(f"Total batches: {len(batches)} x {args.batch}", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_batch, b, args.db) for b in batches]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 10 == 0 or i == len(batches):
                elapsed = time.time() - start
                done = _STATS['ok'] + _STATS['err']
                rate = done / elapsed if elapsed > 0 else 0
                eta = (len(pending) - done) / rate if rate > 0 else 0
                pct = 100.0 * done / len(pending)
                print(
                    f"  [batch {i}/{len(batches)} · {pct:.1f}%] "
                    f"ok={_STATS['ok']} err={_STATS['err']} empty={_STATS['empty']} "
                    f"| {rate:.1f}/s eta={eta/60:.0f}min",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
