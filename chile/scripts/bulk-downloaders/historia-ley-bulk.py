#!/usr/bin/env python3
# std:input [--from-year N] [--to-year N] [--workers N]
# std:output Proyectos de ley + tramitación (Historia de la Ley) en data/historia-ley/ + manifest
# std:deps stdlib (urllib + sqlite3)
"""
Bulk Historia de la Ley — proyectos de ley y su tramitación legislativa, gap
detectado por deep-research (31-may): captura la *intención* detrás de cada ley.
[[reference_legal_chile_fuentes_faltantes]]

Acceso (WSDL real, verificado): web service legislativo de la Cámara
  https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx
- retornarMocionesXAnno?prmAnno=<año>  → proyectos de iniciativa parlamentaria
- retornarMensajesXAnno?prmAnno=<año>  → proyectos de iniciativa del Ejecutivo
  (ambos devuelven XML con los <NUMERO> de boletín, formato NNNNN-NN)
- retornarProyectoLey?prmNumeroBoletin=<boletín>  → tramitación completa del proyecto

Enumera boletines por año (mociones+mensajes), luego baja el detalle de cada uno.
Idempotente por boletín. Guarda el XML crudo (lo embebe el pipeline después).
"""
from __future__ import annotations
import argparse, re, sqlite3, ssl, sys, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = _REPO_ROOT / "chile/data/historia-ley"
WS = "https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_LOCK = Lock()
_STATS = {"ok": 0, "skip": 0, "err": 0}
_BOLETIN = re.compile(r"\b(\d{3,5}-\d{2})\b")  # formato boletín NNNNN-NN


def http(url, t=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=t, context=_CTX) as r:
            return r.status, r.read()
    except Exception:
        return 0, b""


def init_db():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(OUT / "manifest.sqlite3"), check_same_thread=False, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS proyectos (boletin TEXT PRIMARY KEY, anio INTEGER, "
              "tipo TEXT, downloaded INTEGER DEFAULT 0, size INTEGER)")
    c.commit()
    return c


def enumerate_year(c, year):
    nuevos = 0
    for metodo, tipo in [("retornarMocionesXAnno", "mocion"), ("retornarMensajesXAnno", "mensaje")]:
        s, b = http(f"{WS}/{metodo}?prmAnno={year}")
        if s != 200 or not b:
            continue
        bols = set(_BOLETIN.findall(b.decode("utf-8", "replace")))
        with _LOCK:
            for bol in bols:
                nuevos += c.execute("INSERT OR IGNORE INTO proyectos(boletin,anio,tipo) VALUES (?,?,?)",
                                    (bol, year, tipo)).rowcount
            c.commit()
    n = c.execute("SELECT count(*) FROM proyectos WHERE anio=?", (year,)).fetchone()[0]
    print(f"  [enum] {year}: {n} proyectos", flush=True)
    return nuevos


def download_one(boletin):
    dest = OUT / "xml" / f"{boletin}.xml"
    if dest.exists() and dest.stat().st_size > 200:
        return (boletin, "skip", dest.stat().st_size)
    s, b = http(f"{WS}/retornarProyectoLey?prmNumeroBoletin={boletin}")
    if s != 200 or len(b) < 200:  # 222b = respuesta vacía
        return (boletin, "err", 0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b)
    # texto plano del XML para indexar
    txt = OUT / "txt" / f"{boletin}.txt"
    txt.parent.mkdir(parents=True, exist_ok=True)
    plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b.decode("utf-8", "replace"))).strip()
    txt.write_text(plain, encoding="utf-8")
    return (boletin, "ok", len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-year", type=int, default=1990)
    ap.add_argument("--to-year", type=int, default=2026)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    c = init_db()
    print("[FASE 1] Enumerando proyectos de ley por año…", flush=True)
    for year in range(args.to_year, args.from_year - 1, -1):
        enumerate_year(c, year)
        time.sleep(0.2)
    total = c.execute("SELECT count(*) FROM proyectos").fetchone()[0]
    print(f"[enum] {total} proyectos en manifest", flush=True)
    rows = [r[0] for r in c.execute("SELECT boletin FROM proyectos WHERE downloaded=0")]
    print(f"[FASE 2] Descargando tramitación de {len(rows)}…", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_one, b): b for b in rows}
        for fut in as_completed(futs):
            bol, st, sz = fut.result()
            _STATS[st if st in _STATS else "err"] += 1
            if st in ("ok", "skip"):
                with _LOCK:
                    c.execute("UPDATE proyectos SET downloaded=1, size=? WHERE boletin=?", (sz, bol)); c.commit()
            done += 1
            if done % 500 == 0:
                print(f"  {done}/{len(rows)} · {_STATS}", flush=True)
    print(f"[DONE] {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
