#!/usr/bin/env python3
"""Bulk Subtel — resoluciones exentas + decretos supremos.

Subtel publica PDFs vinculados desde 2 índices estables:
- /resoluciones-exentas/  → ~47 PDFs
- /decretos-supremos/     → ~26 PDFs

PDFs viven en /images/stories/articles/subtel/asocfile/<archivo>.pdf
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.parse, urllib.request, urllib.error, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE = "https://www.subtel.gob.cl"
INDEXES = {
    "resoluciones-exentas": f"{BASE}/resoluciones-exentas/",
    "decretos-supremos":    f"{BASE}/decretos-supremos/",
}
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS documentos ("
        "url TEXT PRIMARY KEY, categoria TEXT, "
        "downloaded INTEGER DEFAULT 0, pdf_size INTEGER)"
    )
    conn.commit()
    return conn


def discover_pdfs(index_url: str) -> list[str]:
    req = urllib.request.Request(index_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", errors="replace")
    urls = set()
    for m in re.finditer(r'href=["\']([^"\']+\.pdf)["\']', body, re.IGNORECASE):
        u = m.group(1)
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = BASE + u
        elif u.startswith("http"):
            pass
        else:
            # Subtel templates ponen hrefs como "images/stories/..." que
            # se resuelven contra ROOT, no contra el path del índice.
            u = f"{BASE}/{u.lstrip('./')}"
        urls.add(u)
    return sorted(urls)


def download(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _LOCK:
            _STATS["ok"] += 1
            _STATS["bytes"] += len(body)
        return "ok"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            with _LOCK: _STATS["404"] += 1
            return "404"
        with _LOCK: _STATS["err"] += 1
        return f"http{e.code}"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "err"


def safe_filename(url: str) -> str:
    base = url.rsplit("/", 1)[-1]
    # Decode URL encoding then sanitize
    base = urllib.parse.unquote(base)
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/subtel"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    print(f"[FASE 1] Descubriendo PDFs en índices Subtel...", flush=True)
    all_urls: list[tuple[str, str]] = []  # (url, categoria)
    for cat, index_url in INDEXES.items():
        try:
            urls = discover_pdfs(index_url)
            print(f"  {cat}: {len(urls)} PDFs", flush=True)
            for u in urls:
                conn.execute(
                    "INSERT OR IGNORE INTO documentos(url, categoria) VALUES (?, ?)",
                    (u, cat),
                )
                all_urls.append((u, cat))
        except Exception as e:
            print(f"  {cat}: ERR {e}", flush=True)
    conn.commit()

    pending = [
        (u, c) for u, c in all_urls
        if conn.execute(
            "SELECT downloaded FROM documentos WHERE url = ?", (u,)
        ).fetchone()[0] == 0
    ]
    print(f"\n[FASE 2] Descargando {len(pending)} PDFs...", flush=True)
    if not pending:
        return 0

    def worker(item):
        url, cat = item
        dest = output_dir / cat / safe_filename(url)
        status = download(url, dest)
        if status in ("ok", "skip"):
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute(
                    "UPDATE documentos SET downloaded=1, "
                    "pdf_size=(SELECT pdf_size FROM documentos WHERE url=?) WHERE url=?",
                    (url, url),
                )
                c.commit()
            finally:
                c.close()
        return url, status

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, item) for item in pending]
        for i, fut in enumerate(as_completed(futures), 1):
            fut.result()
            if i % 20 == 0 or i == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(pending)}] ok={_STATS['ok']} 404={_STATS['404']} "
                    f"err={_STATS['err']} | {mb:.0f} MB",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | {_STATS['ok']} PDFs, "
        f"{_STATS['bytes']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
