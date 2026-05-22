#!/usr/bin/env python3
"""Bulk TC legacy: descarga sentencias TC con id 1..12000."""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-tc-fallos/src"))
from mcp_tc_fallos.tc_client import TCClient

USER_AGENT = "claude-legal-chile/0.7 bulk-tc"
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias ("
        "rol_id INTEGER PRIMARY KEY, exists_flag INTEGER, "
        "downloaded INTEGER DEFAULT 0, pdf_size INTEGER)"
    )
    conn.commit()
    return conn


def process_id(rol_id: int, output_dir: Path, db_path: Path,
               skip_pdfs: bool) -> tuple[int, str]:
    client = TCClient(rate_seconds=0.2)
    url = client.build_legacy_url(rol_id)
    # HEAD primero
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            ctype = r.headers.get("Content-Type", "")
            length = int(r.headers.get("Content-Length", "0") or "0")
            if "pdf" not in ctype.lower():
                with _LOCK: _STATS["404"] += 1
                return rol_id, "no-pdf"
    except urllib.error.HTTPError:
        with _LOCK: _STATS["404"] += 1
        return rol_id, "404"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return rol_id, "head-err"

    c = sqlite3.connect(str(db_path), timeout=30)
    try:
        c.execute(
            "INSERT OR REPLACE INTO sentencias(rol_id, exists_flag, downloaded, pdf_size) "
            "VALUES (?, 1, COALESCE((SELECT downloaded FROM sentencias WHERE rol_id=?), 0), ?)",
            (rol_id, rol_id, length),
        )
        c.commit()
    finally:
        c.close()

    if skip_pdfs:
        return rol_id, "head-ok"

    dest = output_dir / f"tc_{rol_id}.pdf"
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return rol_id, "skip"
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
        c = sqlite3.connect(str(db_path), timeout=30)
        try:
            c.execute("UPDATE sentencias SET downloaded = 1 WHERE rol_id = ?", (rol_id,))
            c.commit()
        finally:
            c.close()
        return rol_id, "ok"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return rol_id, "get-err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-id", type=int, default=1)
    parser.add_argument("--to-id", type=int, default=12000)
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/tc"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    init_manifest(db_path).close()

    c = sqlite3.connect(str(db_path), timeout=30)
    existing = {row[0] for row in c.execute("SELECT rol_id FROM sentencias WHERE exists_flag IS NOT NULL")}
    c.close()
    # Reverse: ID más reciente primero
    pending = [i for i in range(args.to_id, args.from_id - 1, -1) if i not in existing]
    print(f"[INFO] TC IDs {args.from_id}..{args.to_id} | Verificados: {len(existing)} | Pendientes: {len(pending)}")
    if not pending:
        return 0

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_id, i, output_dir, db_path, args.skip_pdfs)
                   for i in pending]
        for j, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
            except Exception:
                pass
            if j % 200 == 0 or j == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                rate = j / elapsed if elapsed > 0 else 0
                eta = (len(pending) - j) / rate if rate > 0 else 0
                print(f"[{j}/{len(pending)}] ok={_STATS['ok']} 404={_STATS['404']} err={_STATS['err']} | "
                      f"{mb:.0f} MB | elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

    print(f"\n[DONE] {time.time()-start:.0f}s | {_STATS['ok']} PDFs, {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
