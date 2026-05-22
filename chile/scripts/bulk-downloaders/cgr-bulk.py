#!/usr/bin/env python3
"""Bulk CGR dictámenes — enumerate por año + verify + download.

CGR no expone listado. Estrategia: HEAD a cada (numero, year) en rango.
Para 2010-2025 × 1-100k = millones de HEADs. Usar workers altos.

Más práctico: usar listados anuales si BCN los tiene, o limitar rango
real (~5000 dictámenes/año máx).
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-cgr-dictamenes/src"))
from mcp_cgr_dictamenes.cgr_client import CGRClient

USER_AGENT = "claude-legal-chile/0.7 bulk-cgr"
_STATS = {"ok": 0, "skip": 0, "err": 0, "404": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dictamenes ("
        "dictamen_id TEXT PRIMARY KEY, year INTEGER, numero INTEGER, "
        "exists_flag INTEGER, downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def check_and_maybe_download(
    year: int, numero: int, output_dir: Path, db_path: Path,
    skip_pdfs: bool,
) -> tuple[str, str]:
    """HEAD + (opcional) GET. Devuelve (dictamen_id, status)."""
    client = CGRClient(rate_seconds=0.2)
    urls = client.build_urls(numero, year)
    # HEAD
    req = urllib.request.Request(
        urls.pdf_url, headers={"User-Agent": USER_AGENT}, method="HEAD"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if "pdf" not in r.headers.get("Content-Type", "").lower():
                with _LOCK: _STATS["404"] += 1
                return urls.dictamen_id, "no-pdf"
    except urllib.error.HTTPError:
        with _LOCK: _STATS["404"] += 1
        return urls.dictamen_id, "404"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return urls.dictamen_id, "head-err"

    # Existe — marcar y opcionalmente descargar
    c = sqlite3.connect(str(db_path), timeout=30)
    try:
        c.execute(
            "INSERT OR REPLACE INTO dictamenes(dictamen_id, year, numero, exists_flag, downloaded) "
            "VALUES (?, ?, ?, 1, COALESCE((SELECT downloaded FROM dictamenes WHERE dictamen_id=?), 0))",
            (urls.dictamen_id, year, numero, urls.dictamen_id),
        )
        c.commit()
    finally:
        c.close()

    if skip_pdfs:
        return urls.dictamen_id, "head-ok"

    # GET
    dest = output_dir / str(year) / f"{urls.dictamen_id}.pdf"
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return urls.dictamen_id, "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(urls.pdf_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _LOCK:
            _STATS["ok"] += 1
            _STATS["bytes"] += len(body)
        c = sqlite3.connect(str(db_path), timeout=30)
        try:
            c.execute("UPDATE dictamenes SET downloaded = 1 WHERE dictamen_id = ?", (urls.dictamen_id,))
            c.commit()
        finally:
            c.close()
        return urls.dictamen_id, "ok"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return urls.dictamen_id, "get-err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-year", type=int, default=2024)
    parser.add_argument("--to-year", type=int, default=2025)
    parser.add_argument("--max-numero", type=int, default=80000)
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/cgr"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    init_manifest(db_path).close()

    print(f"[INFO] CGR Bulk — años {args.from_year}..{args.to_year}, "
          f"máx número {args.max_numero}")
    print(f"[INFO] Workers: {args.workers}")
    print(f"[INFO] skip-pdfs: {args.skip_pdfs}\n")

    # Generar candidatos reverse (años más recientes primero)
    candidatos = []
    for year in range(args.to_year, args.from_year - 1, -1):
        for n in range(1, args.max_numero + 1):
            candidatos.append((year, n))

    # Filtrar candidatos ya verificados
    c = sqlite3.connect(str(db_path), timeout=30)
    existing = set()
    for row in c.execute("SELECT year, numero FROM dictamenes WHERE exists_flag IS NOT NULL"):
        existing.add((row[0], row[1]))
    c.close()
    pending = [(y, n) for y, n in candidatos if (y, n) not in existing]
    print(f"[INFO] Total candidatos: {len(candidatos):,}")
    print(f"[INFO] Ya verificados: {len(existing):,}")
    print(f"[INFO] Pendientes: {len(pending):,}\n")

    if not pending:
        return 0

    start = time.time()

    def worker(yn):
        y, n = yn
        return check_and_maybe_download(y, n, output_dir, db_path, args.skip_pdfs)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, yn) for yn in pending]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
            except Exception:
                pass
            if i % 500 == 0 or i == len(pending):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i) / rate if rate > 0 else 0
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"[{i:,}/{len(pending):,}] ok={_STATS['ok']:,} "
                    f"404={_STATS['404']:,} err={_STATS['err']:,} | "
                    f"{mb:.0f} MB | elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )

    print(f"\n[DONE] {time.time()-start:.0f}s")
    print(f"  PDFs ok: {_STATS['ok']}, 404: {_STATS['404']}, err: {_STATS['err']}")
    print(f"  Total: {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
