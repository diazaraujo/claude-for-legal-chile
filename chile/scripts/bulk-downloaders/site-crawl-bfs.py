#!/usr/bin/env python3
# std:input --seeds <url,url> --domain <host> --name <slug>
# std:output PDFs encontrados crawleando desde los seeds, en data/<name>/ + manifest
# std:deps stdlib (urllib + sqlite3 + re)
"""
Crawler BFS genérico desde URLs semilla (mismo dominio). Para compendios/portales
sin sitemap ni REST (Super Salud, SP/Pensiones y otros reguladores w3/CMS): parte
de las páginas semilla, sigue links del mismo dominio hasta --max-pages, y baja
todos los PDFs que encuentra. Idempotente.

Ej: python site-crawl-bfs.py --name superdesalud --domain supersalud.gob.cl \
      --seeds "https://www.superdesalud.gob.cl/normativa/compendio-procedimientos/,..."
"""
from __future__ import annotations
import argparse, re, sqlite3, subprocess, sys, time
import urllib.parse, urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
_HREF = re.compile(r'href="([^"#?]+)"', re.I)


def http_get(url: str, timeout=40) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def init_manifest(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db), check_same_thread=False, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS pdfs (url TEXT PRIMARY KEY, src TEXT, "
              "downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def crawl(conn, seeds, domain, max_pages) -> int:
    seen, q = set(), deque(seeds)
    pages, found = 0, 0
    while q and pages < max_pages:
        url = q.popleft()
        if url in seen:
            continue
        seen.add(url)
        body = http_get(url)
        if not body:
            continue
        pages += 1
        try:
            text = body.decode("utf-8", "replace")
        except Exception:
            continue
        for href in _HREF.findall(text):
            try:
                full = urllib.parse.urljoin(url, href)
                host = urllib.parse.urlsplit(full).netloc
            except ValueError:
                continue  # URL malformada en el HTML (ej. Invalid IPv6) → saltar
            if domain not in host:
                continue
            if full.lower().endswith(".pdf"):
                with _LOCK:
                    found += conn.execute(
                        "INSERT OR IGNORE INTO pdfs(url, src) VALUES (?,?)", (full, url)).rowcount
            elif full not in seen and len(seen) + len(q) < max_pages * 3 and \
                    not re.search(r'\.(jpg|png|gif|css|js|zip|xls|doc)x?$', full, re.I):
                q.append(full)
        if pages % 50 == 0:
            with _LOCK:
                conn.commit()
            print(f"  [crawl] páginas={pages} pdfs={found} cola={len(q)}", flush=True)
    conn.commit()
    print(f"[crawl] {pages} páginas, {found} PDFs nuevos", flush=True)
    return found


def download_one(url, out_dir):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", urllib.parse.unquote(url.rsplit("/", 1)[-1])) or "doc.pdf"
    dest = out_dir / "pdfs" / name
    txt = out_dir / "txt" / (name + ".txt")
    if dest.exists() and dest.stat().st_size > 0:
        return (url, "skip", dest.stat().st_size)
    data = http_get(url, timeout=90)
    if not data or data[:4] != b"%PDF":
        return (url, "err", 0)
    dest.parent.mkdir(parents=True, exist_ok=True); txt.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    try:
        subprocess.run(["pdftotext", "-layout", str(dest), str(txt)], capture_output=True, timeout=120)
    except Exception:
        pass
    return (url, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--max-pages", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    out_root = _REPO_ROOT / "chile/data" / args.name
    conn = init_manifest(out_root / "manifest.sqlite3")
    crawl(conn, [s.strip() for s in args.seeds.split(",") if s.strip()], args.domain, args.max_pages)
    total = conn.execute("SELECT count(*) FROM pdfs").fetchone()[0]
    print(f"[manifest] {total} PDFs", flush=True)
    if args.list_only:
        return 0
    rows = [r[0] for r in conn.execute("SELECT url FROM pdfs WHERE downloaded=0").fetchall()]
    print(f"[fetch] {len(rows)} PDFs (workers={args.workers})", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, u, out_root): u for u in rows}
        for fut in as_completed(futs):
            url, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE pdfs SET downloaded=1, size=? WHERE url=?", (size, url))
                    conn.commit()
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
