#!/usr/bin/env python3
# std:input --sitemap <url> --name <slug>
# std:output PDFs enlazados desde las páginas del sitemap, en data/<name>/ + manifest
# std:deps stdlib (urllib + sqlite3 + re)
"""
Crawler genérico sitemap → PDFs. Para sitios donde la REST API está bloqueada
(p.ej. CDE: wp-json 403) pero el sitemap XML es público. Recorre el sitemap
(incluye sub-sitemaps anidados), baja cada página HTML y extrae los enlaces a
PDF (absolutos o /uploads/...), dedup + descarga idempotente.

Fase 1 (--list-only): enumera URLs de PDF a manifest.
Fase 2: descarga los pendientes.

Ej: python site-pdf-crawler.py --sitemap https://www.cde.cl/wp-sitemap.xml --name cde
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_PDF_RE = re.compile(r"""href=["']([^"']+?\.pdf)["']""", re.I)


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("CREATE TABLE IF NOT EXISTS pdfs ("
                 "url TEXT PRIMARY KEY, src_page TEXT, "
                 "downloaded INTEGER DEFAULT 0, size INTEGER)")
    conn.commit()
    return conn


def collect_sitemap_urls(sitemap: str, seen=None) -> list[str]:
    """Resuelve sitemaps anidados → lista de URLs de página finales."""
    seen = seen if seen is not None else set()
    if sitemap in seen:
        return []
    seen.add(sitemap)
    try:
        body = http_get(sitemap).decode("utf-8", "replace")
    except Exception as e:
        print(f"  [sitemap] err {sitemap}: {e}", flush=True)
        return []
    locs = _LOC_RE.findall(body)
    pages, subs = [], []
    for loc in locs:
        (subs if loc.lower().endswith(".xml") else pages).append(loc)
    for sub in subs:
        pages.extend(collect_sitemap_urls(sub, seen))
        time.sleep(0.1)
    return pages


def extract_pdfs_from_page(page_url: str, conn) -> int:
    try:
        html = http_get(page_url).decode("utf-8", "replace")
    except Exception:
        return 0
    nuevos = 0
    with _LOCK:
        for href in dict.fromkeys(_PDF_RE.findall(html)):
            full = urllib.parse.urljoin(page_url, href)
            cur = conn.execute(
                "INSERT OR IGNORE INTO pdfs(url, src_page) VALUES (?,?)",
                (full, page_url))
            nuevos += cur.rowcount
        conn.commit()
    return nuevos


def download_one(url: str, out_dir: Path):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", url.rsplit("/", 1)[-1]) or "doc.pdf"
    dest = out_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return (url, "skip", dest.stat().st_size)
    try:
        data = http_get(url)
    except Exception:
        return (url, "err", 0)
    if not data or len(data) < 100 or data[:4] != b"%PDF":
        return (url, "err", 0)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.rename(dest)
    return (url, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    out_root = _REPO_ROOT / "chile/data" / args.name
    conn = init_manifest(out_root / "manifest.sqlite3")

    pages = collect_sitemap_urls(args.sitemap)
    print(f"[crawl] {args.name}: {len(pages)} páginas en sitemap", flush=True)
    scanned = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(extract_pdfs_from_page, p, conn): p for p in pages}
        for fut in as_completed(futs):
            fut.result()
            scanned += 1
            if scanned % 100 == 0:
                tot = conn.execute("SELECT count(*) FROM pdfs").fetchone()[0]
                print(f"  scanned={scanned}/{len(pages)} pdfs={tot}", flush=True)
    total = conn.execute("SELECT count(*) FROM pdfs").fetchone()[0]
    print(f"[crawl] {args.name}: {total} PDFs únicos", flush=True)
    if args.list_only:
        return 0

    rows = [r[0] for r in conn.execute(
        "SELECT url FROM pdfs WHERE downloaded=0").fetchall()]
    out_dir = out_root / "pdfs"
    print(f"[fetch] {len(rows)} pendientes", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, u, out_dir): u for u in rows}
        for fut in as_completed(futs):
            url, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE pdfs SET downloaded=1, size=? WHERE url=?",
                                 (size, url))
                    conn.commit()
            done += 1
            if done % 50 == 0:
                print(f"  done={done}/{len(rows)} {_STATS}", flush=True)
    print(f"[DONE] {args.name} | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
