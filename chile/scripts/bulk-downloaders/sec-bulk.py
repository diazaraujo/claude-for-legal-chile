#!/usr/bin/env python3
"""Bulk SEC (Superintendencia de Electricidad y Combustibles).

SEC usa el plugin WP File Download (WPFD) que indexa todos los
archivos en sitemap. Pattern:
  wp-sitemap-posts-wpfd_file-{1,2}.xml
    → /wpfd_file/{slug}/ (HTML page con link al PDF)
    → /sitio-web/descargar/{N}/{cat}/{NN}/{slug}.pdf
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error, urllib.parse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
SITEMAPS = [
    f"https://www.sec.cl/wp-sitemap-posts-wpfd_file-{i}.xml" for i in range(1, 5)
]
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files ("
        "slug TEXT PRIMARY KEY, page_url TEXT, pdf_url TEXT, "
        "downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def discover_pages() -> list[str]:
    pages = []
    for sm in SITEMAPS:
        try:
            req = urllib.request.Request(sm, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", errors="replace")
            locs = re.findall(r"<loc>([^<]+)</loc>", body)
            pages.extend(locs)
            print(f"  {sm.rsplit('/', 1)[-1]}: {len(locs)} entries", flush=True)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  {sm}: 404 (no more sitemaps)", flush=True)
                break
            print(f"  {sm}: HTTP {e.code}", flush=True)
        except Exception as e:
            print(f"  {sm}: ERR {e}", flush=True)
    return pages


def slug_from_page(page_url: str) -> str:
    return page_url.rstrip("/").rsplit("/", 1)[-1]


def find_pdf_url(page_url: str) -> str | None:
    try:
        req = urllib.request.Request(page_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    matches = re.findall(
        r'(https?://[^"\'\s<>]+/(?:sitio-web/descargar|wp-content/uploads)[^"\'\s<>]+\.pdf)',
        body, re.IGNORECASE,
    )
    return matches[0] if matches else None


def safe_filename(url: str) -> str:
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:200]


def download_pdf(url: str, dest: Path) -> str:
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
        req = urllib.request.Request(encoded_url, headers={"User-Agent": USER_AGENT})
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
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/sec"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    # Fase 1: descubrir pages desde sitemap
    existing = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    if existing == 0:
        print("[FASE 1] Descubriendo pages SEC desde sitemap WPFD...", flush=True)
        pages = discover_pages()
        for p in pages:
            slug = slug_from_page(p)
            conn.execute(
                "INSERT OR IGNORE INTO files(slug, page_url) VALUES (?, ?)",
                (slug, p),
            )
        conn.commit()
        existing = len(pages)
    print(f"[FASE 1] {existing} pages SEC en manifest", flush=True)

    # Fase 2: para cada page sin pdf_url, fetch page → find pdf
    rows = conn.execute(
        "SELECT slug, page_url FROM files WHERE pdf_url IS NULL"
    ).fetchall()
    print(f"\n[FASE 2] Buscando PDF URLs en {len(rows)} pages...", flush=True)

    def find_worker(item):
        slug, page_url = item
        pdf_url = find_pdf_url(page_url)
        if pdf_url:
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute("UPDATE files SET pdf_url=? WHERE slug=?",
                          (pdf_url, slug))
                c.commit()
            finally:
                c.close()
        return slug, pdf_url

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(find_worker, r) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 200 == 0 or i == len(rows):
                elapsed = time.time() - start
                print(f"  [{i}/{len(rows)}] elapsed={elapsed:.0f}s",
                      flush=True)

    with_url = conn.execute(
        "SELECT COUNT(*) FROM files WHERE pdf_url IS NOT NULL"
    ).fetchone()[0]
    print(f"  PDFs descubiertos: {with_url}", flush=True)

    # Fase 3: download PDFs
    rows = conn.execute(
        "SELECT slug, pdf_url FROM files WHERE pdf_url IS NOT NULL AND downloaded=0"
    ).fetchall()
    print(f"\n[FASE 3] Descargando {len(rows)} PDFs...", flush=True)

    def dl_worker(item):
        slug, pdf_url = item
        dest = output_dir / "pdfs" / safe_filename(pdf_url)
        status = download_pdf(pdf_url, dest)
        if status in ("ok", "skip"):
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute("UPDATE files SET downloaded=1 WHERE slug=?", (slug,))
                c.commit()
            finally:
                c.close()
        return slug, status

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(dl_worker, r) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 100 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(rows)}] ok={_STATS['ok']} 404={_STATS['404']} "
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
