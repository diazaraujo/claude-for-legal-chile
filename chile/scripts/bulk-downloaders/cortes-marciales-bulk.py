#!/usr/bin/env python3
# std:input -
# std:output PDFs sentencias Cortes/Juzgados Militares + manifest
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download Cortes Marciales y Juzgados Militares de Chile.

Portal: cortemarcial.cl (WordPress + plugin wp-file-download).

Cubre 7 catid:
  7   = Corte Marcial (Ejército)
  1225= Ministra en Visita Extraordinaria
  8   = 1º Juzgado Militar de Antofagasta
  9   = 2º Juzgado Militar de Santiago
  10  = 3º Juzgado Militar de Valdivia
  12  = 4º Juzgado Militar de Coyhaique
  13  = 5º Juzgado Militar de Punta Arenas

API: POST a admin-ajax.php?action=wpfd&task=search.display con
{catid, q, ftags, cfrom, cto, ufrom, uto, limit=10000}

Devuelve tabla HTML. Cada <tr> tiene link a PDF en formato
/download/{catid}/{slug}/{file_id}/{rol}.pdf más metadata
(rol, materia, fecha resolución, tribunal).

Fase 1 (--list-only): enumera y guarda manifest.
Fase 2: descarga PDFs en paralelo.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/cortes-marciales"

AJAX_URL = ("https://www.cortemarcial.cl/wp-admin/admin-ajax.php"
            "?juwpfisadmin=false&action=wpfd&task=search.display")
UA = "claude-legal-chile/0.8 bulk-cortes-marciales"

CATEGORIES = [
    ("7",   "corte-marcial-ejercito"),
    ("1225","ministra-en-visita-extraordinaria"),
    ("8",   "1jm-antofagasta"),
    ("9",   "2jm-santiago"),
    ("10",  "3jm-valdivia"),
    ("12",  "4jm-coyhaique"),
    ("13",  "5jm-punta-arenas"),
]

_STATS = {"pdfs_ok": 0, "pdfs_skip": 0, "pdfs_err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias ("
        "file_id INTEGER PRIMARY KEY, catid TEXT, tribunal TEXT, "
        "rol TEXT, materia TEXT, fecha TEXT, title TEXT, url TEXT, "
        "downloaded INTEGER DEFAULT 0, size INTEGER)"
    )
    conn.commit()
    return conn


def fetch_list(catid: str) -> str:
    data = {"catid": catid, "q": "", "ftags": "", "cfrom": "", "cto": "",
            "ufrom": "", "uto": "", "limit": "10000"}
    req = urllib.request.Request(
        AJAX_URL,
        data=urllib.parse.urlencode(data).encode(),
        headers={"User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "Referer": "https://www.cortemarcial.cl/busqueda-de-sentencias/"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode("utf-8", "replace")


def parse_rows(html: str, catid: str, tribunal_label: str):
    """Yields dict por cada sentencia en la tabla."""
    # Cada <tr> contiene: link PDF, rol, materia, fecha
    # Extraer bloques tr
    trs = re.findall(r"<tr>([\s\S]+?)</tr>", html)
    for tr in trs[1:]:  # primer tr es thead (lo ignoramos)
        # PDF
        m_pdf = re.search(r'href="(https?://[^"]+/download/(\d+)/([^/]+)/(\d+)/([^"]+\.pdf))"', tr)
        if not m_pdf:
            continue
        url = m_pdf.group(1)
        cat_url = m_pdf.group(2)
        slug = m_pdf.group(3)
        file_id = int(m_pdf.group(4))
        filename = m_pdf.group(5)
        # Texto entre celdas <td>
        tds = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr)
        # Quitar tags
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
        cells = [clean(td) for td in tds]
        # estructura típica: [tipo+nombre, abrir, rol, materia, fecha, tribunal]
        rol = cells[2] if len(cells) > 2 else ""
        materia = cells[3] if len(cells) > 3 else ""
        fecha = cells[4] if len(cells) > 4 else ""
        title = cells[0][:200] if cells else ""
        yield {
            "file_id": file_id, "catid": catid, "tribunal": tribunal_label,
            "rol": rol, "materia": materia, "fecha": fecha,
            "title": title, "url": url, "filename": filename,
        }


def enumerate_all(conn: sqlite3.Connection) -> int:
    total = 0
    for catid, tribunal in CATEGORIES:
        print(f"  catid={catid} ({tribunal}) → fetching listado...", flush=True)
        html = fetch_list(catid)
        n = 0
        for row in parse_rows(html, catid, tribunal):
            conn.execute(
                "INSERT OR IGNORE INTO sentencias"
                "(file_id, catid, tribunal, rol, materia, fecha, title, url) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (row["file_id"], row["catid"], row["tribunal"], row["rol"],
                 row["materia"], row["fecha"], row["title"], row["url"]),
            )
            n += 1
        conn.commit()
        print(f"     {n} sentencias", flush=True)
        total += n
    return total


def download_one(row: tuple, out_dir: Path) -> tuple[int, bool, int]:
    file_id, url, catid, tribunal = row
    fname = url.rsplit("/", 1)[-1]
    # Saneamiento básico de filename
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", fname)
    subdir = out_dir / tribunal
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{file_id}_{safe}"
    if dest.exists() and dest.stat().st_size > 1024:
        with _LOCK:
            _STATS["pdfs_skip"] += 1
        return (file_id, True, dest.stat().st_size)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
    except Exception:
        with _LOCK:
            _STATS["pdfs_err"] += 1
        return (file_id, False, 0)
    if len(body) < 200:
        with _LOCK:
            _STATS["pdfs_err"] += 1
        return (file_id, False, 0)
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(body)
    tmp.rename(dest)
    with _LOCK:
        _STATS["pdfs_ok"] += 1
        _STATS["bytes"] += len(body)
    return (file_id, True, len(body))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUTPUT_ROOT))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== Cortes Marciales bulk ===", flush=True)
    print(f"output: {out}  workers: {args.workers}", flush=True)
    print(f"\nFase 1: enumerando 7 tribunales...", flush=True)
    t0 = time.time()
    n = enumerate_all(conn)
    print(f"  total enumerado: {n}  ({time.time()-t0:.1f}s)", flush=True)

    if args.list_only:
        return 0

    rows = conn.execute(
        "SELECT file_id, url, catid, tribunal FROM sentencias WHERE downloaded=0"
    ).fetchall()
    print(f"\nFase 2: descargando {len(rows)} PDFs...", flush=True)

    t0 = time.time()
    last_print = t0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(download_one, r, out) for r in rows]
        done = 0
        for fut in as_completed(futs):
            file_id, ok, size = fut.result()
            if ok:
                conn.execute("UPDATE sentencias SET downloaded=1, size=? WHERE file_id=?",
                             (size, file_id))
            done += 1
            if done % 50 == 0 or time.time() - last_print > 15:
                conn.commit()
                with _LOCK:
                    s = dict(_STATS)
                print(f"  done={done}/{len(rows)} ok={s['pdfs_ok']} "
                      f"skip={s['pdfs_skip']} err={s['pdfs_err']} "
                      f"MB={s['bytes']/1e6:.1f}", flush=True)
                last_print = time.time()
    conn.commit()
    print(f"\n[DONE] {time.time()-t0:.0f}s | {dict(_STATS)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
