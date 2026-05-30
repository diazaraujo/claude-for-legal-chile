#!/usr/bin/env python3
# std:input -
# std:output normas SAG (PDF + texto) en data/sag-normativa/ + manifest
# std:deps stdlib + Zyte (render del treeview) ; descarga directa sin Zyte
"""
Bulk normativa SAG — resoluciones/normas sanitarias y fitosanitarias.

Mecanismo (verificado 2026-05-30):
- El buscador `normativa.sag.gob.cl/Publico/Inicio.aspx` es ASP.NET WebForms con
  un **TreeView** de categorías. Cada norma es un PDF DIRECTO en
  `https://normativa.sag.gob.cl/Upload/ArchivoIndice/<GUID32>.pdf` (sin Zyte para
  el PDF; sí Zyte browserHtml para renderizar el árbol, que es JS).

LIMITACIÓN CONOCIDA (honesta): el TreeView usa full-postback con distinción
expand/select + populate-on-demand. La cobertura COMPLETA exige crawlear 265
nodos vía postbacks stateful (VIEWSTATE encadenado) — build dedicado frágil,
desproporcionado al valor sectorial de SAG. Este scraper baja las normas
ALCANZABLES desde el render del árbol (default + categorías visibles). Para
cobertura total falta el crawler de postbacks del TreeView (TODO documentado).

Idempotente. Descarga directa de los GUID encontrados.
"""
from __future__ import annotations
import argparse, base64, json, os, re, sqlite3, subprocess, sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/sag-normativa"
INICIO = "https://normativa.sag.gob.cl/Publico/Inicio.aspx"
PDF_BASE = "https://normativa.sag.gob.cl/Upload/ArchivoIndice"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
_GUID_RE = re.compile(r"/Upload/ArchivoIndice/([0-9a-f]{32})\.pdf", re.I)


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
    c.execute("CREATE TABLE IF NOT EXISTS normas ("
              "guid TEXT PRIMARY KEY, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def download_one(guid: str):
    out = OUTPUT_ROOT / "pdfs" / f"{guid}.pdf"
    txt = OUTPUT_ROOT / "txt" / f"{guid}.txt"
    if out.exists() and out.stat().st_size > 0:
        return (guid, "skip", out.stat().st_size)
    data = http_get(f"{PDF_BASE}/{guid}.pdf")
    if not data or data[:4] != b"%PDF":
        return (guid, "err", 0)
    out.parent.mkdir(parents=True, exist_ok=True); txt.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    try:
        subprocess.run(["pdftotext", "-layout", str(out), str(txt)], capture_output=True, timeout=120)
    except Exception:
        pass
    return (guid, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
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
        print("ERROR: requiere ZYTE_API_KEY para renderizar el árbol", flush=True)
        return 2
    auth = base64.b64encode(f"{key}:".encode()).decode()

    conn = init_manifest(OUTPUT_ROOT / "manifest.sqlite3")
    # Enumerar: render del árbol (Zyte) → GUIDs alcanzables
    html = zyte_html(INICIO, auth) or ""
    guids = set(g.lower() for g in _GUID_RE.findall(html))
    with _LOCK:
        for g in guids:
            conn.execute("INSERT OR IGNORE INTO normas(guid) VALUES (?)", (g,))
        conn.commit()
    print(f"[enum] GUIDs alcanzables desde el árbol: {len(guids)} "
          f"(cobertura total requiere crawler de postbacks del TreeView — TODO)", flush=True)
    if args.list_only:
        return 0

    rows = [r[0] for r in conn.execute("SELECT guid FROM normas WHERE downloaded=0").fetchall()]
    print(f"[fetch] {len(rows)} normas (descarga directa, sin Zyte)", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, g): g for g in rows}
        for fut in as_completed(futs):
            guid, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE normas SET downloaded=1, size=? WHERE guid=?", (size, guid))
                    conn.commit()
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
