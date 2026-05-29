#!/usr/bin/env python3
# std:input -
# std:output PDFs TRICEL + manifest
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download TRICEL (Tribunal Calificador de Elecciones).

Portal: tribunalcalificador.cl (alias www.tricel.cl). WordPress con WP REST
API abierto. ~662 PDFs publicados (~2010-presente).

NOTA: TRICEL también tiene portal Lexsoft (tricel.lexsoft.cl) con histórico
completo pero requiere login. Acá solo bajamos lo que TRICEL publica en su
WordPress público.

Fase 1: enumera media PDFs vía /wp-json/wp/v2/media.
Fase 2: descarga PDFs en paralelo.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/tricel"

BASE = "https://tribunalcalificador.cl"
MEDIA_URL = BASE + "/wp-json/wp/v2/media"
UA = "claude-legal-chile/0.8 bulk-tricel"

_STATS = {"pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pdfs ("
        "id INTEGER PRIMARY KEY, slug TEXT, title TEXT, url TEXT, "
        "year INTEGER, date_gmt TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)"
    )
    conn.commit()
    return conn


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_year(src: str, date_gmt: str | None) -> int | None:
    m = re.search(r"/uploads/(\d{4})/", src)
    if m: return int(m.group(1))
    if date_gmt:
        m = re.match(r"(\d{4})", date_gmt)
        if m: return int(m.group(1))
    return None


def enumerate_media(conn: sqlite3.Connection) -> int:
    page = 1
    total = 0
    while True:
        url = f"{MEDIA_URL}?per_page=100&page={page}&mime_type=application/pdf"
        print(f"  page {page}", flush=True)
        try:
            body = http_get(url, timeout=90)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                break
            raise
        items = json.loads(body)
        if not items:
            break
        for m in items:
            mid = m.get("id")
            slug = m.get("slug") or ""
            title = (m.get("title") or {}).get("rendered") or ""
            src = m.get("source_url") or ""
            date_gmt = m.get("date_gmt")
            if not src.lower().endswith(".pdf"):
                continue
            year = parse_year(src, date_gmt)
            conn.execute(
                "INSERT OR IGNORE INTO pdfs(id,slug,title,url,year,date_gmt) "
                "VALUES (?,?,?,?,?,?)",
                (mid, slug, title, src, year, date_gmt),
            )
            total += 1
        conn.commit()
        if len(items) < 100:
            break
        page += 1
    return total


def download_one(row: tuple, out_dir: Path) -> tuple[int, bool, int]:
    pid, url, year = row
    fname = url.rsplit("/", 1)[-1]
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", fname)
    subdir = out_dir / (str(year) if year else "sin-anio")
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{pid}_{safe}"
    if dest.exists() and dest.stat().st_size > 1024:
        with _LOCK:
            _STATS["pdfs_skip"] += 1
        return (pid, True, dest.stat().st_size)
    try:
        body = http_get(url, timeout=180)
    except Exception:
        with _LOCK:
            _STATS["pdfs_err"] += 1
        return (pid, False, 0)
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(body)
    tmp.rename(dest)
    with _LOCK:
        _STATS["pdfs_ok"] += 1
        _STATS["bytes"] += len(body)
    return (pid, True, len(body))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUTPUT_ROOT))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== TRICEL bulk ===", flush=True)
    print(f"Fase 1: enumerando WP media...", flush=True)
    t0 = time.time()
    n = enumerate_media(conn)
    print(f"  enumerados: {n} ({time.time()-t0:.1f}s)", flush=True)

    if args.list_only:
        return 0

    rows = conn.execute(
        "SELECT id, url, year FROM pdfs WHERE downloaded=0"
    ).fetchall()
    print(f"\nFase 2: descargando {len(rows)} PDFs", flush=True)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(download_one, r, out) for r in rows]
        done = 0
        for fut in as_completed(futs):
            pid, ok, size = fut.result()
            if ok:
                conn.execute("UPDATE pdfs SET downloaded=1, size=? WHERE id=?",
                             (size, pid))
            done += 1
            if done % 25 == 0:
                conn.commit()
                with _LOCK:
                    s = dict(_STATS)
                print(f"  done={done}/{len(rows)} {s}", flush=True)
    conn.commit()
    print(f"\n[DONE] {time.time()-t0:.0f}s | {dict(_STATS)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
