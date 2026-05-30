#!/usr/bin/env python3
# std:input -
# std:output oficios/jurisprudencia administrativa SII (PDF + texto) en data/sii-oficios/ + manifest
# std:deps stdlib + Zyte (enumeración JS) ; descarga directa sin Zyte
"""
Bulk oficios SII — jurisprudencia administrativa tributaria (renta, IVA, otras).

Contrato (verificado 2026-05-30):
- Las páginas índice `<materia>/<anio>/<materia>_jadm<anio>.htm` son SPAs JS:
  se renderizan con **Zyte browserHtml** (geo CL). Cada oficio aparece como
  `abreDoctoJurAdm('<nombre>','pdf','download','<GUID>','application/pdf')`.
- La descarga es un **GET directo** (sin Zyte) a
  `https://www4.sii.cl/gabineteAdmInternet/descargaArchivo?nombreDocumento=..&
   extension=pdf&acc=download&id=<GUID>&mediaType=application/pdf` → PDF real.

Materias: ley_impuesto_renta, ley_impuesto_ventas, otras_normas. Barrido por año
reverse (más reciente primero). Fase 1 (--list-only) enumera vía Zyte; Fase 2
descarga directo + extrae texto. Idempotente.
"""
from __future__ import annotations
import argparse, base64, json, os, re, sqlite3, subprocess, sys, time
import urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/sii-oficios"
BASE = "https://www.sii.cl/normativa_legislacion/jurisprudencia_administrativa"
DESCARGA = "https://www4.sii.cl/gabineteAdmInternet/descargaArchivo"
MATERIAS = ["ley_impuesto_renta", "ley_impuesto_ventas", "otras_normas"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
# abreDoctoJurAdm('2398-12/12/2024.pdf','pdf','download','<guid>','application/pdf')
_OFIC_RE = re.compile(
    r"abreDoctoJurAdm\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'[^']*'\s*,\s*'([0-9a-fA-F-]{36})'\s*,\s*'([^']*)'\s*\)"
    r"[^>]*>([^<]+)</a>", re.I)


def zyte_html(url: str, auth: str, timeout=120) -> str | None:
    payload = json.dumps({"url": url, "browserHtml": True, "geolocation": "CL"}).encode()
    req = urllib.request.Request("https://api.zyte.com/v1/extract", data=payload,
                                 headers={"Authorization": f"Basic {auth}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("browserHtml", "")
    except Exception:
        return None


def http_get(url: str, timeout=60) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def init_manifest(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db), check_same_thread=False, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("CREATE TABLE IF NOT EXISTS oficios ("
              "guid TEXT PRIMARY KEY, nombre TEXT, extension TEXT, mediatype TEXT, "
              "materia TEXT, anio INTEGER, titulo TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def enumerate_jadm(conn, materia: str, anio: int, auth: str) -> int:
    url = f"{BASE}/{materia}/{anio}/{materia}_jadm{anio}.htm"
    html = zyte_html(url, auth)
    if not html:
        return 0
    nuevos = 0
    with _LOCK:
        for nombre, ext, guid, media, titulo in _OFIC_RE.findall(html):
            cur = conn.execute(
                "INSERT OR IGNORE INTO oficios(guid, nombre, extension, mediatype, materia, anio, titulo) "
                "VALUES (?,?,?,?,?,?,?)",
                (guid, nombre, ext or "pdf", media or "application/pdf", materia, anio,
                 re.sub(r"\s+", " ", titulo).strip()[:500]))
            nuevos += cur.rowcount
        conn.commit()
    print(f"  [enum] {materia} {anio}: +{nuevos}", flush=True)
    return nuevos


def download_one(row) -> tuple:
    guid, nombre, ext, media = row
    out = OUTPUT_ROOT / "pdfs" / f"{guid}.pdf"
    txt = OUTPUT_ROOT / "txt" / f"{guid}.txt"
    if out.exists() and out.stat().st_size > 0:
        return (guid, "skip", out.stat().st_size)
    q = urllib.parse.urlencode({"nombreDocumento": nombre, "extension": ext,
                                "acc": "download", "id": guid, "mediaType": media})
    data = http_get(f"{DESCARGA}?{q}")
    if not data or data[:4] != b"%PDF":
        return (guid, "err", 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    txt.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    try:
        r = subprocess.run(["pdftotext", "-layout", str(out), str(txt)],
                           capture_output=True, timeout=120)
    except Exception:
        pass
    return (guid, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio-tope", type=int, required=True)
    ap.add_argument("--desde-anio", type=int, default=2001)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("ZYTE_API_KEY", "")
    if not key:
        envf = _REPO_ROOT / "chile/.env"
        if envf.exists():
            for line in envf.read_text().splitlines():
                if line.startswith("ZYTE_API_KEY="):
                    key = line.split("=", 1)[1].strip()
    if not key:
        print("ERROR: requiere ZYTE_API_KEY (env o chile/.env) para enumerar", flush=True)
        return 2
    auth = base64.b64encode(f"{key}:".encode()).decode()

    conn = init_manifest(OUTPUT_ROOT / "manifest.sqlite3")

    # Fase 1: enumerar (Zyte) por materia × año, reverse
    for anio in range(args.anio_tope, args.desde_anio - 1, -1):
        for materia in MATERIAS:
            enumerate_jadm(conn, materia, anio, auth)
            time.sleep(0.2)
    total = conn.execute("SELECT count(*) FROM oficios").fetchone()[0]
    print(f"[enum] manifest: {total} oficios", flush=True)
    if args.list_only:
        return 0

    # Fase 2: descargar directo (sin Zyte)
    rows = conn.execute(
        "SELECT guid, nombre, extension, mediatype FROM oficios WHERE downloaded=0").fetchall()
    print(f"[fetch] {len(rows)} pendientes (workers={args.workers})", flush=True)
    t0, done = time.time(), 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, r): r for r in rows}
        for fut in as_completed(futs):
            guid, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE oficios SET downloaded=1, size=? WHERE guid=?", (size, guid))
                    conn.commit()
            done += 1
            if done % 50 == 0:
                print(f"  done={done}/{len(rows)} {_STATS} rate={done/(time.time()-t0):.1f}/s", flush=True)
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
