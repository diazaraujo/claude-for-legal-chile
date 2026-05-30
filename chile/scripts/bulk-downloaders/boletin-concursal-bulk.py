#!/usr/bin/env python3
# std:input -
# std:output Registro Concursal completo (JSON+CSV) en data/boletin-concursal/ + manifest
# std:deps stdlib (urllib + json + sqlite3)
"""
Bulk Registro Concursal — Boletín Concursal (Superintendencia de Insolvencia y
Reemprendimiento, Ley N° 20.720).

Fuente (crackeada 2026-05-30): `boletinconcursal.cl/boletin/procedimientos` es un
buscador Spring (form `#publicacionesForm`, CSRF en `_csrf`). Los botones de la
página re-apuntan el `action` del form a distintos endpoints. El que trae TODO es:

  POST /boletin/getRegistroDiarioPublicacionJson   (con _csrf)  -> ~750k registros
  POST /boletin/getRegistroDiarioPublicacionCsv    (con _csrf)  -> mismo en CSV

Cada registro = una PUBLICACIÓN concursal: {tribunal, rolCausa, tipoProcedimiento,
deudorNombre, rut, entePublicador (veedor/liquidador), nombrePublicacion,
fechaPublicacion}. Cubre 2016-02 → hoy. No requiere paginar: el endpoint devuelve
el registro completo de una sola vez.

Flujo: GET la página para sacar el _csrf + cookie de sesión, luego POST al endpoint
JSON, guarda el dump crudo + un .ndjson por registro normalizado para indexar.
Idempotente: re-baja el dump (la fuente no da digest) y reescribe el ndjson.
"""
from __future__ import annotations
import argparse, json, re, sys, time
import http.cookiejar
import urllib.parse, urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/boletin-concursal"
BASE = "https://www.boletinconcursal.cl/boletin"
PAGE = f"{BASE}/procedimientos"
EP_JSON = f"{BASE}/getRegistroDiarioPublicacionJson"
EP_CSV = f"{BASE}/getRegistroDiarioPublicacionCsv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
_CSRF = re.compile(r'name="_csrf"[^>]*value="([^"]+)"')


def _opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA)]
    return op


def fetch_csrf(op) -> str:
    with op.open(PAGE, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    m = _CSRF.search(html)
    if not m:
        raise RuntimeError("no se encontró _csrf en la página")
    return m.group(1)


def post(op, url: str, csrf: str, timeout=180) -> bytes:
    data = urllib.parse.urlencode({"_csrf": csrf}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Origin": "https://www.boletinconcursal.cl",
        "Referer": PAGE,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with op.open(req, timeout=timeout) as r:
        return r.read()


def rec_text(r: dict) -> str:
    """Texto indexable de un registro concursal."""
    return (f"Publicación concursal · {r.get('nombrePublicacion','')}. "
            f"Procedimiento: {r.get('tipoProcedimiento','')}. "
            f"Deudor: {r.get('deudorNombre','')} (RUT {r.get('rut','')}). "
            f"Rol: {r.get('rolCausa','')} · {r.get('tribunal','')}. "
            f"Veedor/Liquidador: {r.get('entePublicador','')}. "
            f"Fecha: {r.get('fechaPublicacion','')}.").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true", help="bajar también el CSV")
    ap.add_argument("--from-file", help="usar un dump JSON ya bajado en vez de re-pedir")
    args = ap.parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    raw_path = OUTPUT_ROOT / "registro-concursal.json"

    if args.from_file:
        raw = Path(args.from_file).read_bytes()
        raw_path.write_bytes(raw)
    else:
        op = _opener()
        csrf = fetch_csrf(op)
        print(f"[csrf] {csrf}", flush=True)
        t0 = time.time()
        raw = post(op, EP_JSON, csrf)
        raw_path.write_bytes(raw)
        print(f"[json] {len(raw)/1e6:.0f} MB en {time.time()-t0:.0f}s -> {raw_path.name}", flush=True)
        if args.csv:
            csv_bytes = post(op, EP_CSV, csrf)
            (OUTPUT_ROOT / "registro-concursal.csv").write_bytes(csv_bytes)
            print(f"[csv] {len(csv_bytes)/1e6:.0f} MB", flush=True)

    recs = json.loads(raw)
    print(f"[parse] {len(recs):,} publicaciones concursales", flush=True)

    # ndjson normalizado para indexar (un objeto por línea, con texto + path estable)
    nd = OUTPUT_ROOT / "txt" / "registro-concursal.ndjson"
    nd.parent.mkdir(parents=True, exist_ok=True)
    fechas = []
    with nd.open("w", encoding="utf-8") as f:
        for i, r in enumerate(recs):
            fp = r.get("fechaPublicacion", "")
            if fp:
                fechas.append(fp)
            rid = f"{r.get('rolCausa','')}_{i}".replace("/", "-")
            f.write(json.dumps({"id": rid, "text": rec_text(r), **r}, ensure_ascii=False) + "\n")
    if fechas:
        def _k(d):  # dd/mm/yyyy -> yyyymmdd
            p = d.split("/")
            return p[2] + p[1] + p[0] if len(p) == 3 else d
        print(f"[rango] {min(fechas, key=_k)} -> {max(fechas, key=_k)}", flush=True)
    print(f"[DONE] {len(recs):,} registros -> {nd}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
