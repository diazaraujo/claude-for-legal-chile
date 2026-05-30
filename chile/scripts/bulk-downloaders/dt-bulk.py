#!/usr/bin/env python3
"""Bulk DT dictámenes — iterar por año + scrape de cada w3-article.

DT no expone PDFs directos uniformes — la página w3-article-N.html
contiene el texto del dictamen y a veces link a PDF. Por ahora bulk
guarda el HTML de cada dictamen.
"""
from __future__ import annotations
import argparse, os, sqlite3, sys, time, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock, local
import datetime

import requests
from requests.adapters import HTTPAdapter

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-dt-dictamenes/src"))
from mcp_dt_dictamenes.dt_client import DTClient

USER_AGENT = "Mozilla/5.0 claude-legal-chile/0.7 (unholster.com)"
_STATS = {"ok": 0, "skip": 0, "err": 0, "bytes": 0}
_LOCK = Lock()
_THREAD = local()
_ZYTE_AUTH = None  # base64("<key>:") cuando --zyte; bypassa el WAF 301-challenge de DT


def _fetch_via_zyte(url: str) -> bytes | None:
    """browserHtml + geolocation CL — resuelve el challenge JS del WAF de DT."""
    try:
        r = requests.post(
            "https://api.zyte.com/v1/extract",
            headers={"Authorization": f"Basic {_ZYTE_AUTH}"},
            json={"url": url, "browserHtml": True, "geolocation": "CL"},
            timeout=120,
        )
        if r.status_code != 200:
            return None
        html = r.json().get("browserHtml", "")
        return html.encode("utf-8") if html else None
    except Exception:
        return None


def _session() -> requests.Session:
    s = getattr(_THREAD, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"})
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=0)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _THREAD.session = s
    return s


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
        if _ZYTE_AUTH:
            body = _fetch_via_zyte(url)
            if not body:
                with _LOCK: _STATS["err"] += 1
                return False
        else:
            # requests con per-thread session + timeout (connect, read) + max 3 redirects.
            s = _session()
            s.max_redirects = 3
            r = s.get(url, timeout=(4, 6), allow_redirects=True)
            if r.status_code != 200:
                with _LOCK: _STATS["err"] += 1
                return False
            body = r.content
        if len(body) < 100:
            with _LOCK: _STATS["err"] += 1
            return False
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
    parser.add_argument("--skip-enum", action="store_true",
                        help="Saltar Fase 1 (usar enum existente del manifest)")
    parser.add_argument("--zyte", action="store_true",
                        help="Descargar vía Zyte browserHtml+geo CL (bypass WAF). "
                             "Lee ZYTE_API_KEY de env o chile/.env")
    args = parser.parse_args()

    if args.zyte:
        import base64 as _b64
        key = os.environ.get("ZYTE_API_KEY", "")
        if not key:
            envf = _REPO_ROOT / "chile/.env"
            if envf.exists():
                for line in envf.read_text().splitlines():
                    if line.startswith("ZYTE_API_KEY="):
                        key = line.split("=", 1)[1].strip()
        if not key:
            print("ERROR: --zyte requiere ZYTE_API_KEY (env o chile/.env)", flush=True)
            return 2
        global _ZYTE_AUTH
        _ZYTE_AUTH = _b64.b64encode(f"{key}:".encode()).decode()
        print("[ZYTE] browserHtml + geolocation=CL habilitado", flush=True)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    if args.skip_enum:
        existing = conn.execute("SELECT COUNT(*) FROM dictamenes").fetchone()[0]
        print(f"[FASE 1 SKIP] manifest tiene {existing} dictámenes enumerados", flush=True)
        if existing == 0:
            print("  ERROR: manifest vacío, no se puede skip enum.", flush=True)
            return 1
        return _phase2(conn, db_path, output_dir, args)

    # FASE 1: descubrir todos los period_ids del index + enumerar dictámenes
    # de cada uno (1 page per period = 1 año). Reverse: año más reciente primero.
    print(f"[FASE 1] Descubriendo period_ids DT...", flush=True)
    client = DTClient(rate_seconds=0.8)
    periods = client.discover_period_ids()
    print(f"  {len(periods)} period_ids descubiertos", flush=True)
    # Sort: año más reciente primero (label numérico desc)
    sorted_periods = sorted(
        periods.items(),
        key=lambda x: int(x[1]) if x[1].isdigit() else -1,
        reverse=True,
    )
    total_meta = 0
    for pid, label in sorted_periods:
        year_val = int(label) if label.isdigit() else 0
        try:
            results = client.list_by_period_id(pid)
            for r in results:
                conn.execute(
                    "INSERT OR REPLACE INTO dictamenes(article_id, year, title, url, downloaded) "
                    "VALUES (?, ?, ?, ?, COALESCE((SELECT downloaded FROM dictamenes WHERE article_id=?), 0))",
                    (r.article_id, year_val, r.title, r.url, r.article_id),
                )
            conn.commit()
            total_meta += len(results)
            print(f"  period {pid} [{label}]: {len(results)} dictámenes (total {total_meta})", flush=True)
        except Exception as e:
            print(f"  period {pid} [{label}]: ERR {e}", flush=True)

    print(f"\n[FASE 1 DONE] {total_meta} dictámenes total")

    return _phase2(conn, db_path, output_dir, args)


def _phase2(conn, db_path, output_dir, args) -> int:
    if args.skip_html:
        return 0
    print(f"\n[FASE 2] Descargando HTMLs...", flush=True)
    rows = conn.execute(
        "SELECT article_id, year, url FROM dictamenes WHERE downloaded = 0 "
        "ORDER BY article_id DESC"
    ).fetchall()
    print(f"  Pendientes: {len(rows)}\n", flush=True)
    if not rows:
        return 0

    def worker(row):
        aid, year, url = row
        dest = output_dir / str(year) / f"{aid}.html"
        ok = fetch_html(url, dest)
        if ok:
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute(
                    "UPDATE dictamenes SET downloaded = 1 WHERE article_id = ?",
                    (aid,),
                )
                c.commit()
            finally:
                c.close()
        return aid, ok

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, r) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
            except Exception:
                pass
            if i % 100 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(rows) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(rows)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"err={_STATS['err']} | {mb:.1f} MB | "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )
    print(
        f"\n[DONE] {time.time()-start:.0f}s | {_STATS['ok']} HTMLs, "
        f"{_STATS['bytes']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
