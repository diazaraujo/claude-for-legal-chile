#!/usr/bin/env python3
# std:input rango años
# std:output PDFs de circulares SII + manifest SQLite
# std:deps stdlib pura + ThreadPoolExecutor
"""
Bulk download circulares SII Chile en 2 fases.

Fase 1 (--skip-pdfs): enumera índice por año, guarda metadata.
Fase 2: descarga PDFs reverse chronological (hoy → atrás).

Aplica feedback Antonio 2026-05-22 ("toda la data, no muestras" +
"bulk 2 fases reverse"). Reusa SIIJurisClient del MCP.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-sii-juris/src"))
from mcp_sii_juris.sii_client import SIIJurisClient, Circular

USER_AGENT = "claude-legal-chile/0.7 (unholster.com) bulk-sii"


_DOWNLOAD_LOCK = Lock()
_STATS = {"pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS circulares ("
        "year INTEGER, number INTEGER, title TEXT, summary TEXT, "
        "pdf_url TEXT, downloaded INTEGER DEFAULT 0, "
        "PRIMARY KEY(year, number))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS years_indexed ("
        "year INTEGER PRIMARY KEY, count INTEGER, ts INTEGER)"
    )
    conn.commit()
    return conn


def index_year(
    year: int, client: SIIJurisClient, conn: sqlite3.Connection,
    lock: Lock,
) -> int:
    """Indexa metadata de un año entero. Retorna count."""
    try:
        circs = client.list_circulares(year)
    except (urllib.error.HTTPError, urllib.error.URLError):
        with lock:
            conn.execute(
                "INSERT OR REPLACE INTO years_indexed VALUES (?, ?, ?)",
                (year, 0, int(time.time())),
            )
            conn.commit()
        return 0
    with lock:
        for c in circs:
            conn.execute(
                "INSERT OR REPLACE INTO circulares(year, number, title, summary, pdf_url, downloaded) "
                "VALUES (?, ?, ?, ?, ?, COALESCE((SELECT downloaded FROM circulares WHERE year=? AND number=?), 0))",
                (c.year, c.number, c.title, c.summary, c.pdf_url, c.year, c.number),
            )
        conn.execute(
            "INSERT OR REPLACE INTO years_indexed VALUES (?, ?, ?)",
            (year, len(circs), int(time.time())),
        )
        conn.commit()
    return len(circs)


def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_skip"] += 1
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_ok"] += 1
            _STATS["bytes"] += len(body)
        return True
    except Exception:
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_err"] += 1
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk download SII circulares")
    parser.add_argument("--since", type=int, default=1990)
    parser.add_argument("--until", type=int,
                        default=datetime.date.today().year)
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/sii"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rate-seconds", type=float, default=0.3)
    parser.add_argument("--skip-pdfs", action="store_true",
                        help="Fase 1: solo metadata, no PDFs")
    parser.add_argument("--forward", action="store_true",
                        help="Cronológico. Default reverse (hoy→atrás)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)
    manifest_lock = Lock()

    years = list(range(args.since, args.until + 1))
    if not args.forward:
        years = list(reversed(years))

    print(f"[INFO] SII Bulk — años {args.since}..{args.until}")
    print(f"[INFO] Orden: {'forward' if args.forward else 'reverse'}")
    print(f"[INFO] Workers: {args.workers}, rate: {args.rate_seconds}s")
    print(f"[INFO] skip-pdfs: {args.skip_pdfs}\n")

    # ---- Fase 1: Indexar metadata por año (siempre, idempotente) ----
    print("[FASE 1] Indexando metadata por año...")
    already = {row[0] for row in conn.execute("SELECT year FROM years_indexed")}
    pending_years = [y for y in years if y not in already]
    print(f"  Años ya indexados: {len(already)}")
    print(f"  Pendientes: {len(pending_years)}\n")

    start = time.time()
    total_indexed = sum(
        row[0] for row in conn.execute("SELECT count FROM years_indexed")
    )
    for y in pending_years:
        client = SIIJurisClient(rate_seconds=args.rate_seconds)
        n = index_year(y, client, conn, manifest_lock)
        total_indexed += n
        print(f"  {y}: {n} circulares (total {total_indexed})", flush=True)

    print(f"\n[FASE 1 DONE] {time.time()-start:.0f}s, {total_indexed} circulares totales")

    if args.skip_pdfs:
        return 0

    # ---- Fase 2: Download PDFs reverse ----
    print(f"\n[FASE 2] Descargando PDFs ({'reverse' if not args.forward else 'forward'})...")
    order = "DESC" if not args.forward else "ASC"
    rows = conn.execute(
        f"SELECT year, number, pdf_url FROM circulares "
        f"WHERE downloaded = 0 ORDER BY year {order}, number {order}"
    ).fetchall()
    print(f"  PDFs pendientes: {len(rows)}\n")

    if not rows:
        print("  Nada que descargar.")
        return 0

    def worker(row: tuple) -> tuple[int, int, bool]:
        year, number, pdf_url = row
        dest = output_dir / str(year) / f"circu{number}.pdf"
        ok = download_pdf(pdf_url, dest)
        if ok:
            with manifest_lock:
                conn.execute(
                    "UPDATE circulares SET downloaded = 1 "
                    "WHERE year = ? AND number = ?",
                    (year, number),
                )
                conn.commit()
        return year, number, ok

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(worker, r): r for r in rows}
        for i, fut in enumerate(as_completed(futures), 1):
            year, number, ok = fut.result()
            if i % 50 == 0 or i == len(rows):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(rows) - i) / rate if rate > 0 else 0
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(rows)}] {year}/circu{number} {ok} | "
                    f"ok={_STATS['pdfs_ok']} skip={_STATS['pdfs_skip']} "
                    f"err={_STATS['pdfs_err']} | {mb:.0f} MB | "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )

    print(f"\n[FASE 2 DONE] {time.time()-start:.0f}s")
    print(f"  PDFs descargados: {_STATS['pdfs_ok']}")
    print(f"  PDFs error:       {_STATS['pdfs_err']}")
    print(f"  Total:            {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
