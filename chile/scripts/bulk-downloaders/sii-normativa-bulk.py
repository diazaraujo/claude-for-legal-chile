#!/usr/bin/env python3
# std:input [--from-year N] [--to-year N] [--workers N]
# std:output Circulares + Resoluciones Exentas SII en data/sii-normativa/ + manifest
# std:deps stdlib (urllib + sqlite3)
"""
Bulk Circulares + Resoluciones Exentas del SII (normativa interpretativa tributaria),
gap detectado por deep-research (31-may): el corpus tenía SII oficios pero no la
serie completa de circulares/resoluciones. [[reference_legal_chile_fuentes_faltantes]]

Acceso (verificado):
- Circulares: PDFs en URL predecible `sii.cl/normativa_legislacion/circulares/<año>/circu<N>.pdf`
  con N SIN cero a la izquierda (`circu1.pdf`, no `circu01.pdf`). El índice
  `indcir<año>.htm` es JS (sin hrefs) → se enumera por brute-force de N hasta varios
  404 seguidos. El patrón circu<N>.pdf funciona ~2013→hoy.
- Resoluciones Exentas: el índice `resoluciones/<año>/res_ind<año>.htm` SÍ lista los
  PDFs directamente (~135/año) → parse de hrefs.

Idempotente. pdftotext para el texto.
"""
from __future__ import annotations
import argparse, re, sqlite3, ssl, subprocess, sys
import urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = _REPO_ROOT / "chile/data/sii-normativa"
BASE = "https://www.sii.cl/normativa_legislacion"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}


def http(url, t=40):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=t, context=_CTX) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def init_db():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(OUT / "manifest.sqlite3"), check_same_thread=False, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS docs (url TEXT PRIMARY KEY, tipo TEXT, anio INTEGER, "
              "numero INTEGER, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def enum_circulares(c, y0, y1):
    nuevos = 0
    for year in range(y1, y0 - 1, -1):
        miss = 0
        n = 0
        while miss < 10 and n < 200:
            n += 1
            url = f"{BASE}/circulares/{year}/circu{n}.pdf"
            s, b = http(url, t=15)
            if s == 200 and b[:4] == b"%PDF":
                with _LOCK:
                    nuevos += c.execute("INSERT OR IGNORE INTO docs(url,tipo,anio,numero) VALUES (?,?,?,?)",
                                        (url, "circular", year, n)).rowcount
                miss = 0
            else:
                miss += 1
        with _LOCK:
            c.commit()
        cnt = c.execute("SELECT count(*) FROM docs WHERE tipo='circular' AND anio=?", (year,)).fetchone()[0]
        print(f"  [circ] {year}: {cnt} circulares", flush=True)
        if cnt == 0 and year < 2015:
            break  # bajo 2013-2015 el patrón circu<N>.pdf ya no existe
    return nuevos


def enum_resoluciones(c, y0, y1):
    nuevos = 0
    for year in range(y1, y0 - 1, -1):
        s, b = http(f"{BASE}/resoluciones/{year}/res_ind{year}.htm")
        if s != 200:
            if year < 2015:
                break
            continue
        txt = b.decode("utf-8", "replace")
        # el índice referencia los PDFs como reso<N>.pdf / res<N>.pdf en texto/JS, no en href=
        fnames = set(re.findall(r'\b(res[o]?\d+\.pdf)\b', txt, re.I))
        with _LOCK:
            for fn in fnames:
                url = f"{BASE}/resoluciones/{year}/{fn}"
                m = re.search(r'res[o]?(\d+)\.pdf', fn, re.I)
                nuevos += c.execute("INSERT OR IGNORE INTO docs(url,tipo,anio,numero) VALUES (?,?,?,?)",
                                    (url, "resolucion", year, int(m.group(1)) if m else None)).rowcount
            c.commit()
        pdfs = fnames
        print(f"  [res] {year}: {len(pdfs)} resoluciones", flush=True)
    return nuevos


def download_one(url):
    # incluir el AÑO en el nombre: circu1.pdf existe en cada año → colisionaban
    m = re.search(r"/(circulares|resoluciones)/(\d{4})/([^/]+)$", url)
    if m:
        tipo, year, fn = m.group(1), m.group(2), m.group(3)
        name = f"{year}_{re.sub(r'[^A-Za-z0-9._-]', '_', fn)}"
    else:
        tipo = "circulares" if "circu" in url else "resoluciones"
        name = re.sub(r"[^A-Za-z0-9._-]", "_", url.rsplit("/", 1)[-1])
    dest = OUT / tipo / name
    if dest.exists() and dest.stat().st_size > 0:
        return (url, "skip", dest.stat().st_size)
    s, b = http(url, t=60)
    if s != 200 or b[:4] != b"%PDF":
        return (url, "err", 0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b)
    txt = OUT / "txt" / (name + ".txt")
    txt.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["pdftotext", "-layout", str(dest), str(txt)], capture_output=True, timeout=120)
    except Exception:
        pass
    return (url, "ok", len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-year", type=int, default=2009)
    ap.add_argument("--to-year", type=int, default=2026)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    c = init_db()
    print("[FASE 1] Enumerando circulares + resoluciones SII…", flush=True)
    enum_circulares(c, args.from_year, args.to_year)
    enum_resoluciones(c, args.from_year, args.to_year)
    total = c.execute("SELECT count(*) FROM docs").fetchone()[0]
    print(f"[enum] {total} docs en manifest", flush=True)
    rows = [r[0] for r in c.execute("SELECT url FROM docs WHERE downloaded=0")]
    print(f"[FASE 2] Descargando {len(rows)}…", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, u): u for u in rows}
        for fut in as_completed(futs):
            url, st, sz = fut.result()
            _STATS[st if st in _STATS else "err"] += 1
            if st in ("ok", "skip"):
                with _LOCK:
                    c.execute("UPDATE docs SET downloaded=1, size=? WHERE url=?", (sz, url)); c.commit()
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
