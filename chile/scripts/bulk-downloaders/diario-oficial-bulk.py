#!/usr/bin/env python3
# std:input rango de fechas (DD-MM-YYYY) + output dir
# std:output PDFs en {output}/YYYY/MM/DD/edicion_NNNNN/{sumario,cve}.pdf + manifest SQLite
# std:deps stdlib pura + ThreadPoolExecutor
"""
Descarga BULK de TODAS las publicaciones del Diario Oficial chileno.

Aplica principio "toda la data, no muestras" (feedback Antonio
2026-05-22): enumera día por día desde el inicio de la edición
electrónica (17-08-2016) hasta hoy, y descarga cada PDF.

Estructura de salida:
  {output}/YYYY/MM/DD/edicion_NNNNN/
    sumario.pdf               # PDF tabla contenidos
    {cve_id}.pdf              # cada publicación individual
    publicaciones.jsonl       # metadata estructurada de la edición

Manifest SQLite global:
  {output}/manifest.sqlite3
    descargas(date, edition, total_pubs, downloaded, status, error)

Modo idempotente:
- Skip ediciones ya descargadas (manifest).
- Skip PDFs ya en disco.
- Resume automáticamente si se interrumpe.

Paralelismo:
- ThreadPoolExecutor workers=8 (escalable a 32 si BCN no tira 429).
- Rate limit por worker.

Uso:
  python3 diario-oficial-bulk.py [--from DD-MM-YYYY] [--to DD-MM-YYYY]
                                  [--output DIR] [--workers N]
                                  [--dry-run] [--skip-pdfs]

Estimación:
- ~250 días hábiles/año × 9 años (2016-2025) ≈ 2250 ediciones
- ~25 publicaciones/edición ≈ 56.000 PDFs
- ~200KB/PDF ≈ 11 GB total
- A 8 PDFs/s ≈ 2 horas
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

# Reusar do_client del MCP
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-diario-oficial/src"))
from mcp_diario_oficial.do_client import DiarioOficialClient, Publicacion

USER_AGENT = "claude-legal-chile/0.7 (unholster.com) bulk-do"
DEFAULT_FROM = "17-08-2016"  # Inicio edición electrónica DO


# ---- manifest ----

def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    # WAL para concurrent writes seguros
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS descargas ("
        "date TEXT PRIMARY KEY, edition TEXT, total_pubs INTEGER, "
        "downloaded INTEGER, status TEXT, error TEXT, "
        "ts INTEGER)"
    )
    conn.commit()
    return conn


def manifest_get(conn: sqlite3.Connection, date: str) -> dict | None:
    row = conn.execute(
        "SELECT date, edition, total_pubs, downloaded, status, error FROM descargas "
        "WHERE date = ?", (date,)
    ).fetchone()
    if not row:
        return None
    return {
        "date": row[0], "edition": row[1], "total_pubs": row[2],
        "downloaded": row[3], "status": row[4], "error": row[5],
    }


def manifest_upsert(
    conn: sqlite3.Connection, date: str, edition: str,
    total_pubs: int, downloaded: int, status: str, error: str = "",
    lock: Lock | None = None,
) -> None:
    if lock:
        lock.acquire()
    try:
        conn.execute(
            "INSERT INTO descargas(date, edition, total_pubs, downloaded, status, error, ts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(date) DO UPDATE SET edition=excluded.edition, "
            "total_pubs=excluded.total_pubs, downloaded=excluded.downloaded, "
            "status=excluded.status, error=excluded.error, ts=excluded.ts",
            (date, edition, total_pubs, downloaded, status, error, int(time.time())),
        )
        conn.commit()
    finally:
        if lock:
            lock.release()


# ---- descarga PDF ----

_DOWNLOAD_LOCK = Lock()
_STATS = {"pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}


def download_pdf(url: str, dest: Path, timeout: int = 60) -> bool:
    """Descarga PDF a dest (skip si ya existe). Retorna True si OK."""
    if dest.exists() and dest.stat().st_size > 0:
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_skip"] += 1
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
        # Write atomically
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_ok"] += 1
            _STATS["bytes"] += len(body)
        return True
    except Exception as e:
        with _DOWNLOAD_LOCK:
            _STATS["pdfs_err"] += 1
        return False


# ---- procesar edición ----

def process_edition(
    date: str,
    edition: str,
    publicaciones: list[Publicacion],
    output_dir: Path,
    do_client: DiarioOficialClient,
    conn: sqlite3.Connection,
    manifest_lock: Lock,
    skip_pdfs: bool = False,
) -> None:
    """Descarga sumario + cada publicación de una edición."""
    day, month, year = date.split("-")
    edition_dir = output_dir / year / month / day / f"edicion_{edition}"
    edition_dir.mkdir(parents=True, exist_ok=True)

    # Guardar manifest jsonl de la edición
    manifest_file = edition_dir / "publicaciones.jsonl"
    with manifest_file.open("w", encoding="utf-8") as fh:
        for p in publicaciones:
            fh.write(json.dumps({
                "cve": p.cve, "title": p.title,
                "pdf_url": p.pdf_url,
            }, ensure_ascii=False) + "\n")

    downloaded = 0
    if not skip_pdfs:
        # Sumario
        sumario_url = do_client.get_sumario_pdf_url(date, edition)
        sumario_dest = edition_dir / "sumario.pdf"
        if download_pdf(sumario_url, sumario_dest):
            downloaded += 1

        # Publicaciones
        for p in publicaciones:
            dest = edition_dir / f"{p.cve}.pdf"
            if download_pdf(p.pdf_url, dest):
                downloaded += 1

    status = "ok" if (skip_pdfs or downloaded > 0) else "no-pdfs"
    manifest_upsert(
        conn, date, edition, len(publicaciones), downloaded, status,
        lock=manifest_lock,
    )


def fetch_and_process(
    date: str,
    output_dir: Path,
    do_client: DiarioOficialClient,
    conn: sqlite3.Connection,
    manifest_lock: Lock,
    skip_pdfs: bool = False,
) -> tuple[str, str]:
    """Fetch + procesa una edición. Devuelve (date, status_msg)."""
    existing = manifest_get(conn, date)
    if existing and existing["status"] == "ok":
        # Skip solo si:
        # - skip_pdfs (no necesitamos descargar): manifest ok es suficiente
        # - O downloaded ya >= total_pubs (todos los PDFs en disco)
        if skip_pdfs:
            return date, "skip-manifest"
        if (existing.get("downloaded") or 0) >= (existing.get("total_pubs") or 0) + 1:
            # +1 por el sumario
            return date, "skip-manifest"
        # Si manifest ok pero downloaded < total_pubs, reprocesar para
        # descargar los PDFs faltantes.
    try:
        d, edition, pubs = do_client.fetch_by_date(date)
        if not edition:
            manifest_upsert(
                conn, date, "", 0, 0, "no-edition",
                lock=manifest_lock,
            )
            return date, "no-edition"
        process_edition(
            d, edition, pubs, output_dir, do_client, conn, manifest_lock,
            skip_pdfs=skip_pdfs,
        )
        return date, f"ok ({len(pubs)} pubs)"
    except Exception as e:
        manifest_upsert(
            conn, date, "", 0, 0, "error", error=str(e),
            lock=manifest_lock,
        )
        return date, f"err: {type(e).__name__}"


# ---- main ----

def iter_business_days(
    from_date: datetime.date, to_date: datetime.date
) -> list[str]:
    """Genera lista de fechas DD-MM-YYYY hábiles (L-V) en rango."""
    dates = []
    current = from_date
    while current <= to_date:
        if current.weekday() < 5:
            dates.append(current.strftime("%d-%m-%Y"))
        current += datetime.timedelta(days=1)
    return dates


def parse_date(s: str) -> datetime.date:
    d, m, y = s.split("-")
    return datetime.date(int(y), int(m), int(d))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk download Diario Oficial")
    parser.add_argument("--from", dest="from_date", default=DEFAULT_FROM,
                        help="Fecha inicio DD-MM-YYYY (default: 17-08-2016)")
    parser.add_argument("--to", dest="to_date",
                        default=datetime.date.today().strftime("%d-%m-%Y"),
                        help="Fecha fin DD-MM-YYYY (default: hoy)")
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/diario-oficial"),
                        help="Directorio salida")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rate-seconds", type=float, default=1.0,
                        help="Rate limit por worker (segundos entre requests)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo listar fechas, no descargar")
    parser.add_argument("--skip-pdfs", action="store_true",
                        help="Solo bajar metadata, no PDFs (Fase 1)")
    parser.add_argument("--forward", action="store_true",
                        help="Cronológico (from→to). Default es reverse (hoy→atrás)")
    args = parser.parse_args()

    from_d = parse_date(args.from_date)
    to_d = parse_date(args.to_date)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    dates = iter_business_days(from_d, to_d)
    # Reverse chronological: hoy → atrás (feedback Antonio 2026-05-22)
    if not args.forward:
        dates = list(reversed(dates))
    print(f"[INFO] Rango: {args.from_date} → {args.to_date}")
    print(f"[INFO] Orden: {'forward' if args.forward else 'reverse (hoy→atrás)'}")
    print(f"[INFO] Días hábiles: {len(dates)}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Workers: {args.workers}, rate: {args.rate_seconds}s")
    print(f"[INFO] skip-pdfs: {args.skip_pdfs}")

    if args.dry_run:
        print(f"\n[DRY-RUN] First 5: {dates[:5]}")
        print(f"[DRY-RUN] Last 5: {dates[-5:]}")
        return 0

    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)
    manifest_lock = Lock()

    # Skip ya completadas:
    # - Si skip-pdfs: status='ok' es suficiente
    # - Si Fase 2 (PDFs): solo skip las que tienen downloaded >= total+1 (incluido sumario)
    completed = set()
    if args.skip_pdfs:
        for row in conn.execute("SELECT date FROM descargas WHERE status='ok'"):
            completed.add(row[0])
    else:
        for row in conn.execute(
            "SELECT date FROM descargas WHERE status='ok' AND downloaded >= total_pubs + 1"
        ):
            completed.add(row[0])
        # También skip no-edition (no hay nada que descargar)
        for row in conn.execute("SELECT date FROM descargas WHERE status='no-edition'"):
            completed.add(row[0])
    pending = [d for d in dates if d not in completed]
    print(f"[INFO] Ya completadas (skip): {len(completed)}")
    print(f"[INFO] Pendientes: {len(pending)}")

    if not pending:
        print("[INFO] Nada que hacer.")
        return 0

    # Worker pool
    start_ts = time.time()

    def worker(date: str) -> tuple[str, str]:
        # Cliente + conn per-worker (SQLite no es safe en multithread
        # con conn compartida — terminamos con "database disk image is
        # malformed").
        client = DiarioOficialClient(rate_seconds=args.rate_seconds)
        local_conn = sqlite3.connect(str(db_path), timeout=30)
        local_conn.execute("PRAGMA busy_timeout=30000")
        try:
            return fetch_and_process(
                date, output_dir, client, local_conn, manifest_lock,
                skip_pdfs=args.skip_pdfs,
            )
        finally:
            local_conn.close()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(worker, d): d for d in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                date, status = fut.result()
            except Exception as e:
                date, status = "?", f"fatal: {e}"
            if i % 25 == 0 or i == len(pending):
                elapsed = time.time() - start_ts
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i) / rate if rate > 0 else 0
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"[{i}/{len(pending)}] {date}: {status} | "
                    f"PDFs ok={_STATS['pdfs_ok']} skip={_STATS['pdfs_skip']} "
                    f"err={_STATS['pdfs_err']} | {mb:.0f} MB | "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start_ts
    print(f"\n[DONE] {elapsed:.0f}s")
    print(f"  PDFs descargados:    {_STATS['pdfs_ok']:,}")
    print(f"  PDFs skipped:        {_STATS['pdfs_skip']:,}")
    print(f"  PDFs error:          {_STATS['pdfs_err']:,}")
    print(f"  Total bytes:         {_STATS['bytes']/1024/1024:.0f} MB")
    print(f"\n  Manifest: {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
