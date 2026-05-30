#!/usr/bin/env python3
# std:input -
# std:output normativa SAG (PDF + texto + metadata) en data/sag-normativa/ + manifest
# std:deps stdlib (urllib + sqlite3 + re) — descarga directa
"""
Bulk normativa SAG — resoluciones, consultas públicas, procedimientos.

Fuente (verificada 2026-05-30): el portal Drupal
`sag.gob.cl/ambitos-de-accion/resoluciones-consultas-publicas/<subseccion>` es un
**Drupal view paginado** (`?page=N`), server-rendered, con una tabla por fila:
título (link al PDF en /sites/default/files/), N°, fecha, estado, tipo. Sin
treeview ni JS. Mucho más limpio que el buscador normativa.sag.gob.cl.

Subsecciones: normativas, procedimientos, publicaciones, registros.
Pagina cada una hasta que no haya filas con PDF. Descarga directa + pdftotext.
Idempotente.
"""
from __future__ import annotations
import argparse, html, re, sqlite3, subprocess, sys, time
import urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/sag-normativa"
BASE = "https://www.sag.gob.cl"
SECTION = "/ambitos-de-accion/resoluciones-consultas-publicas"
SUBS = ["normativas", "procedimientos", "publicaciones", "registros"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_PDF = re.compile(r'href="([^"]+\.pdf)"', re.I)


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
              "pdf_url TEXT PRIMARY KEY, subseccion TEXT, titulo TEXT, numero TEXT, "
              "fecha TEXT, estado TEXT, tipo TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def _field(row, cls):
    m = re.search(r'views-field-%s[^>]*>\s*(?:<a[^>]*>)?\s*([^<]+)' % cls, row)
    return html.unescape(m.group(1).strip()) if m and m.group(1).strip() else None


def parse_page(htmltext: str):
    out = []
    for row in _ROW.findall(htmltext):
        m = _PDF.search(row)
        if not m:
            continue
        url = urllib.parse.urljoin(BASE, html.unescape(m.group(1)))
        titulo = (re.search(r'views-field-nothing[^>]*>\s*<a[^>]*>([^<]+)', row)
                  or re.search(r'\.pdf"[^>]*>([^<]+)', row))
        out.append(dict(
            pdf_url=url,
            titulo=html.unescape(titulo.group(1).strip())[:300] if titulo else None,
            numero=_field(row, "field-n-"),
            fecha=_field(row, "field-fecha-publicaci-n-do"),
            estado=_field(row, "field-estado"),
            tipo=_field(row, "field-tipo-de-normativa")))
    return out


def enumerate_sub(conn, sub: str) -> int:
    page, nuevos, empty = 0, 0, 0
    while True:
        body = http_get(f"{BASE}{SECTION}/{sub}?page={page}")
        if not body:
            break
        rows = parse_page(body.decode("utf-8", "replace"))
        if not rows:
            empty += 1
            if empty >= 1:
                break
        with _LOCK:
            for r in rows:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO normas(pdf_url, subseccion, titulo, numero, fecha, estado, tipo) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (r["pdf_url"], sub, r["titulo"], r["numero"], r["fecha"], r["estado"], r["tipo"]))
                nuevos += cur.rowcount
            conn.commit()
        print(f"  [enum] {sub} page {page}: {len(rows)} filas (nuevos {nuevos})", flush=True)
        page += 1
        time.sleep(0.3)
    return nuevos


def download_one(row):
    url, = row
    name = re.sub(r"[^A-Za-z0-9._-]", "_", urllib.parse.unquote(url.rsplit("/", 1)[-1])) or "norma.pdf"
    out = OUTPUT_ROOT / "pdfs" / name
    txt = OUTPUT_ROOT / "txt" / (name + ".txt")
    if out.exists() and out.stat().st_size > 0:
        return (url, "skip", out.stat().st_size)
    data = http_get(url)
    if not data or data[:4] != b"%PDF":
        return (url, "err", 0)
    out.parent.mkdir(parents=True, exist_ok=True); txt.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    try:
        subprocess.run(["pdftotext", "-layout", str(out), str(txt)], capture_output=True, timeout=120)
    except Exception:
        pass
    return (url, "ok", len(data))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()
    conn = init_manifest(OUTPUT_ROOT / "manifest.sqlite3")

    for sub in SUBS:
        enumerate_sub(conn, sub)
    total = conn.execute("SELECT count(*) FROM normas").fetchone()[0]
    print(f"[enum] {total} normas en manifest", flush=True)
    if args.list_only:
        return 0

    rows = conn.execute("SELECT pdf_url FROM normas WHERE downloaded=0").fetchall()
    print(f"[fetch] {len(rows)} normas a descargar (workers={args.workers})", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, r): r for r in rows}
        for fut in as_completed(futs):
            url, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE normas SET downloaded=1, size=? WHERE pdf_url=?", (size, url))
                    conn.commit()
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
