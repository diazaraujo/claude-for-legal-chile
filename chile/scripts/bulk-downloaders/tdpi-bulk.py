#!/usr/bin/env python3
"""Bulk TDPI — Tribunal de Propiedad Industrial.

TDPI publica todos los fallos en una única página /fallos/, agrupados
por año. PDFs viven en wp-content/uploads/YYYY/MM/<archivo>.pdf
"""
from __future__ import annotations
import argparse, sqlite3, sys, time, urllib.request, urllib.error, urllib.parse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
INDEX_URL = "https://www.tdpi.cl/fallos/"
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fallos ("
        "url TEXT PRIMARY KEY, year INTEGER, "
        "downloaded INTEGER DEFAULT 0, pdf_size INTEGER)"
    )
    conn.commit()
    return conn


def discover_pdfs() -> list[tuple[str, int]]:
    """Devuelve [(url, year)] de todos los fallos en /fallos/.

    Estructura HTML: cada <h4>YYYY</h4> seguido de <p><a href="...pdf">.
    Asignamos el año al PDF según el último <h4> visto antes.
    """
    req = urllib.request.Request(INDEX_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", errors="replace")
    results: list[tuple[str, int]] = []
    current_year = 0
    # Scan in order: h4 sections + PDF links
    token_re = re.compile(
        r'<h4>(\d{4})</h4>|href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE,
    )
    seen: set[str] = set()
    for m in token_re.finditer(body):
        if m.group(1):
            current_year = int(m.group(1))
        elif m.group(2):
            u = m.group(2)
            if u in seen:
                continue
            seen.add(u)
            if u.startswith("//"):
                u = "https:" + u
            elif u.startswith("/"):
                u = "https://www.tdpi.cl" + u
            elif not u.startswith("http"):
                u = urllib.parse.urljoin(INDEX_URL, u)
            results.append((u, current_year))
    return results


def safe_filename(url: str) -> str:
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)


def download(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # URL-encode non-ASCII (URLs TDPI contienen N°, espacios, acentos).
    parts = urllib.parse.urlsplit(url)
    encoded_path = urllib.parse.quote(parts.path, safe="/%")
    encoded_url = urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment)
    )
    try:
        req = urllib.request.Request(
            encoded_url, headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.rename(dest)
        with _LOCK:
            _STATS["ok"] += 1
            _STATS["bytes"] += len(body)
        return "ok"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            with _LOCK: _STATS["404"] += 1
            return "404"
        with _LOCK: _STATS["err"] += 1
        return f"http{e.code}"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/tdpi"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    print("[FASE 1] Descubriendo fallos TDPI...", flush=True)
    fallos = discover_pdfs()
    print(f"  Descubiertos: {len(fallos)} PDFs", flush=True)
    by_year: dict[int, int] = {}
    for u, y in fallos:
        conn.execute(
            "INSERT OR IGNORE INTO fallos(url, year) VALUES (?, ?)",
            (u, y),
        )
        by_year[y] = by_year.get(y, 0) + 1
    conn.commit()
    for y in sorted(by_year, reverse=True):
        print(f"  {y}: {by_year[y]}", flush=True)

    pending = [
        (u, y) for u, y in fallos
        if conn.execute(
            "SELECT downloaded FROM fallos WHERE url=?", (u,)
        ).fetchone()[0] == 0
    ]
    print(f"\n[FASE 2] Descargando {len(pending)} PDFs...", flush=True)
    if not pending:
        return 0

    def worker(item):
        url, year = item
        dest = output_dir / str(year or "sin-anio") / safe_filename(url)
        status = download(url, dest)
        if status in ("ok", "skip"):
            c = sqlite3.connect(str(db_path), timeout=30)
            try:
                c.execute(
                    "UPDATE fallos SET downloaded=1 WHERE url=?", (url,)
                )
                c.commit()
            finally:
                c.close()
        return url, status

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, item) for item in pending]
        for i, fut in enumerate(as_completed(futures), 1):
            fut.result()
            if i % 25 == 0 or i == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                print(
                    f"  [{i}/{len(pending)}] ok={_STATS['ok']} "
                    f"404={_STATS['404']} err={_STATS['err']} | {mb:.0f} MB",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | {_STATS['ok']} PDFs, "
        f"{_STATS['bytes']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
