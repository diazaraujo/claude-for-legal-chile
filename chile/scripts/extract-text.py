#!/usr/bin/env python3
"""Extrae texto de todos los PDFs descargados en chile/data/**/*.pdf
usando `pdftotext` (poppler-utils). Output: .pdf.txt al lado.

Idempotente: skip si el .txt existe y es no-vacío.
"""
from __future__ import annotations
import argparse, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = _REPO_ROOT / "chile/data"
_STATS = {"ok": 0, "skip": 0, "err": 0, "empty": 0, "bytes_out": 0}
_LOCK = Lock()


def find_pdfs(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.pdf") if p.is_file()]


def extract_one(pdf: Path, force: bool = False) -> str:
    txt = pdf.with_suffix(".pdf.txt")
    if not force and txt.exists() and txt.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    try:
        # -layout preserva mejor estructura. -nopgbrk omite ^L entre páginas.
        result = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", str(pdf), str(txt)],
            capture_output=True, timeout=120, check=False,
        )
        if result.returncode != 0:
            with _LOCK: _STATS["err"] += 1
            return "err"
        if not txt.exists() or txt.stat().st_size == 0:
            with _LOCK: _STATS["empty"] += 1
            # crear placeholder vacío para no reintentar
            txt.touch()
            return "empty"
        with _LOCK:
            _STATS["ok"] += 1
            _STATS["bytes_out"] += txt.stat().st_size
        return "ok"
    except subprocess.TimeoutExpired:
        with _LOCK: _STATS["err"] += 1
        return "timeout"
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DATA_ROOT))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--filter", default="",
                        help="Solo PDFs cuyo path contenga este string")
    args = parser.parse_args()

    root = Path(args.root)
    pdfs = find_pdfs(root)
    if args.filter:
        pdfs = [p for p in pdfs if args.filter in str(p)]
    print(f"PDFs encontrados: {len(pdfs)}", flush=True)

    if not pdfs:
        return 0

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(extract_one, p, args.force) for p in pdfs]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 500 == 0 or i == len(pdfs):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pdfs) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(pdfs)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"empty={_STATS['empty']} err={_STATS['err']} | "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s rate={rate:.1f}/s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} skip={_STATS['skip']} "
        f"empty={_STATS['empty']} err={_STATS['err']} | "
        f"texto extraído: {_STATS['bytes_out']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
