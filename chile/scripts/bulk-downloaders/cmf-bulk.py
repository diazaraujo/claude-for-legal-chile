#!/usr/bin/env python3
"""Bulk CMF: NCG + Circulares — enumerate por tipo×año×número con HEAD verify."""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "chile/scripts/mcp-cmf/src"))
from mcp_cmf.cmf_client import CMFClient

USER_AGENT = "claude-legal-chile/0.7 bulk-cmf"
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS normas ("
        "tipo TEXT, numero INTEGER, year INTEGER, "
        "exists_flag INTEGER, downloaded INTEGER DEFAULT 0, "
        "PRIMARY KEY(tipo, numero, year))"
    )
    conn.commit()
    return conn


def check_download(tipo: str, numero: int, year: int, output_dir: Path,
                   db_path: Path, skip_pdfs: bool) -> tuple[str, str]:
    client = CMFClient(rate_seconds=0.2)
    url = client.build_url(tipo, numero, year)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if "pdf" not in r.headers.get("Content-Type", "").lower():
                with _LOCK: _STATS["404"] += 1
                return f"{tipo}_{numero}_{year}", "no-pdf"
    except urllib.error.HTTPError:
        with _LOCK: _STATS["404"] += 1
        return f"{tipo}_{numero}_{year}", "404"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return f"{tipo}_{numero}_{year}", "head-err"

    c = sqlite3.connect(str(db_path), timeout=30)
    try:
        c.execute(
            "INSERT OR REPLACE INTO normas(tipo, numero, year, exists_flag, downloaded) "
            "VALUES (?, ?, ?, 1, COALESCE((SELECT downloaded FROM normas WHERE tipo=? AND numero=? AND year=?), 0))",
            (tipo, numero, year, tipo, numero, year),
        )
        c.commit()
    finally:
        c.close()

    if skip_pdfs:
        return f"{tipo}_{numero}_{year}", "head-ok"

    dest = output_dir / tipo / str(year) / f"{tipo}_{numero}.pdf"
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return f"{tipo}_{numero}_{year}", "skip"
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
        c = sqlite3.connect(str(db_path), timeout=30)
        try:
            c.execute("UPDATE normas SET downloaded = 1 WHERE tipo=? AND numero=? AND year=?",
                      (tipo, numero, year))
            c.commit()
        finally:
            c.close()
        return f"{tipo}_{numero}_{year}", "ok"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return f"{tipo}_{numero}_{year}", "get-err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", choices=["ncg", "cir", "both"], default="both")
    parser.add_argument("--from-year", type=int, default=1990)
    parser.add_argument("--to-year", type=int, default=2025)
    parser.add_argument("--ncg-max", type=int, default=600)
    parser.add_argument("--cir-max", type=int, default=2400)
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/cmf"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    init_manifest(db_path).close()

    tipos = ["ncg", "cir"] if args.tipo == "both" else [args.tipo]
    candidatos = []
    for tipo in tipos:
        max_n = args.ncg_max if tipo == "ncg" else args.cir_max
        for year in range(args.to_year, args.from_year - 1, -1):
            for n in range(1, max_n + 1):
                candidatos.append((tipo, n, year))

    c = sqlite3.connect(str(db_path), timeout=30)
    existing = {(row[0], row[1], row[2])
                for row in c.execute("SELECT tipo, numero, year FROM normas WHERE exists_flag IS NOT NULL")}
    c.close()
    pending = [(t, n, y) for t, n, y in candidatos if (t, n, y) not in existing]
    print(f"[INFO] Candidatos: {len(candidatos):,} | Verificados: {len(existing):,} | Pendientes: {len(pending):,}")
    if not pending:
        return 0

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(check_download, t, n, y, output_dir, db_path, args.skip_pdfs)
                   for t, n, y in pending]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
            except Exception:
                pass
            if i % 1000 == 0 or i == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i) / rate if rate > 0 else 0
                print(f"[{i:,}/{len(pending):,}] ok={_STATS['ok']:,} 404={_STATS['404']:,} "
                      f"err={_STATS['err']:,} | {mb:.0f} MB | elapsed={elapsed:.0f}s eta={eta:.0f}s",
                      flush=True)

    print(f"\n[DONE] {time.time()-start:.0f}s | {_STATS['ok']} PDFs, {_STATS['bytes']/1024/1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
