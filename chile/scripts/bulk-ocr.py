#!/usr/bin/env python3
"""OCR sobre PDFs solo-imagen (.pdf.txt vacío) usando tesseract + pdftocairo.

Pipeline por PDF:
  1. pdftocairo -png -r 200 → N páginas en tmp/
  2. tesseract -l spa por página → texto
  3. Concatenar pages → {pdf}.pdf.txt
  4. Cleanup PNGs

Idempotente: skip si .pdf.txt ya tiene >50 chars (no fue empty).
Multiproceso real (no thread) — tesseract es CPU-bound.
"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = _REPO_ROOT / "chile/data"
TMP_ROOT = _REPO_ROOT / "chile/tmp/ocr"


def find_pdfs_needing_ocr(root: Path) -> list[Path]:
    """PDFs cuyo .pdf.txt está vacío (size=0) — pdftotext no extrajo nada."""
    results: list[Path] = []
    for txt in root.rglob("*.pdf.txt"):
        try:
            if txt.stat().st_size == 0:
                pdf = txt.with_suffix("")  # remove .txt to get .pdf
                if pdf.exists():
                    results.append(pdf)
        except OSError:
            pass
    return results


def ocr_one_pdf(pdf_str: str, tmp_root_str: str) -> tuple[str, str, int]:
    """Returns (pdf_path, status, n_chars_extracted)."""
    pdf = Path(pdf_str)
    out_txt = pdf.with_suffix(".pdf.txt")
    tmp_root = Path(tmp_root_str)

    if out_txt.exists() and out_txt.stat().st_size > 50:
        return (pdf_str, "skip", out_txt.stat().st_size)

    work = tmp_root / f"{os.getpid()}_{pdf.stem[:40]}_{int(time.time()*1000)}"
    work.mkdir(parents=True, exist_ok=True)

    try:
        # PDF → PNGs
        proc = subprocess.run(
            ["pdftocairo", "-png", "-r", "200", str(pdf),
             str(work / "page")],
            capture_output=True, timeout=300, check=False,
        )
        if proc.returncode != 0:
            return (pdf_str, "pdftocairo_err", 0)

        pngs = sorted(work.glob("page-*.png"))
        if not pngs:
            return (pdf_str, "no_pages", 0)

        # OCR each page
        all_text: list[str] = []
        for png in pngs:
            base = png.with_suffix("")
            proc = subprocess.run(
                ["tesseract", "-l", "spa", str(png), str(base)],
                capture_output=True, timeout=120, check=False,
            )
            txt_file = base.with_suffix(".txt")
            if txt_file.exists():
                try:
                    all_text.append(txt_file.read_text(
                        encoding="utf-8", errors="replace"
                    ))
                except Exception:
                    pass

        if not all_text:
            return (pdf_str, "no_text", 0)

        merged = "\n\n".join(all_text).strip()
        if len(merged) < 50:
            return (pdf_str, "too_short", len(merged))

        # Write atomic
        tmp_out = out_txt.with_suffix(".tmp")
        tmp_out.write_text(merged, encoding="utf-8")
        tmp_out.rename(out_txt)
        return (pdf_str, "ok", len(merged))

    except subprocess.TimeoutExpired:
        return (pdf_str, "timeout", 0)
    except Exception as e:
        return (pdf_str, f"err:{type(e).__name__}", 0)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--filter", default="",
                        help="Solo PDFs cuyo path contenga este string")
    parser.add_argument("--max", type=int, default=0,
                        help="Limit total PDFs (0 = unlimited)")
    parser.add_argument("--tmp", default=str(TMP_ROOT))
    args = parser.parse_args()

    tmp_root = Path(args.tmp)
    tmp_root.mkdir(parents=True, exist_ok=True)

    root = Path(args.root)
    pdfs = find_pdfs_needing_ocr(root)
    if args.filter:
        pdfs = [p for p in pdfs if args.filter in str(p)]
    if args.max > 0:
        pdfs = pdfs[:args.max]
    print(f"PDFs necesitando OCR: {len(pdfs)}", flush=True)
    if not pdfs:
        return 0

    start = time.time()
    stats = {"ok": 0, "skip": 0, "err": 0, "chars": 0}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(ocr_one_pdf, str(p), str(tmp_root)) for p in pdfs]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                _, status, nchars = fut.result()
            except Exception:
                status, nchars = "err", 0
            if status == "ok":
                stats["ok"] += 1
                stats["chars"] += nchars
            elif status == "skip":
                stats["skip"] += 1
            else:
                stats["err"] += 1
            if i % 20 == 0 or i == len(pdfs):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pdfs) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(pdfs)}] ok={stats['ok']} skip={stats['skip']} "
                    f"err={stats['err']} | "
                    f"chars={stats['chars']/1000:.0f}K | "
                    f"elapsed={elapsed:.0f}s rate={rate:.1f}/s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | ok={stats['ok']} skip={stats['skip']} "
        f"err={stats['err']} | {stats['chars']/1024/1024:.1f} MB texto"
    )
    # Cleanup tmp dir
    shutil.rmtree(tmp_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
