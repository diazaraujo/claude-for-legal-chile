#!/usr/bin/env python3
# std:input [--once] [--workers N] [--source slug]
# std:output reintenta TODOS los pendientes (downloaded=0) de cada data/*/manifest hasta agotarlos
# std:deps stdlib (urllib + sqlite3)
"""
Daemon de persistencia — descarga de pendientes del corpus legal-chile.

Recorre todos los `data/*/manifest.sqlite*`, detecta la tabla y la columna de URL,
y reintenta cada documento `downloaded=0` con:
  - URL-encoding del path (arregla URLs con espacios/acentos → fallas [000]),
  - reintentos con backoff,
  - distinción transitorio vs muerto: 404/410 tras varios pases → `dead=1`
    (no es pendiente, es link muerto), 5xx/timeout/000 → queda pendiente.

Hace pases sucesivos hasta que no quede `downloaded=0 AND dead=0` recuperable, y
en modo loop (sin --once) duerme y vuelve a barrer — persistente.
[[feedback_legal_chile_persistencia_pendientes]]
"""
from __future__ import annotations
import argparse, glob, re, sqlite3, subprocess, sys, time
import urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_LOCK = Lock()
# tabla -> columna de url (manifests heterogéneos)
URLCOLS = {"pdfs": "url", "normas": "pdf_url", "docs": "url", "media": "url", "items": "url",
           "files": "pdf_url", "posts": "link", "dictamenes": "url"}
DEAD_AFTER = 2  # nº de pases con 404/410 antes de marcar dead


def encode_url(u: str) -> str:
    sp = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((sp.scheme, sp.netloc, urllib.parse.quote(sp.path, safe="/%"),
                                    urllib.parse.quote(sp.query, safe="=&%"), ""))


def fetch(u: str, timeout=90):
    """-> (status, bytes|None). status: 'ok'/'404'/'transient'."""
    try:
        req = urllib.request.Request(encode_url(u), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        return ("ok", data)
    except urllib.error.HTTPError as e:
        return ("404", None) if e.code in (404, 410) else ("transient", None)
    except Exception:
        return ("transient", None)


def ensure_cols(c: sqlite3.Connection, table: str):
    cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})")}
    if "downloaded" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN downloaded INTEGER DEFAULT 0")
    if "dead" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN dead INTEGER DEFAULT 0")
    if "miss" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN miss INTEGER DEFAULT 0")
    if "size" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN size INTEGER")
    c.commit()


def detect_tables(c: sqlite3.Connection):
    """Todas las tablas del manifest que matchean URLCOLS (un manifest puede tener varias)."""
    tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    out = []
    for t, col in URLCOLS.items():
        if t in tabs:
            cols = {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
            if col in cols:
                out.append((t, col))
    return out


def download_one(url, out_dir: Path):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", urllib.parse.unquote(url.rsplit("/", 1)[-1])) or "doc.pdf"
    if not name.lower().endswith((".pdf", ".html", ".htm", ".txt", ".xml")):
        name += ".pdf"
    dest = out_dir / "pdfs" / name
    if dest.exists() and dest.stat().st_size > 0:
        return (url, "ok", dest.stat().st_size)
    status, data = fetch(url)
    if status != "ok" or not data:
        return (url, status, 0)
    # aceptar PDF o HTML/XML con cuerpo razonable
    is_pdf = data[:4] == b"%PDF"
    if not is_pdf and len(data) < 600:
        return (url, "transient", 0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    if is_pdf:
        txt = out_dir / "txt" / (name + ".txt")
        txt.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["pdftotext", "-layout", str(dest), str(txt)], capture_output=True, timeout=120)
        except Exception:
            pass
    return (url, "ok", len(data))


def process_source(mpath: Path, workers: int):
    out_dir = mpath.parent
    name = out_dir.name
    c = sqlite3.connect(str(mpath), check_same_thread=False, timeout=60)
    c.execute("PRAGMA busy_timeout=60000")
    tables = detect_tables(c)
    if not tables:
        return (name, 0, 0, 0)
    ok = dead = rem = 0
    for table, col in tables:
        ensure_cols(c, table)
        pend = [r[0] for r in c.execute(
            f"SELECT {col} FROM {table} WHERE COALESCE(downloaded,0)=0 AND COALESCE(dead,0)=0 "
            f"AND {col} IS NOT NULL AND {col} <> ''")]
        if pend:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(download_one, u, out_dir): u for u in pend}
                for fut in as_completed(futs):
                    url, status, size = fut.result()
                    with _LOCK:
                        if status == "ok":
                            c.execute(f"UPDATE {table} SET downloaded=1, size=? WHERE {col}=?", (size, url))
                            ok += 1
                        elif status == "404":
                            c.execute(f"UPDATE {table} SET miss=COALESCE(miss,0)+1 WHERE {col}=?", (url,))
                            c.execute(f"UPDATE {table} SET dead=1 WHERE {col}=? AND COALESCE(miss,0)>=?",
                                      (url, DEAD_AFTER))
                            if c.execute(f"SELECT dead FROM {table} WHERE {col}=?", (url,)).fetchone()[0]:
                                dead += 1
                        c.commit()
        rem += c.execute(
            f"SELECT count(*) FROM {table} WHERE COALESCE(downloaded,0)=0 AND COALESCE(dead,0)=0 "
            f"AND {col} IS NOT NULL AND {col} <> ''").fetchone()[0]
    c.close()
    return (name, ok, dead, rem)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="un solo barrido (sin loop persistente)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--source", help="solo esta fuente (slug de data/<slug>)")
    ap.add_argument("--sleep", type=int, default=300, help="segundos entre barridos en modo loop")
    args = ap.parse_args()

    pass_n = 0
    while True:
        pass_n += 1
        manifests = sorted(m for m in glob.glob(str(DATA / "*/manifest.sqlite*"))
                           if not m.endswith(("-wal", "-shm", "-journal")))
        if args.source:
            manifests = [m for m in manifests if Path(m).parent.name == args.source]
        total_ok = total_rem = total_dead = 0
        print(f"\n===== PASE {pass_n} · {len(manifests)} fuentes =====", flush=True)
        for m in manifests:
            try:
                name, ok, dead, rem = process_source(Path(m), args.workers)
            except Exception as e:
                print(f"  [{Path(m).parent.name}] ERR {e}", flush=True); continue
            total_ok += ok; total_rem += rem; total_dead += dead
            if ok or rem or dead:
                print(f"  [{name:22}] +{ok} bajados · {dead} muertos · {rem} pendientes", flush=True)
        print(f"--- pase {pass_n}: +{total_ok} bajados, {total_dead} muertos, {total_rem} pendientes ---", flush=True)
        if args.once:
            return 0
        if total_ok == 0 and total_rem == 0:
            print("[DONE] no quedan pendientes recuperables", flush=True)
            return 0
        time.sleep(args.sleep)


if __name__ == "__main__":
    sys.exit(main())
