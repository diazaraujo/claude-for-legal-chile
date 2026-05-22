#!/usr/bin/env python3
"""Bulk DT dictámenes — iterar por año + scrape de cada w3-article.

DT no expone PDFs directos uniformes — la página w3-article-N.html
contiene el texto del dictamen y a veces link a PDF. Por ahora bulk
guarda el HTML de cada dictamen.
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
import datetime

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-dt-dictamenes/src"))
from mcp_dt_dictamenes.dt_client import DTClient

USER_AGENT = "claude-legal-chile/0.7 bulk-dt"
_STATS = {"ok": 0, "skip": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dictamenes ("
        "article_id INTEGER PRIMARY KEY, year INTEGER, title TEXT, "
        "url TEXT, downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def fetch_html(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 100:
        with _LOCK: _STATS["skip"] += 1
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _LOCK:
            _STATS["ok"] += 1
            _STATS["bytes"] += len(body)
        return True
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-year", type=int, default=2010)
    parser.add_argument("--to-year", type=int,
                        default=datetime.date.today().year)
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/dt"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-html", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    # FASE 1: enumerar por año (reverse)
    print(f"[FASE 1] Enumerando dictámenes DT {args.to_year}..{args.from_year}...")
    client = DTClient(rate_seconds=1.0)
    total_meta = 0
    for year in range(args.to_year, args.from_year - 1, -1):
        try:
            results = client.list_all_by_year(year)
            for r in results:
                conn.execute(
                    "INSERT OR REPLACE INTO dictamenes(article_id, year, title, url, downloaded) "
                    "VALUES (?, ?, ?, ?, COALESCE((SELECT downloaded FROM dictamenes WHERE article_id=?), 0))",
                    (r.article_id, year, r.title, r.url, r.article_id),
                )
            conn.commit()
            total_meta += len(results)
            print(f"  {year}: {len(results)} dictámenes (total {total_meta})", flush=True)
        except Exception as e:
            print(f"  {year}: ERR {e}", flush=True)

    print(f"\n[FASE 1 DONE] {total_meta} dictámenes total")

    if args.skip_html:
        return 0

    # FASE 2: descargar HTML de cada article
    print(f"\n[FASE 2] Descargando HTMLs...")
    rows = conn.execute(
        "SELECT article_id, year, url FROM dictamenes WHERE downloaded = 0 ORDER BY article_id DESC"
    ).fetchall()
    print(f"  Pendientes: {len(rows)}\n")
    if not rows:
        return 0

    def worker(row):
        aid, year, url = row
        dest = output_dir / str(year) / f"{aid}.html"
        ok = fetch_html(url, dest)
        if ok:
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute("UPDATE dictamenes SET downloaded = 1 WHERE article_id = ?", (aid,))
                c.commit()
            finally:
                c.close()
        return aid, ok

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, fut in enumerate(as_completed([pool.submit(worker, r) for r in rows]), 1):
            fut.result()
            if i % 100 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                print(f"  [{i}/{len(rows)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                      f"err={_STATS['err']} | {mb:.1f} MB", flush=True)

    print(f"\n[DONE] {time.time()-start:.0f}s | {_STATS['ok']} HTMLs, {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
