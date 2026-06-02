#!/usr/bin/env python3
# std:input rango de meses (YYYYMM) + output dir
# std:output PDF/JPGs en {output}/YYYY/MM/DD/ + manifest SQLite
# std:deps stdlib pura + ThreadPoolExecutor
"""
Descarga BULK del DIARIO OFICIAL HISTÓRICO de Chile — edición IMPRESA
01-03-1877 → 16-08-2016 (lo ANTERIOR a la edición electrónica que ya tenemos
en data/diario-oficial/, que arranca el 17-08-2016).

Aplica "toda la data desde el origen" + "ingest reciente→viejo" (reglas Antonio).

═══ MECANISMO (crackeado 2026-06-01, sitio oficial diariooficial.interior.gob.cl) ═══
El visor "Edición Impresa" / versiones-anteriores expone TODO como archivos
estáticos con patrón determinístico. NO requiere navegar el visor para bajar:

  1) Listado de fechas válidas de un mes  →  POST a /versiones-anteriores/
        body: searchBy=YYYYMM&mes=MM&anio=YYYY
        respuesta: HTML con celdas <a href="/versiones-anteriores/do-h/YYYYMMDD/">
  2) Página-día (manifest de la edición)   →  GET /versiones-anteriores/do-h/YYYYMMDD/
        contiene: href al PDF consolidado  /media/YYYY/MM/DD/do-YYYYMMDD.pdf
                  + <img src> de cada página /media/YYYY/MM/DD/DDNNNNNN.jpg
  3) Descarga directa:
        PRIMARIO : /media/YYYY/MM/DD/do-YYYYMMDD.pdf   (Content-Type application/pdf)
        FALLBACK : las páginas JPG (años muy viejos a veces no tienen PDF consolidado)

Verificado en vivo: 1985-01-02 → PDF 9.5 MB OK; 1877-03-01 → PDF 404 pero
01000001.jpg (44 KB, JPEG real) OK; marzo-1877 = 24 ediciones listadas.

═══ SALIDA ═══
  {output}/YYYY/MM/DD/do-YYYYMMDD.pdf            # edición consolidada (si existe)
  {output}/YYYY/MM/DD/DDNNNNNN.jpg               # páginas escaneadas (--jpg o fallback)
  {output}/manifest.sqlite3
     descargas(date TEXT PK, n_pages, pdf_bytes, jpg_count, status, error, ts)

Idempotente: skip ediciones ya OK en manifest + archivos ya en disco; resume.

Uso:
  python3 diario-oficial-historico-bulk.py                       # 2016→1877 completo, solo PDF
  python3 diario-oficial-historico-bulk.py --from 200001 --to 201608
  python3 diario-oficial-historico-bulk.py --jpg                 # además baja todas las páginas JPG
  python3 diario-oficial-historico-bulk.py --workers 8 --dry-run
"""
from __future__ import annotations
import argparse, base64, json, os, re, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

BASE = "https://www.diariooficial.interior.gob.cl"
VA   = f"{BASE}/versiones-anteriores/"
UA   = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
FIRST_YM, LAST_YM = 187703, 201608          # 01-mar-1877 .. 16-ago-2016 (impresa)
ZYTE_API = "https://api.zyte.com/v1/extract"
ZYTE_AUTH = None                            # se setea en main() si --zyte
REQ_SLEEP = 0.0                             # throttle por request (seg), se setea en main()

# El visor usa DOS prefijos de ruta: 'do-h/' (años antiguos) y 'do/' (años recientes)
DOH_RE  = re.compile(r"/versiones-anteriores/(do-h|do)/(\d{8})/")
PDF_RE  = re.compile(r'href="(/media/\d{4}/\d{2}/\d{2}/do-\d{8}\.pdf)"')
JPG_RE  = re.compile(r'src="(?:https?://[^"]+)?(/media/\d{4}/\d{2}/\d{2}/\d{8}\.jpg)"')

_print_lock = Lock()
def log(*a):
    with _print_lock: print(*a, file=sys.stderr, flush=True)

def _http_direct(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"User-Agent": UA, "Referer": VA})
    if data:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _http_zyte(url, data=None, timeout=90):
    payload = {"url": url, "httpResponseBody": True}
    if data:
        payload["httpRequestMethod"] = "POST"
        payload["httpRequestText"] = data.decode("utf-8", "replace")
        payload["customHttpRequestHeaders"] = [
            {"name": "Content-Type", "value": "application/x-www-form-urlencoded"}]
    req = urllib.request.Request(
        ZYTE_API, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {ZYTE_AUTH}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        obj = json.loads(r.read())
    code = obj.get("statusCode")
    if code and code >= 400:
        raise urllib.error.HTTPError(url, code, "zyte upstream", None, None)
    b64 = obj.get("httpResponseBody", "")
    return base64.b64decode(b64) if b64 else b""

# 520/503/502/429 (y errores Zyte 429/5xx) = transitorios → retry con backoff.
# 404/400 = definitivos → propagar.
_TRANSIENT = {429, 500, 502, 503, 520, 521, 522, 524}
def http(url, data=None, timeout=60, binary=False, retries=4):
    last = None
    for i in range(retries):
        if REQ_SLEEP:
            time.sleep(REQ_SLEEP)
        try:
            body = (_http_zyte(url, data, max(timeout, 90)) if ZYTE_AUTH
                    else _http_direct(url, data, timeout))
            return body if binary else body.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in _TRANSIENT:
                last = e; time.sleep(2 * (i + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e; time.sleep(2 * (i + 1)); continue
    raise last

def months(a, b):                            # itera YYYYMM inclusive a..b
    y, m = a // 100, a % 100
    out = []
    while y * 100 + m <= b:
        out.append(y * 100 + m)
        m += 1
        if m == 13: y, m = y + 1, 1
    return out

def valid_dates(ym):                         # [(date8, kind)] con edición en el mes
    y, m = ym // 100, f"{ym % 100:02d}"
    try:
        html = http(VA, data=f"searchBy={ym}&mes={m}&anio={y}".encode())
    except Exception as e:
        log(f"  ! mes {ym}: {e}"); return []
    # DOH_RE captura (kind, date8); devolvemos (date8, kind)
    return sorted({(d, k) for k, d in DOH_RE.findall(html)})

def edition_assets(date8, kind):             # (pdf_path|None, [jpg_paths])
    url = f"{BASE}/versiones-anteriores/{kind}/{date8}/"
    html = http(url)
    pdf = PDF_RE.search(html)
    jpgs = sorted(set(JPG_RE.findall(html)))
    return (pdf.group(1) if pdf else None), jpgs

def download(path_rel, dest: Path):          # baja BASE+path_rel → dest, devuelve bytes o 0
    if dest.exists() and dest.stat().st_size > 0:
        return dest.stat().st_size
    try:
        blob = http(BASE + path_rel, binary=True)
    except urllib.error.HTTPError as e:
        if e.code == 404: return 0
        raise
    if not blob or blob[:4] not in (b"%PDF", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"):
        # algunos jpg traen otros markers \xff\xd8\xff\xdb etc.
        if not (blob[:2] == b"\xff\xd8" or blob[:4] == b"%PDF"):
            return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(blob); tmp.rename(dest)
    return len(blob)

def init_db(p: Path):
    con = sqlite3.connect(p, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("""CREATE TABLE IF NOT EXISTS descargas(
        date TEXT PRIMARY KEY, n_pages INTEGER, pdf_bytes INTEGER,
        jpg_count INTEGER, status TEXT, error TEXT, ts INTEGER)""")
    con.commit(); return con

def process_date(item, outdir: Path, want_jpg: bool, dry: bool):
    date8, kind = item
    y, m, d = date8[:4], date8[4:6], date8[6:8]
    day_dir = outdir / y / m / d
    try:
        pdf_rel, jpgs = edition_assets(date8, kind)
    except Exception as e:
        return (date8, 0, 0, 0, "error", f"manifest:{e}")
    if dry:
        return (date8, len(jpgs), 0, 0, "dry", f"pdf={'si' if pdf_rel else 'no'}")
    pdf_bytes = 0
    if pdf_rel:
        pdf_bytes = download(pdf_rel, day_dir / Path(pdf_rel).name)
    jpg_count = 0
    # baja JPGs si se pidió, o como fallback si no hubo PDF consolidado
    if want_jpg or pdf_bytes == 0:
        for jp in jpgs:
            if download(jp, day_dir / Path(jp).name) > 0:
                jpg_count += 1
    ok = pdf_bytes > 0 or jpg_count > 0
    status = "ok" if ok else "empty"
    err = "" if ok else "sin pdf ni jpg"
    return (date8, len(jpgs), pdf_bytes, jpg_count, status, err)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", type=int, default=FIRST_YM, help="YYYYMM")
    ap.add_argument("--to",   dest="to",  type=int, default=LAST_YM,  help="YYYYMM")
    ap.add_argument("--output", default="data/diario-oficial-historico")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--jpg", action="store_true", help="bajar también páginas JPG (no solo PDF)")
    ap.add_argument("--reverse", action="store_true", default=True, help="reciente→viejo (default)")
    ap.add_argument("--forward", dest="reverse", action="store_false")
    ap.add_argument("--zyte", action="store_true", help="rutear por Zyte (bypassa el IP-block del sitio). Requiere env ZYTE_API_KEY")
    ap.add_argument("--sleep", type=float, default=0.0, help="throttle seg/request (directo); usar ~0.5 sin Zyte")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    global ZYTE_AUTH, REQ_SLEEP
    REQ_SLEEP = a.sleep
    if a.zyte:
        key = os.environ.get("ZYTE_API_KEY", "")
        if not key:
            log("ERROR: --zyte requiere env ZYTE_API_KEY"); sys.exit(1)
        ZYTE_AUTH = base64.b64encode(f"{key}:".encode()).decode()
        log("[ZYTE] proxy habilitado (bypass IP-block)")

    outdir = Path(a.output); outdir.mkdir(parents=True, exist_ok=True)
    con = init_db(outdir / "manifest.sqlite3"); dblock = Lock()
    done = {r[0] for r in con.execute(
        "SELECT date FROM descargas WHERE status IN('ok','dry')").fetchall()}

    ms = months(a.frm, a.to)
    if a.reverse: ms = ms[::-1]
    log(f"=== DO histórico {a.frm}→{a.to} · {len(ms)} meses · "
        f"{'reverse' if a.reverse else 'forward'} · workers={a.workers} · "
        f"{'PDF+JPG' if a.jpg else 'PDF (jpg fallback)'} · ya hechas={len(done)} ===")

    tot_ed = tot_pdf = tot_jpg = tot_bytes = 0
    for ym in ms:
        dates = [it for it in valid_dates(ym) if it[0] not in done]
        if not dates:
            continue
        log(f"[{ym}] {len(dates)} ediciones")
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(process_date, it, outdir, a.jpg, a.dry_run): it[0] for it in dates}
            for f in as_completed(futs):
                date8, n_pages, pdf_b, jpg_c, status, err = f.result()
                with dblock:
                    con.execute("INSERT OR REPLACE INTO descargas VALUES(?,?,?,?,?,?,?)",
                                (date8, n_pages, pdf_b, jpg_c, status, err, int(time.time())))
                    con.commit()
                tot_ed += 1; tot_bytes += pdf_b
                if pdf_b > 0: tot_pdf += 1
                tot_jpg += jpg_c
                if tot_ed % 50 == 0:
                    log(f"  · {tot_ed} ediciones · {tot_pdf} pdf · {tot_jpg} jpg · "
                        f"{tot_bytes/1e9:.2f} GB")
    log(f"=== FIN · {tot_ed} ediciones nuevas · {tot_pdf} PDF · {tot_jpg} JPG · "
        f"{tot_bytes/1e9:.2f} GB ===")
    con.close()

if __name__ == "__main__":
    main()
