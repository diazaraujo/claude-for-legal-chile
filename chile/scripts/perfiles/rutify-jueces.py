#!/usr/bin/env python3
"""Rutifica jueces (nombre → RUT) contra OpenSearch `persona_natural_read`.

Porta el MÉTODO icare (no sus credenciales): span_near in_order + match fuzzy +
span_first del primer nombre; confianza = similitud_nombre · 0.85; high ≥ 0.70.
Solo se persiste el match; el endpoint backend decide exponer datos solo si
confianza ≥ 0.70 (gateo anti-homónimo).

Config (todo por entorno / .env del proyecto chile — NO se hardcodea nada):
  OPENSEARCH_URL   default http://localhost:9200   (túnel SSH que abre Antonio)
  OPENSEARCH_INDEX default persona_natural_read
  OPENSEARCH_USER / OPENSEARCH_PASS  (opcional, si el túnel exige basic-auth)

Antonio abre los túneles con `! bash open_tunnels.sh` (el clasificador me bloquea
el SSH al bastión); este cliente corre contra localhost.

Uso:
  python3 scripts/perfiles/rutify-jueces.py --probe        # muestra 1 doc del índice (confirmar campos)
  python3 scripts/perfiles/rutify-jueces.py --limit 50     # prueba
  python3 scripts/perfiles/rutify-jueces.py                # todos los jueces
"""
import argparse
import json
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone

import requests
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except Exception:
    pass

PERF = "data/_index/perfiles.sqlite3"
OUT = "data/_index/jueces_enriched.sqlite3"
OS_URL = os.environ.get("OPENSEARCH_URL", "http://localhost:9200").rstrip("/")
OS_INDEX = os.environ.get("OPENSEARCH_INDEX", "persona_natural_read")
OS_AUTH = (
    (os.environ["OPENSEARCH_USER"], os.environ["OPENSEARCH_PASS"])
    if os.environ.get("OPENSEARCH_USER") else None
)
# Campos del índice (ajustables por entorno si el probe muestra otros nombres).
F_NOMBRE = os.environ.get("OS_FIELD_NOMBRE", "nombre_completo")
F_RUT = os.environ.get("OS_FIELD_RUT", "rut")
CONF_HIGH = 0.70

SCHEMA = """
CREATE TABLE IF NOT EXISTS juez_enriched(
  juez_key TEXT PRIMARY KEY,
  nombre TEXT, rut_cuerpo TEXT, rut_fmt TEXT,
  confianza REAL, conf_status TEXT,
  edad INTEGER, genero TEXT, estado_civil TEXT, n_hijos INTEGER,
  comuna TEXT, nse_decil INTEGER,
  patrimonio INTEGER, bienes_raices INTEGER, avaluo INTEGER,
  conyuge TEXT, familia_json TEXT, biografia TEXT, fuentes_json TEXT,
  rutificado_at TEXT, mallas_at TEXT, updated_at TEXT
);
"""


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper()).strip()


def dv(cuerpo: str) -> str:
    r = [int(c) for c in reversed(cuerpo)]
    s = sum(d * f for d, f in zip(r, (2, 3, 4, 5, 6, 7) * 3))
    m = 11 - (s % 11)
    return "0" if m == 11 else "K" if m == 10 else str(m)


def fmt_rut(cuerpo: str) -> str:
    c = f"{int(cuerpo):,}".replace(",", ".")
    return f"{c}-{dv(cuerpo)}"


def query_os(nombre_norm: str) -> dict | None:
    """Devuelve {rut_cuerpo, confianza, nombre_match} del mejor hit, o None."""
    toks = nombre_norm.split()
    if len(toks) < 2:
        return None
    body = {
        "size": 3,
        "query": {
            "bool": {
                "should": [
                    {"span_near": {"clauses": [{"span_term": {F_NOMBRE: t.lower()}} for t in toks],
                                   "slop": 2, "in_order": True, "boost": 4.0}},
                    {"match": {F_NOMBRE: {"query": nombre_norm, "fuzziness": "AUTO", "operator": "and", "boost": 2.0}}},
                    {"span_first": {"match": {"span_term": {F_NOMBRE: toks[0].lower()}}, "end": 2, "boost": 1.0}},
                ],
                "minimum_should_match": 1,
            }
        },
    }
    r = requests.post(f"{OS_URL}/{OS_INDEX}/_search", json=body, auth=OS_AUTH, timeout=15)
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    if not hits:
        return None
    top = hits[0]
    src = top.get("_source", {})
    cand = norm(src.get(F_NOMBRE, ""))
    # similitud por tokens (Jaccard sobre el set de tokens) · escalada 0.85 como icare
    a, b = set(toks), set(cand.split())
    sim = len(a & b) / max(1, len(a | b))
    conf = round(sim * 0.85 + (0.15 if cand.startswith(toks[0]) else 0), 3)
    rut = re.sub(r"[^0-9kK]", "", str(src.get(F_RUT, "")).split("-")[0])
    if not rut.isdigit():
        return None
    return {"rut_cuerpo": rut, "confianza": min(conf, 0.99), "nombre_match": cand}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--probe", action="store_true", help="imprime un doc del índice y sale")
    args = ap.parse_args()

    if args.probe:
        r = requests.post(f"{OS_URL}/{OS_INDEX}/_search", json={"size": 1, "query": {"match_all": {}}}, auth=OS_AUTH, timeout=15)
        print(f"OpenSearch {OS_URL}/{OS_INDEX} → HTTP {r.status_code}")
        hits = r.json().get("hits", {}).get("hits", [])
        if hits:
            print("Campos del _source:")
            print(json.dumps(hits[0]["_source"], ensure_ascii=False, indent=2)[:1500])
            print(f"\n→ ajustar OS_FIELD_NOMBRE / OS_FIELD_RUT si difieren de '{F_NOMBRE}' / '{F_RUT}'")
        return

    out = sqlite3.connect(OUT)
    out.executescript(SCHEMA)
    done = {r[0] for r in out.execute("SELECT juez_key FROM juez_enriched WHERE rutificado_at IS NOT NULL")}

    perf = sqlite3.connect(f"file:{PERF}?mode=ro", uri=True)
    jueces = [(k, n) for k, n in perf.execute(
        "SELECT juez_key, juez FROM juez_perfil WHERE juez IS NOT NULL AND n_causas>=1 ORDER BY n_causas DESC")]
    perf.close()
    if args.limit:
        jueces = jueces[:args.limit]

    now = datetime.now(timezone.utc).isoformat()
    hi = mid = lo = err = skip = 0
    for i, (key, nombre) in enumerate(jueces, 1):
        if key in done:
            skip += 1
            continue
        nn = norm(nombre)
        try:
            m = query_os(nn)
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  ! error OS ({nombre}): {e}")
            continue
        conf = m["confianza"] if m else 0.0
        status = "high" if conf >= CONF_HIGH else "mid" if conf >= 0.5 else "low"
        hi += status == "high"; mid += status == "mid"; lo += status == "low"
        out.execute(
            "INSERT INTO juez_enriched(juez_key,nombre,rut_cuerpo,rut_fmt,confianza,conf_status,fuentes_json,rutificado_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(juez_key) DO UPDATE SET "
            "rut_cuerpo=excluded.rut_cuerpo,rut_fmt=excluded.rut_fmt,confianza=excluded.confianza,"
            "conf_status=excluded.conf_status,rutificado_at=excluded.rutificado_at,updated_at=excluded.updated_at",
            (key, nombre, m["rut_cuerpo"] if m else None,
             fmt_rut(m["rut_cuerpo"]) if m else None, conf, status,
             json.dumps(["PJUD sentencias", "OpenSearch persona_natural_read"], ensure_ascii=False),
             now, now))
        if i % 100 == 0:
            out.commit()
            print(f"  [{i}/{len(jueces)}] high={hi} mid={mid} low={lo} err={err}")
    out.commit()
    out.close()
    print(f"\nRUTIFICACIÓN OK · {len(jueces)} jueces · high={hi} mid={mid} low={lo} err={err} skip={skip}")
    print(f"→ siguiente: python3 scripts/perfiles/enrich-jueces-mallas.py  (solo enriquece los high)")


if __name__ == "__main__":
    main()
