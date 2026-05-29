#!/usr/bin/env python3
"""OCR sobre PDFs Cortes Marciales (escaneados Xerox sin layer texto).

Pipeline: pdftoppm @200dpi → PNG por página → tesseract -l spa --psm 6 →
concat. Salida en data/cortes-marciales/_ocr/{tribunal}/{file_id}.txt.

Idempotente: skip si el .txt ya existe y >100 bytes.
"""
from __future__ import annotations
import argparse, os, subprocess, sys, tempfile, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = _REPO_ROOT / "chile/data/cortes-marciales"
OCR_ROOT = ROOT / "_ocr"


def ocr_one(pdf_path_str: str) -> tuple[str, str, int, float]:
    pdf = Path(pdf_path_str)
    rel = pdf.relative_to(ROOT)
    # _ocr/{tribunal}/{file_id}.txt
    out_path = OCR_ROOT / rel.with_suffix(".txt")
    if out_path.exists() and out_path.stat().st_size > 100:
        return (str(pdf), "skip", out_path.stat().st_size, 0.0)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="ocr-cm-") as td:
        td_p = Path(td)
        # pdftoppm @200dpi
        r = subprocess.run(
            ["pdftoppm", "-r", "200", str(pdf), str(td_p / "p"), "-png"],
            capture_output=True, timeout=300,
        )
        if r.returncode != 0:
            return (str(pdf), "pdftoppm-err", 0, time.time() - t0)
        pngs = sorted(td_p.glob("p-*.png"))
        if not pngs:
            return (str(pdf), "no-pages", 0, time.time() - t0)
        chunks = []
        for png in pngs:
            r = subprocess.run(
                ["tesseract", str(png), "-", "-l", "spa", "--psm", "6"],
                capture_output=True, text=True, timeout=180,
            )
            if r.returncode == 0:
                chunks.append(r.stdout)
        text = "\n".join(chunks).strip()
        if len(text) < 100:
            return (str(pdf), "empty-ocr", len(text), time.time() - t0)
        tmp = out_path.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.rename(out_path)
        return (str(pdf), "ok", len(text), time.time() - t0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(ROOT.rglob("*.pdf"))
    pdfs = [p for p in pdfs if "_ocr" not in p.parts]
    if args.limit:
        pdfs = pdfs[: args.limit]
    print(f"PDFs a OCR: {len(pdfs)} (workers={args.workers})", flush=True)

    stats = {"ok": 0, "skip": 0, "err": 0, "empty": 0, "bytes": 0, "secs": 0.0}
    t0 = time.time()
    last_print = t0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(ocr_one, str(p)): p for p in pdfs}
        done = 0
        for fut in as_completed(futs):
            _, status, size, secs = fut.result()
            stats["secs"] += secs
            if status == "ok":
                stats["ok"] += 1
                stats["bytes"] += size
            elif status == "skip":
                stats["skip"] += 1
            elif status in ("empty-ocr", "no-pages"):
                stats["empty"] += 1
            else:
                stats["err"] += 1
            done += 1
            if done % 10 == 0 or time.time() - last_print > 30:
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                eta = (len(pdfs) - done) / rate / 60 if rate > 0 else 0
                print(f"  done={done}/{len(pdfs)} ok={stats['ok']} skip={stats['skip']} "
                      f"err={stats['err']} empty={stats['empty']} MB={stats['bytes']/1e6:.1f} "
                      f"rate={rate:.2f}/s ETA={eta:.0f}min", flush=True)
                last_print = time.time()
    print(f"\n[DONE] {time.time()-t0:.0f}s wall | {dict(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
