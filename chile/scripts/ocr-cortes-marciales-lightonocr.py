#!/usr/bin/env python3
# std:input PDFs escaneados en data/cortes-marciales/**.pdf
# std:output texto OCR en data/cortes-marciales/_ocr/{tribunal}/{file_id}.txt
# std:deps pypdfium2 + pillow + requests (stdlib resto) + vLLM sirviendo LightOnOCR
"""OCR de fallos Cortes Marciales con LightOnOCR-2-1B (VLM) vía vLLM.

Por qué este, no tesseract: los PDFs son escaneos Xerox degradados donde
tesseract -l spa da muchas páginas vacías. LightOnOCR-2-1B (modelo OCR VLM,
~1B) maneja escaneos degradados y layout complejo mucho mejor.

Infra: el modelo corre en **enigma (GPU)** vía vLLM (OpenAI-compatible):

    vllm serve lightonai/LightOnOCR-2-1B \
        --limit-mm-per-prompt '{"image": 1}' \
        --mm-processor-cache-gb 0 --no-enable-prefix-caching

Este cliente se corre en enigma (endpoint localhost:8000) o desde la laptop
apuntando al endpoint por SSH tunnel. Configurable con --endpoint / env
LIGHTONOCR_ENDPOINT.

Idempotente: skip si el .txt ya existe y >100 bytes (mismo layout que el
pipeline tesseract, así conviven y comparas calidad).
"""
from __future__ import annotations
import argparse, base64, io, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import pypdfium2 as pdfium

_REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = _REPO_ROOT / "chile/data/cortes-marciales"
OCR_ROOT = ROOT / "_ocr"

DEFAULT_ENDPOINT = os.environ.get(
    "LIGHTONOCR_ENDPOINT", "http://localhost:8000/v1/chat/completions"
)
MODEL = os.environ.get("LIGHTONOCR_MODEL", "lightonai/LightOnOCR-2-1B")
# 200 DPI ≈ scale 2.77 sobre 72dpi base; lado largo objetivo ~1540px.
RENDER_SCALE = 200 / 72
MAX_LONG_SIDE = 1540


def _page_to_b64_png(page) -> str:
    pil = page.render(scale=RENDER_SCALE).to_pil()
    # cap del lado largo preservando aspect ratio (recomendación del modelo)
    w, h = pil.size
    longest = max(w, h)
    if longest > MAX_LONG_SIDE:
        f = MAX_LONG_SIDE / longest
        pil = pil.resize((max(1, int(w * f)), max(1, int(h * f))))
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _ocr_image_b64(b64: str, endpoint: str, timeout: int) -> str:
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            }],
        }],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.9,
    }
    r = requests.post(endpoint, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ocr_one(pdf_path_str: str, endpoint: str, timeout: int) -> tuple[str, str, int, float]:
    pdf_path = Path(pdf_path_str)
    rel = pdf_path.relative_to(ROOT)
    out_path = OCR_ROOT / rel.with_suffix(".txt")
    if out_path.exists() and out_path.stat().st_size > 100:
        return (str(pdf_path), "skip", out_path.stat().st_size, 0.0)
    t0 = time.time()
    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
    except Exception:
        return (str(pdf_path), "pdf-open-err", 0, time.time() - t0)
    chunks: list[str] = []
    try:
        n = len(pdf)
        for i in range(n):
            try:
                b64 = _page_to_b64_png(pdf[i])
                chunks.append(_ocr_image_b64(b64, endpoint, timeout))
            except Exception:
                # una página que falla no aborta el documento
                continue
    finally:
        pdf.close()
    text = "\n\n".join(c.strip() for c in chunks if c and c.strip()).strip()
    if len(text) < 100:
        return (str(pdf_path), "empty-ocr", len(text), time.time() - t0)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.rename(out_path)
    return (str(pdf_path), "ok", len(text), time.time() - t0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                    help="vLLM OpenAI-compatible /v1/chat/completions")
    ap.add_argument("--workers", type=int, default=4,
                    help="requests concurrentes al servidor vLLM")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(ROOT.rglob("*.pdf"), key=lambda p: p.stat().st_size)
    pdfs = [p for p in pdfs if "_ocr" not in p.parts]
    if args.limit:
        pdfs = pdfs[: args.limit]
    print(f"PDFs a OCR: {len(pdfs)} | endpoint={args.endpoint} "
          f"workers={args.workers} model={MODEL}", flush=True)

    stats = {"ok": 0, "skip": 0, "err": 0, "empty": 0, "bytes": 0}
    t0 = time.time()
    last = t0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(ocr_one, str(p), args.endpoint, args.timeout): p for p in pdfs}
        done = 0
        for fut in as_completed(futs):
            _, status, size, _ = fut.result()
            if status == "ok":
                stats["ok"] += 1; stats["bytes"] += size
            elif status == "skip":
                stats["skip"] += 1
            elif status in ("empty-ocr",):
                stats["empty"] += 1
            else:
                stats["err"] += 1
            done += 1
            if done % 10 == 0 or time.time() - last > 30:
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                eta = (len(pdfs) - done) / rate / 60 if rate > 0 else 0
                print(f"  done={done}/{len(pdfs)} ok={stats['ok']} skip={stats['skip']} "
                      f"err={stats['err']} empty={stats['empty']} MB={stats['bytes']/1e6:.1f} "
                      f"rate={rate:.2f}/s ETA={eta:.0f}min", flush=True)
                last = time.time()
    print(f"\n[DONE] {time.time()-t0:.0f}s wall | {dict(stats)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
