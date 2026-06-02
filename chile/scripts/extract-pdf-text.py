#!/usr/bin/env python3
"""
Extrae texto de PDFs → `<archivo>.pdf.txt` junto al original, para que el
pipeline (embed-loop / embed-new-source / build-fts-index) lo indexe como texto.

Estrategia por archivo:
  1) pdftotext -layout  → si rinde >= MIN_CHARS, es PDF DIGITAL, listo.
  2) si rinde poco (PDF ESCANEADO) → OCR con ocrmypdf (--sidecar) o tesseract.
  3) escribe <name>.pdf.txt. Idempotente: salta si ya existe y no está vacío.

Pensado para fuentes con PDFs mixtos digital/escaneado (recursos administrativos
SOFOFA, TA sentencias, Diario Oficial histórico). CPU puro, NO toca la GPU.

Uso:
  python3 scripts/extract-pdf-text.py --src data/recursos-administrativos --workers 4
  python3 scripts/extract-pdf-text.py --src data/tribunal-ambiental --workers 4 --ocr
  python3 scripts/extract-pdf-text.py --src data/recursos-administrativos --no-ocr   # solo digitales (rápido)
"""
import argparse, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

MIN_CHARS = 200          # umbral para considerar "digital" (texto real, no header suelto)
_lock = Lock()
_st = {"digital":0, "ocr":0, "ocr_fail":0, "skip":0, "empty":0}

def log(*a):
    with _lock: print(*a, file=sys.stderr, flush=True)

def pdftotext(p: Path) -> str:
    try:
        r = subprocess.run(["pdftotext","-layout",str(p),"-"],
                           capture_output=True, timeout=120)
        return r.stdout.decode("utf-8","replace")
    except Exception:
        return ""

def ocr(p: Path) -> str:
    # ocrmypdf con sidecar (texto plano) — fuerza OCR aunque no haya capa de texto.
    side = p.with_suffix(p.suffix+".ocr.txt")
    try:
        subprocess.run(["ocrmypdf","-l","spa","--force-ocr","--sidecar",str(side),
                        "--output-type","none","--quiet",str(p),"-"],
                       capture_output=True, timeout=900)
        if side.exists():
            t = side.read_text("utf-8","replace"); side.unlink(missing_ok=True)
            return t
    except Exception:
        pass
    # fallback: tesseract directo no maneja PDF multipágina sin pdftoppm; lo dejamos a ocrmypdf
    return ""

def process(p: Path, do_ocr: bool):
    out = Path(str(p)+".txt")          # foo.pdf → foo.pdf.txt
    if out.exists() and out.stat().st_size > 50:
        with _lock: _st["skip"]+=1
        return
    txt = pdftotext(p)
    if len(txt.strip()) >= MIN_CHARS:
        out.write_text(txt,"utf-8");
        with _lock: _st["digital"]+=1
        return
    if do_ocr:
        txt2 = ocr(p)
        if len(txt2.strip()) >= 50:
            out.write_text(txt2,"utf-8")
            with _lock: _st["ocr"]+=1
            return
        with _lock: _st["ocr_fail"]+=1
    # digital pobre o sin OCR: igual grabar lo poco que haya (mejor que nada) o marcar vacío
    if txt.strip():
        out.write_text(txt,"utf-8")
        with _lock: _st["digital"]+=1
    else:
        with _lock: _st["empty"]+=1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src",required=True)
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--ocr",dest="ocr",action="store_true",default=True)
    ap.add_argument("--no-ocr",dest="ocr",action="store_false")
    ap.add_argument("--limit",type=int)
    a=ap.parse_args()
    root=Path(a.src)
    pdfs=[p for p in root.rglob("*") if p.suffix.lower()==".pdf"]
    if a.limit: pdfs=pdfs[:a.limit]
    log(f"[extract-pdf] {len(pdfs)} PDFs en {a.src} · workers={a.workers} · OCR={'on' if a.ocr else 'off'}")
    t0=time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs=[ex.submit(process,p,a.ocr) for p in pdfs]
        done=0
        for _ in as_completed(futs):
            done+=1
            if done%200==0:
                el=time.time()-t0
                log(f"  · {done}/{len(pdfs)} · {dict(_st)} · {done/el:.1f}/s")
    log(f"[FIN] {dict(_st)} · {time.time()-t0:.0f}s")

if __name__=="__main__":
    main()
