#!/usr/bin/env python3
"""Bulk SERNAC: circulares + dictámenes interpretativos.

Listado HTML estático con article links. Fase 1 enumera, Fase 2 baja PDFs.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-sernac/src"))
from mcp_sernac.sernac_client import SERNACClient

USER_AGENT = "claude-legal-chile/0.7 bulk-sernac"
_STATS = {"ok": 0, "skip": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS docs ("
        "article_id INTEGER PRIMARY KEY, tipo TEXT, title TEXT, "
        "html_url TEXT, pdf_url TEXT, downloaded INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
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
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/sernac"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)
    client = SERNACClient(rate_seconds=0.5)

    print("[FASE 1] Listando SERNAC...")
    all_docs = []
    for tipo in ["circulares", "dictamenes"]:
        docs = client.list_documentos(tipo)
        print(f"  {tipo}: {len(docs)}")
        for d in docs:
            conn.execute(
                "INSERT OR REPLACE INTO docs(article_id, tipo, title, html_url, pdf_url, downloaded) "
                "VALUES (?, ?, ?, ?, ?, COALESCE((SELECT downloaded FROM docs WHERE article_id=?), 0))",
                (d.article_id, tipo, d.title, d.html_url, d.pdf_url, d.article_id),
            )
            all_docs.append((d.article_id, tipo, d.pdf_url))
        conn.commit()

    if args.skip_pdfs:
        return 0

    print(f"\n[FASE 2] Descargando PDFs...")
    rows = conn.execute(
        "SELECT article_id, tipo, pdf_url FROM docs WHERE downloaded = 0 ORDER BY article_id DESC"
    ).fetchall()
    print(f"  Pendientes: {len(rows)}")

    def worker(row):
        aid, tipo, url = row
        dest = output_dir / tipo / f"{aid}.pdf"
        ok = download(url, dest)
        if ok:
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute("UPDATE docs SET downloaded = 1 WHERE article_id = ?", (aid,))
                c.commit()
            finally:
                c.close()
        return aid, ok

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, fut in enumerate(as_completed([pool.submit(worker, r) for r in rows]), 1):
            fut.result()
            if i % 20 == 0 or i == len(rows):
                mb = _STATS["bytes"] / 1024 / 1024
                print(f"  [{i}/{len(rows)}] ok={_STATS['ok']} skip={_STATS['skip']} err={_STATS['err']} | {mb:.0f} MB", flush=True)

    print(f"\n[DONE] {time.time()-start:.0f}s, {_STATS['ok']} PDFs, {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
