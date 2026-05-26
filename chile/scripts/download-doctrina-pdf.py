#!/usr/bin/env python3
"""Fase 2 doctrina: descargar PDF fulltext desde handle DSpace.

Lee los .md de chile/normativa/doctrina/{fuente}/, extrae URL handle,
parsea la página HTML para encontrar el bitstream PDF principal,
y descarga a chile/data/doctrina/{fuente}/{handle_slug}.pdf.

Idempotente: skip si archivo ya existe.
Workers paralelos (default 8).
Filtros: boilerplate UCh (/pdf/guia.pdf, /pdf/Formulario_*) excluido.
"""
from __future__ import annotations
import argparse, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTRINA_META = REPO_ROOT / "chile/normativa/doctrina"
DOCTRINA_PDF = REPO_ROOT / "chile/data/doctrina"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

# Patrones de boilerplate UCh DSpace a excluir
EXCLUDE_PATTERNS = [
    r"/pdf/guia\.pdf",
    r"/pdf/Formulario",
    r"/pdf/license",
]
EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)

# Regex href PDF
HREF_PDF_RE = re.compile(
    r'href=["\']([^"\']*\.pdf(?:\?[^"\']*)?)["\']', re.IGNORECASE
)

_STATS = {"ok": 0, "skip": 0, "noref": 0, "err": 0, "boiler": 0}
_LOCK = Lock()


def parse_md(path: Path) -> dict | None:
    """Extract handle URL + handle_slug from .md frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"urls:\s*\n((?:  - .+\n)+)", text)
    urls = []
    if m:
        for line in m.group(1).splitlines():
            u = line.strip().lstrip("- ").strip()
            if u.startswith("http"):
                urls.append(u)
    # handle slug = filename minus .md
    return {"handle_slug": path.stem, "urls": urls}


def find_pdf_link(html: str, base_url: str) -> str | None:
    """Find first non-boilerplate PDF href."""
    for m in HREF_PDF_RE.finditer(html):
        href = m.group(1)
        if EXCLUDE_RE.search(href):
            continue
        if href.startswith("/"):
            parsed = urllib.parse.urlparse(base_url)
            href = f"{parsed.scheme}://{parsed.netloc}{href}"
        elif not href.startswith("http"):
            continue
        return href
    return None


def download_pdf(meta: dict, fuente: str, max_retries: int = 3) -> str:
    handle_slug = meta["handle_slug"]
    out_dir = DOCTRINA_PDF / fuente
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{handle_slug}.pdf"
    if out_path.exists() and out_path.stat().st_size > 1024:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    if not meta.get("urls"):
        with _LOCK: _STATS["noref"] += 1
        return "noref"

    handle_url = meta["urls"][0]
    # 1. Fetch handle page
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                handle_url, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", errors="replace")
            break
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            if attempt == max_retries - 1:
                with _LOCK: _STATS["err"] += 1
                return f"err_handle:{type(e).__name__}"
            time.sleep(3 * (attempt + 1))
    else:
        with _LOCK: _STATS["err"] += 1
        return "err_handle_unknown"

    pdf_url = find_pdf_link(html, handle_url)
    if not pdf_url:
        with _LOCK: _STATS["boiler"] += 1
        return "no_pdf_found"

    # 2. Download PDF
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                pdf_url, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) < 1024:
                with _LOCK: _STATS["err"] += 1
                return "too_small"
            tmp = out_path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.rename(out_path)
            with _LOCK: _STATS["ok"] += 1
            return "ok"
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            if attempt == max_retries - 1:
                with _LOCK: _STATS["err"] += 1
                return f"err_pdf:{type(e).__name__}"
            time.sleep(3 * (attempt + 1))
    with _LOCK: _STATS["err"] += 1
    return "err_pdf_unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente", default="uch")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    meta_dir = DOCTRINA_META / args.fuente
    md_files = list(meta_dir.glob("*.md"))
    if args.max > 0:
        md_files = md_files[:args.max]
    print(f"Doctrina PDF downloader — fuente={args.fuente}", flush=True)
    print(f"Metadatos: {len(md_files)} | workers={args.workers}", flush=True)

    metas: list[dict] = []
    for f in md_files:
        m = parse_md(f)
        if m and m.get("urls"):
            metas.append(m)
    print(f"Con URL handle: {len(metas)}", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download_pdf, m, args.fuente) for m in metas]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 100 == 0 or i == len(metas):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(metas) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(metas)}] "
                    f"ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"noref={_STATS['noref']} boiler={_STATS['boiler']} "
                    f"err={_STATS['err']} | "
                    f"{rate:.1f}/s eta={eta/60:.0f}min",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
