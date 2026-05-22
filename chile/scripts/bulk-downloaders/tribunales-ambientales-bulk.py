#!/usr/bin/env python3
"""Bulk Tribunales Ambientales de Chile.

Chile tiene 3 Tribunales Ambientales:
- 1ro (Antofagasta): tribunalambiental.cl/sentencias/ → 1ra y 2da
- 2do (Santiago): tribunalambiental.cl (mismo dominio, /sentencias/)
- 3ro (Valdivia): 3ta.cl/sentencias/

El 1° y 2° comparten dominio tribunalambiental.cl. Filtramos por ruta
de archivo del PDF (cada tribunal pone en su subcarpeta).
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error, urllib.parse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"

INDEXES = {
    "tribunal-12":  "https://www.tribunalambiental.cl/sentencias/",
    "tribunal-3":   "https://3ta.cl/sentencias/",
}
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias ("
        "url TEXT PRIMARY KEY, tribunal TEXT, "
        "downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def discover_pdfs(index_url: str, tribunal_label: str) -> list[tuple[str, str]]:
    req = urllib.request.Request(index_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", errors="replace")
    urls = set()
    base = "/".join(index_url.split("/")[:3])
    for m in re.finditer(r'href=["\']([^"\']+\.pdf)["\']', body, re.IGNORECASE):
        u = m.group(1)
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = base + u
        elif not u.startswith("http"):
            u = urllib.parse.urljoin(index_url, u)
        urls.add(u)
    return [(u, tribunal_label) for u in sorted(urls)]


def safe_filename(url: str) -> str:
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:200]


def download(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    parts = urllib.parse.urlsplit(url)
    encoded_path = urllib.parse.quote(parts.path, safe="/%")
    encoded_url = urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment)
    )
    try:
        req = urllib.request.Request(
            encoded_url, headers={"User-Agent": USER_AGENT}
        )
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",
                        default=str(_REPO_ROOT / "chile/data/tribunales-ambientales"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    print("[FASE 1] Descubriendo PDFs Tribunales Ambientales...", flush=True)
    all_items: list[tuple[str, str]] = []
    for label, index_url in INDEXES.items():
        try:
            items = discover_pdfs(index_url, label)
            print(f"  {label}: {len(items)} PDFs", flush=True)
            for u, t in items:
                conn.execute(
                    "INSERT OR IGNORE INTO sentencias(url, tribunal) "
                    "VALUES (?, ?)", (u, t),
                )
                all_items.append((u, t))
        except Exception as e:
            print(f"  {label}: ERR {e}", flush=True)
    conn.commit()

    pending = [
        (u, t) for u, t in all_items
        if conn.execute(
            "SELECT downloaded FROM sentencias WHERE url=?", (u,)
        ).fetchone()[0] == 0
    ]
    print(f"\n[FASE 2] Descargando {len(pending)} PDFs...", flush=True)
    if not pending:
        return 0

    def worker(item):
        url, tribunal = item
        dest = output_dir / tribunal / safe_filename(url)
        status = download(url, dest)
        if status in ("ok", "skip"):
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute(
                    "UPDATE sentencias SET downloaded=1 WHERE url=?", (url,)
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
            if i % 100 == 0 or i == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(pending)}] ok={_STATS['ok']} "
                    f"404={_STATS['404']} err={_STATS['err']} | {mb:.0f} MB",
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
