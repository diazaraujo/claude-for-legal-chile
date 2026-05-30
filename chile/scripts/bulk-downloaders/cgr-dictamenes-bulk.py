#!/usr/bin/env python3
# std:input -
# std:output dictámenes CGR (metadata + materia + cuerpo) en data/cgr-dictamenes/ + manifest
# std:deps stdlib (urllib + sqlite3 + html.parser) — sin Zyte
"""
Bulk download dictámenes CGR — jurisprudencia administrativa de la Contraloría.

Fuente: base Lotus Domino pública `DictamenesGeneralesMunicipales.nsf`. El
buscador apibusca/lex va detrás de IBM WebSEAL y 503-ea a IP extranjera, pero el
**form Domino principal responde directo** (verificado 2026-05-29), así que NO se
necesita Zyte.

Contrato (verificado):
- Enumerar (GET): `FormConsultaWeb2k?OpenForm&FechaDesde=DD-MM-YYYY&
  FechaHasta=DD-MM-YYYY&porPagina=500&desde=<offset>&Orden=2&
  HaPresionadoBotonBuscar=1` → HTML con, por dictamen,
  `cgrDetalleDictamenNVDA?OpenForm&UNID=<32hex>` + identificador `E<num>N<yy>`.
  `desde` es el offset 1-based de paginación; el texto "Se han encontrado N
  dictámenes" da el total por ventana.
- Detalle (GET): `cgrDetalleDictamenNVDA?OpenForm&UNID=<UNID>` → metadata
  (ID, número, fecha, carácter, descriptores, fuentes legales, dictámenes
  relacionados, MATERIA) + cuerpo. Intentamos también `0/<UNID>?OpenDocument`
  por el cuerpo completo.

Estrategia: barrido por ventanas mensuales (el form filtra por fecha) desde hoy
hacia atrás hasta `--desde-anio` (default 1990), paginando cada ventana. Reverse
cronológico: si se corta, lo más reciente queda primero.

Fase 1 (--list-only): enumera UNIDs a manifest sin bajar detalle.
Fase 2: baja el detalle de los pendientes.
Idempotente vía manifest (downloaded flag).
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/cgr-dictamenes"
NSF = ("https://www.contraloria.cl/appinf/LegisJuri/"
       "DictamenesGeneralesMunicipales.nsf")
# Full-text por número (E<num>N<yy>): /html (texto) y /pdf (oficial). NO bloqueado.
PDFBUSCADOR = "https://www.contraloria.cl/pdfbuscador/dictamenes"
UA = "claude-legal-chile/0.8 cgr-dictamenes (research corpus)"
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0, "empty": 0}

_UNID_RE = re.compile(
    r"cgrDetalleDictamenNVDA\?OpenForm&UNID=([0-9A-F]{32})", re.I)
_TOTAL_RE = re.compile(r"encontrado\s+([\d.]+)\s+dict", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def http_get_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_get(url: str, timeout: int = 60) -> str:
    return http_get_bytes(url, timeout).decode("utf-8", "replace")


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dictamenes ("
        "unid TEXT PRIMARY KEY, numero TEXT, anio INTEGER, "
        "ventana TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    conn.commit()
    return conn


def enumerate_window(conn, fdesde: str, fhasta: str, etiqueta: str,
                     per_page: int = 500) -> int:
    """Pagina una ventana de fechas y registra UNIDs. Devuelve nº nuevos."""
    nuevos, desde = 0, 1
    while True:
        url = (f"{NSF}/FormConsultaWeb2k?OpenForm"
               f"&TextoLibre=&NumeroDictamen=&Materia="
               f"&FechaDesde={fdesde}&FechaHasta={fhasta}"
               f"&porPagina={per_page}&desde={desde}&Orden=2"
               f"&HaPresionadoBotonBuscar=1")
        try:
            html = http_get(url)
        except Exception as e:
            print(f"  [enum] err {etiqueta} desde={desde}: {e}", flush=True)
            break
        unids = list(dict.fromkeys(_UNID_RE.findall(html)))
        if desde == 1:
            mt = _TOTAL_RE.search(html.replace(".", ""))
            total = int(mt.group(1)) if mt else len(unids)
            print(f"  [enum] {etiqueta}: total={total}", flush=True)
        if not unids:
            break
        with _LOCK:
            for u in unids:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO dictamenes(unid, ventana) VALUES (?,?)",
                    (u, etiqueta))
                nuevos += cur.rowcount
            conn.commit()
        if len(unids) < per_page:
            break
        desde += per_page
        time.sleep(0.3)
    return nuevos


def parse_detalle(html: str) -> tuple[str, dict]:
    """Devuelve (texto_plano_limpio, metadata mínima)."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html,
                  flags=re.S | re.I)
    text = _TAG_RE.sub(" ", body)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = _WS_RE.sub(" ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    meta = {}
    m = re.search(r"N[úu]mero Dictamen\s*([A-Z0-9]+)", text)
    if m:
        meta["numero"] = m.group(1)
    m = re.search(r"Fecha\s*(\d{2}-\d{2}-\d{4})", text)
    if m:
        meta["fecha"] = m.group(1)
    return text, meta


def download_one(unid: str) -> tuple[str, str, int]:
    out_dir = OUTPUT_ROOT / "dictamenes"
    out_path = out_dir / f"{unid}.txt"
    if out_path.exists() and out_path.stat().st_size > 200:
        return (unid, "skip", out_path.stat().st_size)
    try:
        det = http_get(f"{NSF}/cgrDetalleDictamenNVDA?OpenForm&UNID={unid}")
    except Exception:
        return (unid, "err", 0)
    text, meta = parse_detalle(det)
    numero = meta.get("numero", "")
    # cuerpo COMPLETO vía pdfbuscador por número (texto + PDF oficial)
    if numero:
        try:
            full, _ = parse_detalle(http_get(f"{PDFBUSCADOR}/{numero}/html"))
            if len(full) > len(text):
                text = full
        except Exception:
            pass
        try:
            pdf = http_get_bytes(f"{PDFBUSCADOR}/{numero}/pdf")
            if pdf[:4] == b"%PDF":
                pdir = OUTPUT_ROOT / "pdfs"
                pdir.mkdir(parents=True, exist_ok=True)
                (pdir / f"{numero}.pdf").write_bytes(pdf)
        except Exception:
            pass
    if len(text) < 200:
        return (unid, "empty", len(text))
    out_dir.mkdir(parents=True, exist_ok=True)
    header = f"# Dictamen CGR {numero} ({meta.get('fecha','')})\n"
    header += f"<!-- UNID {unid} · num {numero} · fuente CGR -->\n\n"
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(header + text, encoding="utf-8")
    tmp.rename(out_path)
    return (unid, "ok", out_path.stat().st_size)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio-tope", type=int, required=True,
                    help="año del mes más reciente a barrer (ej 2026)")
    ap.add_argument("--mes-tope", type=int, required=True,
                    help="mes más reciente a barrer (1-12)")
    ap.add_argument("--desde-anio", type=int, default=1990)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    conn = init_manifest(OUTPUT_ROOT / "manifest.sqlite3")

    # Fase 1: enumerar por ventanas mensuales, reverse cronológico (más reciente
    # primero, así si se corta queda el material de mayor valor).
    y, m = args.anio_tope, args.mes_tope
    while y > args.desde_anio or (y == args.desde_anio and m >= 1):
        last = [31, 29 if y % 4 == 0 and (y % 100 or not y % 400) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        fd, fh = f"01-{m:02d}-{y}", f"{last:02d}-{m:02d}-{y}"
        enumerate_window(conn, fd, fh, f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    total = conn.execute("SELECT count(*) FROM dictamenes").fetchone()[0]
    print(f"[enum] manifest: {total} dictámenes UNID", flush=True)
    if args.list_only:
        return 0

    # Fase 2: bajar detalle de los pendientes
    rows = [r[0] for r in conn.execute(
        "SELECT unid FROM dictamenes WHERE downloaded=0").fetchall()]
    print(f"[fetch] pendientes: {len(rows)} (workers={args.workers})", flush=True)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, u): u for u in rows}
        for fut in as_completed(futs):
            unid, status, size = fut.result()
            _STATS[status if status in _STATS else "err"] += 1
            if status == "ok":
                with _LOCK:
                    conn.execute("UPDATE dictamenes SET downloaded=1, size=? "
                                 "WHERE unid=?", (size, unid))
                    conn.commit()
            done += 1
            if done % 50 == 0:
                el = time.time() - t0
                rate = done / el if el else 0
                eta = (len(rows) - done) / rate / 60 if rate else 0
                print(f"  done={done}/{len(rows)} {_STATS} "
                      f"rate={rate:.1f}/s ETA={eta:.0f}min", flush=True)
    print(f"[DONE] {time.time()-t0:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
