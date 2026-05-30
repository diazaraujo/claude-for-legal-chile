#!/usr/bin/env python3
# std:input --rut <RUT> | --nombre <texto> | --rol <C-1234-2024> [--tribunal <txt>]
# std:output procedimientos concursales (Ley 20.720) desde el Registro del Boletín Concursal
# std:deps stdlib (sqlite3)
"""
Consulta el Registro Concursal (Boletín Concursal, Superir, Ley N° 20.720) ya
indexado en `data/_index/new-sources.fts.sqlite3` (tabla estructurada `concursal`).

747k publicaciones, 2014-10 → hoy. Un procedimiento = (rol, tribunal); cada fila
es una PUBLICACIÓN dentro de ese procedimiento. La última publicación es la mejor
señal del estado actual del procedimiento.

Uso:
  query.py --rut 17994454-5
  query.py --nombre "CAROCA POBLETE"
  query.py --rol C-418-2026 [--tribunal "Villa Alemana"]
  query.py --rut 17994454-5 --json
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data/_index/new-sources.fts.sqlite3"


def _ddmmyyyy_key(d: str) -> str:
    p = (d or "").split("/")
    return p[2] + p[1] + p[0] if len(p) == 3 else (d or "")


def norm_rut(r: str) -> str:
    return r.replace(".", "").replace(" ", "").upper().strip()


def connect() -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def by_filter(c, where: str, params: tuple):
    rows = c.execute(
        f"SELECT rol, tipo, deudor, rut, ente, publicacion, tribunal, fecha "
        f"FROM concursal WHERE {where}", params).fetchall()
    # agrupar por procedimiento (rol + tribunal)
    procs: dict = {}
    for r in rows:
        k = (r["rol"], r["tribunal"])
        p = procs.setdefault(k, {"rol": r["rol"], "tribunal": r["tribunal"],
                                 "tipo": r["tipo"], "deudor": r["deudor"], "rut": r["rut"],
                                 "publicaciones": []})
        p["publicaciones"].append({"fecha": r["fecha"], "publicacion": r["publicacion"], "ente": r["ente"]})
    out = []
    for p in procs.values():
        pubs = sorted(p["publicaciones"], key=lambda x: _ddmmyyyy_key(x["fecha"]))
        p["publicaciones"] = pubs
        p["n_pub"] = len(pubs)
        p["primera"] = pubs[0]["fecha"] if pubs else None
        p["ultima"] = pubs[-1]["fecha"] if pubs else None
        p["estado_aprox"] = pubs[-1]["publicacion"] if pubs else None  # última publicación ≈ estado
        out.append(p)
    out.sort(key=lambda p: _ddmmyyyy_key(p["ultima"] or ""), reverse=True)
    return out


def render(procs, query_desc: str):
    if not procs:
        print(f"Sin procedimientos concursales para {query_desc} en el Registro del Boletín Concursal.")
        print("(Registro cubre 2014-10 → hoy. Ausencia de resultados = no hay publicación registrada, "
              "no necesariamente ausencia de procedimiento muy reciente o reservado.)")
        return
    print(f"{len(procs)} procedimiento(s) concursal(es) para {query_desc}:\n")
    for p in procs:
        print(f"● Rol {p['rol']} · {p['tribunal']}")
        print(f"  Deudor: {p['deudor']} (RUT {p['rut']})")
        print(f"  Tipo: {p['tipo']}")
        print(f"  Publicaciones: {p['n_pub']} ({p['primera']} → {p['ultima']})")
        print(f"  Última publicación (≈ estado): {p['estado_aprox']}")
        if p["n_pub"] <= 12:
            for pub in p["publicaciones"]:
                print(f"     {pub['fecha']}  {pub['publicacion']}  · {pub['ente']}")
        else:
            for pub in p["publicaciones"][:3]:
                print(f"     {pub['fecha']}  {pub['publicacion']}")
            print(f"     … {p['n_pub']-6} más …")
            for pub in p["publicaciones"][-3:]:
                print(f"     {pub['fecha']}  {pub['publicacion']}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--rut")
    g.add_argument("--nombre")
    g.add_argument("--rol")
    ap.add_argument("--tribunal")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not DB.exists():
        print(f"[error] no existe el índice {DB}", file=sys.stderr); return 2
    c = connect()
    if args.rut:
        procs = by_filter(c, "rut = ?", (norm_rut(args.rut),)); desc = f"RUT {args.rut}"
    elif args.nombre:
        procs = by_filter(c, "deudor LIKE ?", (f"%{args.nombre.upper()}%",)); desc = f"«{args.nombre}»"
    else:
        if args.tribunal:
            procs = by_filter(c, "rol = ? AND tribunal LIKE ?", (args.rol, f"%{args.tribunal}%"))
        else:
            procs = by_filter(c, "rol = ?", (args.rol,))
        desc = f"Rol {args.rol}"
    if args.json:
        print(json.dumps(procs, ensure_ascii=False, indent=2))
    else:
        render(procs, desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
