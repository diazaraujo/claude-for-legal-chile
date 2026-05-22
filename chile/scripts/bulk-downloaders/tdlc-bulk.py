#!/usr/bin/env python3
# std:input -
# std:output PDFs sentencias TDLC + manifest
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download TDLC sentencias en 2 fases.

Fase 1 (--skip-pdfs): enumera 213 sentencias via WP REST API.
Fase 2: descarga PDFs anexos de cada sentencia (extraídos del content
HTML de cada post).

Aplica feedback Antonio "toda la data, no muestras" + "bulk 2 fases".
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-tdlc/src"))
from mcp_tdlc.tdlc_client import TDLCClient, SentenciaTDLC

USER_AGENT = "claude-legal-chile/0.7 bulk-tdlc"

_STATS = {"pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}
_STATS_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias ("
        "id INTEGER PRIMARY KEY, slug TEXT, title TEXT, link TEXT, "
        "date TEXT, pdf_urls TEXT, downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        with _STATS_LOCK:
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
        with _STATS_LOCK:
            _STATS["pdfs_ok"] += 1
            _STATS["bytes"] += len(body)
        return True
    except Exception:
        with _STATS_LOCK:
            _STATS["pdfs_err"] += 1
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/tdlc"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-pdfs", action="store_true")
    parser.add_argument("--forward", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)
    lock = Lock()

    # FASE 1: enumerate metadata
    print("[FASE 1] Enumerando sentencias TDLC vía REST API...")
    client = TDLCClient(rate_seconds=0.3)
    sentencias = client.list_all_sentencias()
    print(f"  Total: {len(sentencias)}\n")

    with lock:
        for s in sentencias:
            conn.execute(
                "INSERT OR REPLACE INTO sentencias(id, slug, title, link, date, pdf_urls, downloaded) "
                "VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT downloaded FROM sentencias WHERE id=?), 0))",
                (s.id, s.slug, s.title, s.link, s.date, json.dumps(s.pdf_urls), s.id),
            )
        conn.commit()

    if args.skip_pdfs:
        print("[FASE 1 DONE] Metadata guardada en manifest.")
        return 0

    # FASE 2: scrape page de cada sentencia para PDFs + descargar
    print(f"[FASE 2] Scrape page + download PDFs...")
    order = "ASC" if args.forward else "DESC"
    rows = conn.execute(
        f"SELECT id, slug, link FROM sentencias WHERE downloaded = 0 ORDER BY id {order}"
    ).fetchall()
    print(f"  Pendientes: {len(rows)}\n")

    if not rows:
        return 0

    PDF_RE = re.compile(r'href="([^"]+\.pdf)"')

    def worker(row: tuple) -> tuple[int, str, int]:
        sid, slug, link = row
        # Fetch HTML del post para extraer PDFs
        req = urllib.request.Request(link, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", errors="replace")
        except Exception:
            return sid, "fetch-error", 0

        pdfs = list(set(PDF_RE.findall(body)))
        # Filtrar PDFs externos (mantener solo wp-content/uploads del propio TDLC)
        pdfs = [p for p in pdfs if "wp-content" in p or "tdlc.cl" in p]

        downloaded = 0
        for url in pdfs:
            if not url.startswith("http"):
                url = "https://www.tdlc.cl" + url
            fname = url.rsplit("/", 1)[-1]
            dest = output_dir / slug / fname
            if download_pdf(url, dest):
                downloaded += 1

        # Marcar como descargado solo si hubo al menos algo
        if downloaded > 0:
            local_conn = sqlite3.connect(str(db_path), timeout=30)
            try:
                local_conn.execute(
                    "UPDATE sentencias SET downloaded = ? WHERE id = ?",
                    (downloaded, sid),
                )
                local_conn.commit()
            finally:
                local_conn.close()

        return sid, f"{downloaded}/{len(pdfs)} pdfs", downloaded

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(worker, r): r for r in rows}
        for i, fut in enumerate(as_completed(futures), 1):
            sid, status, n = fut.result()
            if i % 10 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                print(
                    f"  [{i}/{len(rows)}] id={sid}: {status} | "
                    f"PDFs ok={_STATS['pdfs_ok']} skip={_STATS['pdfs_skip']} "
                    f"err={_STATS['pdfs_err']} | {mb:.0f} MB | "
                    f"elapsed={elapsed:.0f}s",
                    flush=True,
                )

    print(f"\n[FASE 2 DONE] {time.time()-start:.0f}s")
    print(f"  PDFs ok: {_STATS['pdfs_ok']}, skip: {_STATS['pdfs_skip']}, err: {_STATS['pdfs_err']}")
    print(f"  Total: {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
