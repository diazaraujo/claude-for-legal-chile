#!/usr/bin/env python3
"""Bulk FNE — Fiscalía Nacional Económica via WP REST API.

Itera por las categorías LEGAL_CATEGORIES (dictámenes, resoluciones,
sentencias, requerimientos, etc.) y guarda metadata + content HTML
de cada post. Además descarga PDFs embebidos en content.
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-fne/src"))
from mcp_fne.fne_client import FNEClient, LEGAL_CATEGORIES

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
_STATS = {"posts": 0, "pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS posts ("
        "post_id INTEGER PRIMARY KEY, date TEXT, slug TEXT, "
        "title TEXT, link TEXT, categorias TEXT, "
        "downloaded INTEGER DEFAULT 0, pdfs INTEGER DEFAULT 0)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pdfs ("
        "url TEXT PRIMARY KEY, post_id INTEGER, "
        "downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def safe_filename(url: str) -> str:
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:200]


def download_pdf(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["pdfs_skip"] += 1
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
            _STATS["pdfs_ok"] += 1
            _STATS["bytes"] += len(body)
        return "ok"
    except Exception:
        with _LOCK: _STATS["pdfs_err"] += 1
        return "err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/fne"))
    parser.add_argument("--categories", default="",
                        help="Comma-separated category IDs (default: todas las legal)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-pdfs", action="store_true")
    parser.add_argument("--fetch-links", action="store_true",
                        help="Fetch HTML de cada post link (API esconde content)")
    parser.add_argument("--skip-enum", action="store_true",
                        help="Saltar Fase 1 (usa manifest existente)")
    args = parser.parse_args()

    if args.categories:
        cats = {int(x): LEGAL_CATEGORIES.get(int(x), f"cat-{x}")
                for x in args.categories.split(",")}
    else:
        cats = LEGAL_CATEGORIES

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    client = FNEClient(rate_seconds=0.4)

    if args.skip_enum:
        existing = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        print(f"[FASE 1 SKIP] manifest tiene {existing} posts", flush=True)
        if existing == 0:
            print("  ERROR: manifest vacío.", flush=True)
            return 1
    else:
        _enumerate(client, cats, conn, output_dir)

    if args.fetch_links:
        _fetch_links_phase(conn, db_path, output_dir, args.workers)

    if args.skip_pdfs:
        return 0
    return _pdfs_phase(conn, db_path, output_dir, args.workers)


def _enumerate(client, cats, conn, output_dir):
    print(f"[FASE 1] Enumerando posts FNE en {len(cats)} categorías...", flush=True)
    for cat_id, cat_name in cats.items():
        # Reverse chronological: per_page=100, page=1 has most recent
        page, total_pages = 1, None
        cat_count = 0
        while total_pages is None or page <= total_pages:
            try:
                posts, total_pages = client.list_posts_by_category(
                    cat_id, page=page, per_page=100,
                )
            except Exception as e:
                print(f"  cat {cat_id} page {page}: ERR {e}", flush=True)
                break
            for p in posts:
                conn.execute(
                    "INSERT OR REPLACE INTO posts("
                    "post_id, date, slug, title, link, categorias, "
                    "downloaded, pdfs) VALUES (?, ?, ?, ?, ?, ?, "
                    "COALESCE((SELECT downloaded FROM posts WHERE post_id=?), 0), "
                    "COALESCE((SELECT pdfs FROM posts WHERE post_id=?), 0))",
                    (p.post_id, p.date, p.slug, p.title, p.link,
                     ",".join(map(str, p.categorias)), p.post_id, p.post_id),
                )
                # Save content HTML to disk
                year = p.date[:4] if p.date else "0000"
                html_dest = output_dir / "posts" / year / f"{p.post_id}.html"
                if not html_dest.exists():
                    html_dest.parent.mkdir(parents=True, exist_ok=True)
                    html_dest.write_text(p.content_html, encoding="utf-8")
                # Extract PDFs
                pdfs = client.extract_pdf_urls(p.content_html)
                for u in pdfs:
                    conn.execute(
                        "INSERT OR IGNORE INTO pdfs(url, post_id) VALUES (?, ?)",
                        (u, p.post_id),
                    )
                cat_count += 1
            conn.commit()
            page += 1
        print(f"  cat {cat_id} ({cat_name[:40]}): {cat_count} posts en {total_pages or 0} pages",
              flush=True)

    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_pdfs = conn.execute("SELECT COUNT(*) FROM pdfs").fetchone()[0]
    print(f"\n[FASE 1 DONE] {total_posts} posts, {total_pdfs} PDFs embebidos", flush=True)


def _fetch_links_phase(conn, db_path, output_dir, workers):
    """Fetch HTML real de cada post link (API WP esconde content).
    Re-extrae PDF URLs del HTML descargado y los inserta al manifest.
    """
    rows = conn.execute(
        "SELECT post_id, link, date FROM posts WHERE downloaded=0 "
        "AND link IS NOT NULL AND link != '' ORDER BY date DESC"
    ).fetchall()
    print(f"\n[FASE LINKS] Descargando HTML de {len(rows)} post links...", flush=True)
    if not rows:
        return

    from mcp_fne.fne_client import FNEClient
    fclient = FNEClient(rate_seconds=0.0)
    pdf_re_global = __import__("re").compile(
        r'href=["\']([^"\']+\.pdf)["\']', __import__("re").IGNORECASE,
    )

    def worker(row):
        post_id, link, date = row
        year = (date[:4] if date else "0000")
        html_dest = output_dir / "links" / year / f"{post_id}.html"
        if html_dest.exists() and html_dest.stat().st_size > 100:
            with _LOCK: _STATS["pdfs_skip"] += 1
            return post_id, "skip"
        html_dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(
                link, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
            tmp = html_dest.with_suffix(".tmp")
            tmp.write_bytes(body)
            tmp.rename(html_dest)
            # Re-extraer PDFs del HTML real (no del API)
            html_text = body.decode("utf-8", errors="replace")
            for m in pdf_re_global.finditer(html_text):
                u = m.group(1)
                if u.startswith("//"):
                    u = "https:" + u
                elif u.startswith("/"):
                    u = "https://www.fne.gob.cl" + u
                # Filter: only wp-content/uploads (documentos), exclude
                # PDFs de header/menu (e.g. codigo-etica)
                if "wp-content/uploads" not in u:
                    continue
                if "codigo-etica" in u.lower() or "logo" in u.lower():
                    continue
                c = sqlite3.connect(str(db_path), timeout=30)
                try:
                    c.execute(
                        "INSERT OR IGNORE INTO pdfs(url, post_id) "
                        "VALUES (?, ?)", (u, post_id),
                    )
                    c.commit()
                finally:
                    c.close()
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute("UPDATE posts SET downloaded=1 WHERE post_id=?",
                          (post_id,))
                c.commit()
            finally:
                c.close()
            with _LOCK:
                _STATS["pdfs_ok"] += 1
                _STATS["bytes"] += len(body)
            return post_id, "ok"
        except Exception:
            with _LOCK: _STATS["pdfs_err"] += 1
            return post_id, "err"

    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, r) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 100 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(rows) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(rows)}] ok={_STATS['pdfs_ok']} "
                    f"err={_STATS['pdfs_err']} | {mb:.0f} MB | "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )


def _pdfs_phase(conn, db_path, output_dir, workers):
    pending_pdfs = conn.execute(
        "SELECT url, post_id FROM pdfs WHERE downloaded=0"
    ).fetchall()
    print(f"\n[FASE 2] Descargando {len(pending_pdfs)} PDFs...", flush=True)
    if not pending_pdfs:
        return 0

    def worker(item):
        url, post_id = item
        c = sqlite3.connect(str(db_path), timeout=30)
        try:
            row = c.execute(
                "SELECT date FROM posts WHERE post_id=?", (post_id,)
            ).fetchone()
            year = (row[0][:4] if row and row[0] else "0000")
        finally:
            c.close()
        dest = output_dir / "pdfs" / year / f"{post_id}_{safe_filename(url)}"
        status = download_pdf(url, dest)
        if status in ("ok", "skip"):
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute(
                    "UPDATE pdfs SET downloaded=1 WHERE url=?", (url,)
                )
                c.commit()
            finally:
                c.close()
        return url, status

    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, p) for p in pending_pdfs]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
            except Exception:
                pass
            if i % 50 == 0 or i == len(pending_pdfs):
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(pending_pdfs)}] ok={_STATS['pdfs_ok']} "
                    f"err={_STATS['pdfs_err']} | {mb:.0f} MB",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | {_STATS['pdfs_ok']} PDFs, "
        f"{_STATS['bytes']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
