#!/usr/bin/env python3
# std:input -
# std:output PDFs TCP (boletines + estado diario) + manifest
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download TCP (Tribunal de Contratación Pública) — boletines de
jurisprudencia (mensual/anual) + Estado Diario (PDFs sentenciados).

El portal es WordPress (`tribunaldecontratacionpublica.cl`). Usamos el WP
REST `/wp-json/wp/v2/media` para enumerar TODOS los PDFs históricos.

Fase 1 (--list-only): enumera y guarda manifest sin bajar PDFs.
Fase 2: descarga PDFs faltantes en paralelo.

Categorías capturadas (por nombre de archivo):
- `Boletin*Jurisprudencia*` y `Boletin TCP *` → carpeta `boletines/`
- `ESTADO-DIARIO-*` → carpeta `estado-diario/`
- Resto → carpeta `otros/`
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/tcp"

BASE = "https://tribunaldecontratacionpublica.cl"
MEDIA_URL = BASE + "/wp-json/wp/v2/media"
UA = "claude-legal-chile/0.8 bulk-tcp"

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
        "category TEXT, year INTEGER, date_gmt TEXT, "
        "downloaded INTEGER DEFAULT 0, size INTEGER, sha256 TEXT)"
    )
    conn.commit()
    return conn


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def classify(source_url: str, title: str) -> str:
    name = source_url.rsplit("/", 1)[-1]
    low = name.lower() + " " + (title or "").lower()
    if "boletin" in low:
        return "boletines"
    if "estado-diario" in low or "estado diario" in low:
        return "estado-diario"
    return "otros"


def parse_year(source_url: str, date_gmt: str | None) -> int | None:
    # 1) por URL /wp-content/uploads/YYYY/
    m = re.search(r"/uploads/(\d{4})/", source_url)
    if m: return int(m.group(1))
    # 2) por nombre archivo: -YYYY
    m = re.search(r"-(\d{4})", source_url.rsplit("/", 1)[-1])
    if m and 1990 < int(m.group(1)) < 2050:
        return int(m.group(1))
    # 3) por date_gmt
    if date_gmt:
        m = re.match(r"(\d{4})", date_gmt)
        if m: return int(m.group(1))
    return None


def enumerate_media(conn: sqlite3.Connection, max_pages: int | None = None) -> int:
    """Pagina WP media (per_page=100), filtra mime=application/pdf."""
    page = 1
    total_seen = 0
    while True:
        if max_pages and page > max_pages:
            break
        url = f"{MEDIA_URL}?per_page=100&page={page}&mime_type=application/pdf"
        print(f"  page {page} → fetching", flush=True)
        try:
            body = http_get(url, timeout=90)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                print(f"  page {page}: HTTP {e.code} (final)", flush=True)
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
            cat = classify(src, title)
            year = parse_year(src, date_gmt)
            conn.execute(
                "INSERT OR IGNORE INTO pdfs(id,slug,title,url,category,year,date_gmt) "
                "VALUES (?,?,?,?,?,?,?)",
                (mid, slug, title, src, cat, year, date_gmt),
            )
            total_seen += 1
        conn.commit()
        if len(items) < 100:
            break
        page += 1
    return total_seen


def download_one(row: tuple, out_dir: Path) -> tuple[int, bool, int]:
    pid, url, category, year = row
    fname = url.rsplit("/", 1)[-1]
    subdir = out_dir / category / (str(year) if year else "sin-anio")
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / fname
    if dest.exists() and dest.stat().st_size > 1024:
        with _LOCK:
            _STATS["pdfs_skip"] += 1
        return (pid, True, dest.stat().st_size)
    try:
        body = http_get(url, timeout=120)
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
    ap.add_argument("--categories", default="boletines",
                    help="csv: boletines,estado-diario,otros (default: solo boletines)")
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== TCP bulk ===", flush=True)
    print(f"output: {out}  workers: {args.workers}  cats: {args.categories}",
          flush=True)

    # Fase 1
    print("Fase 1: enumerando WP media...", flush=True)
    t0 = time.time()
    n = enumerate_media(conn, max_pages=args.max_pages)
    print(f"  enumerados nuevos: {n}  ({time.time()-t0:.1f}s)", flush=True)
    counts = conn.execute("SELECT category, COUNT(*) FROM pdfs GROUP BY category").fetchall()
    for c, k in counts:
        print(f"  {c}: {k}", flush=True)

    if args.list_only:
        print("(list-only: no descargo)", flush=True)
        return 0

    cats = set(args.categories.split(","))
    rows = conn.execute(
        "SELECT id, url, category, year FROM pdfs "
        "WHERE downloaded=0 AND category IN (" + ",".join("?"*len(cats)) + ")",
        list(cats)
    ).fetchall()
    print(f"\nFase 2: descargando {len(rows)} PDFs ({sorted(cats)})", flush=True)

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
                if done % 20 == 0:
                    conn.commit()
                    with _LOCK:
                        s = dict(_STATS)
                    print(f"  done={done}/{len(rows)} ok={s['pdfs_ok']} "
                          f"skip={s['pdfs_skip']} err={s['pdfs_err']} "
                          f"MB={s['bytes']/1e6:.1f}", flush=True)
    conn.commit()
    print(f"\n[DONE] {time.time()-t0:.0f}s | {dict(_STATS)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
