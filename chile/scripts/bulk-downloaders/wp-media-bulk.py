#!/usr/bin/env python3
# std:input --base <url-wordpress> --name <slug>
# std:output PDFs del sitio en data/<name>/ + manifest
# std:deps stdlib (urllib + sqlite3) — opcional Zyte si --zyte
"""
Bulk download genérico de PDFs publicados en un sitio **WordPress** vía el REST
`/wp-json/wp/v2/media`. Reusable para cualquier organismo gov chileno montado en
WP (DGA, SUBTRANS, etc. — verificado 2026-05-29).

Fase 1 (--list-only): enumera TODOS los media `application/pdf` a manifest.
Fase 2: descarga los pendientes en paralelo.
Idempotente vía manifest. Reverse cronológico (date_gmt desc) — si se corta, lo
más reciente queda primero.

Ej:
  python wp-media-bulk.py --base https://dga.mop.gob.cl --name dga
  python wp-media-bulk.py --base https://www.subtrans.gob.cl --name subtrans
"""
from __future__ import annotations
import argparse, base64, json, os, re, sqlite3, sys, time
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
UA = "claude-legal-chile/0.8 wp-media-bulk (research corpus)"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}


def http_get(url: str, timeout: int = 60, zyte_auth: str | None = None) -> bytes:
    if zyte_auth:
        payload = json.dumps({"url": url, "httpResponseBody": True}).encode()
        req = urllib.request.Request(
            "https://api.zyte.com/v1/extract", data=payload,
            headers={"Authorization": f"Basic {zyte_auth}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return base64.b64decode(json.loads(r.read())["httpResponseBody"])
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pdfs ("
        "id INTEGER PRIMARY KEY, slug TEXT, title TEXT, url TEXT, "
        "year INTEGER, date_gmt TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    conn.commit()
    return conn


def parse_year(url: str, date_gmt: str | None) -> int | None:
    m = re.search(r"/uploads/(\d{4})/", url or "")
    if m:
        return int(m.group(1))
    if date_gmt and len(date_gmt) >= 4 and date_gmt[:4].isdigit():
        return int(date_gmt[:4])
    return None


def enumerate_media(conn, base: str, zyte_auth=None) -> int:
    media_url = base.rstrip("/") + "/wp-json/wp/v2/media"
    page, nuevos = 1, 0
    while True:
        url = f"{media_url}?per_page=100&page={page}&mime_type=application/pdf&orderby=date&order=desc"
        try:
            body = http_get(url, zyte_auth=zyte_auth)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):  # fin de páginas
                break
            print(f"  [enum] HTTP {e.code} page {page}", flush=True)
            break
        try:
            items = json.loads(body)
        except Exception:
            break
        if not items:
            break
        with _LOCK:
            for it in items:
                src = it.get("source_url", "")
                if not src.lower().endswith(".pdf"):
                    continue
                title = (it.get("title", {}) or {}).get("rendered", "")
                dg = it.get("date_gmt") or it.get("date")
                cur = conn.execute(
                    "INSERT OR IGNORE INTO pdfs(id, slug, title, url, year, date_gmt) "
                    "VALUES (?,?,?,?,?,?)",
                    (it.get("id"), it.get("slug", ""), title, src,
                     parse_year(src, dg), dg))
                nuevos += cur.rowcount
            conn.commit()
        print(f"  [enum] page {page}: +{len(items)} (manifest nuevos={nuevos})", flush=True)
        page += 1
        time.sleep(0.2)
    return nuevos


def download_one(row, out_dir: Path, zyte_auth=None):
    _id, url = row
    name = re.sub(r"[^A-Za-z0-9._-]", "_", url.rsplit("/", 1)[-1]) or f"{_id}.pdf"
    dest = out_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return (_id, "skip", dest.stat().st_size)
    try:
        data = http_get(url, zyte_auth=zyte_auth)
    except Exception:
        return (_id, "err", 0)
    if not data or len(data) < 100:
        return (_id, "err", 0)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.rename(dest)
    return (_id, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="URL raíz del sitio WordPress")
    ap.add_argument("--name", required=True, help="slug carpeta destino en data/")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--zyte", action="store_true", help="usar Zyte (env ZYTE_API_KEY)")
    args = ap.parse_args()

    zyte_auth = None
    if args.zyte:
        key = os.environ.get("ZYTE_API_KEY", "")
        if not key:
            print("ERROR: --zyte requiere env ZYTE_API_KEY", flush=True)
            return 2
        zyte_auth = base64.b64encode(f"{key}:".encode()).decode()

    out_root = _REPO_ROOT / "chile/data" / args.name
    conn = init_manifest(out_root / "manifest.sqlite3")

    n = enumerate_media(conn, args.base, zyte_auth)
    total = conn.execute("SELECT count(*) FROM pdfs").fetchone()[0]
    print(f"[enum] {args.name}: {total} PDFs en manifest (+{n} nuevos)", flush=True)
    if args.list_only:
        return 0

    rows = conn.execute(
        "SELECT id, url FROM pdfs WHERE downloaded=0 ORDER BY date_gmt DESC").fetchall()
    out_dir = out_root / "pdfs"
    print(f"[fetch] {args.name}: {len(rows)} pendientes (workers={args.workers})", flush=True)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, r, out_dir, zyte_auth): r for r in rows}
        for fut in as_completed(futs):
            _id, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE pdfs SET downloaded=1, size=? WHERE id=?",
                                 (size, _id))
                    conn.commit()
            done += 1
            if done % 50 == 0:
                el = time.time() - t0
                rate = done / el if el else 0
                print(f"  done={done}/{len(rows)} {_STATS} rate={rate:.1f}/s", flush=True)
    print(f"[DONE] {args.name} {time.time()-t0:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
