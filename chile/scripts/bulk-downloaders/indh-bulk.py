#!/usr/bin/env python3
# std:input [--workers N]
# std:output Biblioteca digital INDH (PDFs + texto + metadata) en data/indh/ + manifest
# std:deps stdlib (urllib + sqlite3 + json)
"""
Bulk biblioteca digital del INDH (Instituto Nacional de Derechos Humanos), gap
detectado por deep-research (31-may). Doctrina DDHH: informes, actas del Consejo,
amicus, recursos de amparo, estudios. [[reference_legal_chile_fuentes_faltantes]]

Acceso: DSpace 7 **REST API** (el OAI-PMH del sitio devuelve noRecordsMatch — índice
OAI sin construir). Endpoints:
- listado: /server/api/discover/search/objects?dsoType=item&size=100&page=N  (~1650 items)
- bitstreams: /server/api/core/items/<uuid>/bundles → bundle ORIGINAL → bitstreams
- descarga: /server/api/core/bitstreams/<uuid>/content

Idempotente por uuid de bitstream. pdftotext para el texto.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, ssl, subprocess, sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = _REPO_ROOT / "chile/data/indh"
API = "https://bibliotecadigital.indh.cl/server/api"
UA = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept": "application/json"}
_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}


def getj(url, t=40):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t, context=_CTX).read()
        return json.loads(b)
    except Exception:
        return None


def getb(url, t=90):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]}),
                                      timeout=t, context=_CTX).read()
    except Exception:
        return None


def init_db():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(OUT / "manifest.sqlite3"), check_same_thread=False, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS docs (bitstream TEXT PRIMARY KEY, item TEXT, titulo TEXT, "
              "filename TEXT, url TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def enumerate_items(c):
    page, total_pages = 0, 1
    nuevos = 0
    while page < total_pages:
        d = getj(f"{API}/discover/search/objects?dsoType=item&size=100&page={page}")
        if not d:
            break
        sr = d.get("_embedded", {}).get("searchResult", {})
        total_pages = sr.get("page", {}).get("totalPages", page + 1)
        objs = sr.get("_embedded", {}).get("objects", [])
        for o in objs:
            it = o.get("_embedded", {}).get("indexableObject", {})
            uuid, name = it.get("uuid"), it.get("name", "")
            if not uuid:
                continue
            # bundles → ORIGINAL → bitstreams
            bd = getj(f"{API}/core/items/{uuid}/bundles")
            for bundle in (bd or {}).get("_embedded", {}).get("bundles", []):
                if bundle.get("name") != "ORIGINAL":
                    continue
                bsd = getj(bundle.get("_links", {}).get("bitstreams", {}).get("href", ""))
                for bs in (bsd or {}).get("_embedded", {}).get("bitstreams", []):
                    bid = bs.get("uuid"); fn = bs.get("name", "")
                    if not bid or not fn.lower().endswith(".pdf"):
                        continue
                    url = f"{API}/core/bitstreams/{bid}/content"
                    with _LOCK:
                        nuevos += c.execute(
                            "INSERT OR IGNORE INTO docs(bitstream,item,titulo,filename,url) VALUES (?,?,?,?,?)",
                            (bid, uuid, name[:300], fn, url)).rowcount
        with _LOCK:
            c.commit()
        if page % 10 == 0:
            print(f"  [enum] page {page}/{total_pages} · {c.execute('SELECT count(*) FROM docs').fetchone()[0]} bitstreams", flush=True)
        page += 1
    return nuevos


def download_one(row):
    bid, fn, url = row
    name = f"{bid[:8]}_{re.sub(r'[^A-Za-z0-9._-]', '_', fn)}"[:140]
    dest = OUT / "pdfs" / name
    if dest.exists() and dest.stat().st_size > 0:
        return (bid, "skip", dest.stat().st_size)
    b = getb(url)
    if not b or b[:4] != b"%PDF":
        return (bid, "err", 0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b)
    txt = OUT / "txt" / (name + ".txt")
    txt.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["pdftotext", "-layout", str(dest), str(txt)], capture_output=True, timeout=120)
    except Exception:
        pass
    return (bid, "ok", len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    c = init_db()
    print("[FASE 1] Enumerando items INDH (DSpace REST)…", flush=True)
    enumerate_items(c)
    total = c.execute("SELECT count(*) FROM docs").fetchone()[0]
    print(f"[enum] {total} bitstreams PDF", flush=True)
    rows = c.execute("SELECT bitstream, filename, url FROM docs WHERE downloaded=0").fetchall()
    print(f"[FASE 2] Descargando {len(rows)}…", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, r): r for r in rows}
        for fut in as_completed(futs):
            bid, st, sz = fut.result()
            _STATS[st if st in _STATS else "err"] += 1
            if st in ("ok", "skip"):
                with _LOCK:
                    c.execute("UPDATE docs SET downloaded=1, size=? WHERE bitstream=?", (sz, bid)); c.commit()
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
