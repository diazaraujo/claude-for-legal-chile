#!/usr/bin/env python3
"""Enriquece los jueces rutificados (confianza ≥ 0.70) con datos Mallas:
identidad/demografía, patrimonio y red familiar (depth 1).

Credenciales por entorno (.env del proyecto chile): MALLAS_USER, MALLAS_PASSWORD.
Solo lectura sobre la API Mallas. Solo se consultan los RUT con confianza 'high'
(gateo anti-homónimo ya aplicado en rutify-jueces.py).

Uso:
  python3 scripts/perfiles/enrich-jueces-mallas.py --probe 12645512   # dump crudo (mapear campos)
  python3 scripts/perfiles/enrich-jueces-mallas.py --limit 20         # prueba
  python3 scripts/perfiles/enrich-jueces-mallas.py                    # todos los high pendientes
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone

import requests
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except Exception:
    pass

OUT = "data/_index/jueces_enriched.sqlite3"
BASE = os.environ.get("MALLAS_URL", "https://api.mallas.unholster.com").rstrip("/")
USER = os.environ.get("MALLAS_USER")
PASS = os.environ.get("MALLAS_PASSWORD") or os.environ.get("MALLAS_PASS")


def login() -> str:
    if not (USER and PASS):
        raise SystemExit("Falta MALLAS_USER / MALLAS_PASSWORD en el entorno (.env).")
    r = requests.post(f"{BASE}/login",
                      data={"username": USER, "password": PASS},
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


def g(tok: str, path: str) -> dict | list | None:
    r = requests.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {tok}"}, timeout=25)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def pick(d: dict, *keys):
    """Primer valor no nulo entre varias claves candidatas (defensivo ante el shape)."""
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", "null"):
            return d[k]
    return None


def to_int(x):
    try:
        return int(float(str(x).replace(".", "").replace("$", "").replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


def parse_persona(p: dict) -> dict:
    if not isinstance(p, dict):
        return {}
    return {
        "edad": to_int(pick(p, "edad", "age")),
        "genero": pick(p, "genero", "sexo", "gender"),
        "estado_civil": pick(p, "estado_civil", "estadoCivil"),
        "n_hijos": to_int(pick(p, "n_hijos", "hijos", "num_hijos")),
        "comuna": pick(p, "comuna", "comuna_residencia"),
        "nse_decil": to_int(pick(p, "decil", "nse_decil", "nse")),
        "patrimonio": to_int(pick(p, "patrimonio", "patrimonio_estimado", "patrimonio_total")),
        "avaluo": to_int(pick(p, "avaluo", "avaluo_total", "avaluo_fiscal")),
        "bienes_raices": to_int(pick(p, "n_bienes_raices", "bienes_raices", "num_bbrr")),
        "conyuge": pick(p, "conyuge", "pareja", "conyuge_nombre"),
    }


def parse_familia(fam) -> list:
    """Aplana depth-1: lista de {rel, nombre, rut, decil}."""
    out = []
    if not fam:
        return out
    rels = fam.get("relationships") if isinstance(fam, dict) else fam
    for n in (rels or []):
        if not isinstance(n, dict):
            continue
        out.append({
            "rel": pick(n, "parentesco", "relacion", "rel", "tipo"),
            "nombre": pick(n, "nombre", "nombre_completo", "name"),
            "rut": pick(n, "rut", "rut_fmt"),
            "decil": to_int(pick(n, "decil", "nse_decil")),
        })
    return [x for x in out if x.get("nombre")][:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--probe", metavar="RUT_CUERPO", help="dump crudo persona+familiares de un RUT")
    args = ap.parse_args()
    tok = login()

    if args.probe:
        c = args.probe
        print(f"=== /unholster/persona/{c} ===")
        print(json.dumps(g(tok, f"/unholster/persona/{c}"), ensure_ascii=False, indent=2)[:2000])
        print(f"\n=== /unholster/familiares/{c}?depth=1 ===")
        print(json.dumps(g(tok, f"/unholster/familiares/{c}?depth=1"), ensure_ascii=False, indent=2)[:2000])
        return

    out = sqlite3.connect(OUT)
    rows = out.execute(
        "SELECT juez_key, rut_cuerpo FROM juez_enriched "
        "WHERE conf_status='high' AND rut_cuerpo IS NOT NULL AND mallas_at IS NULL "
        "ORDER BY confianza DESC").fetchall()
    if args.limit:
        rows = rows[:args.limit]

    now = datetime.now(timezone.utc).isoformat()
    ok = nf = err = 0
    for i, (key, cuerpo) in enumerate(rows, 1):
        try:
            persona = g(tok, f"/unholster/persona/{cuerpo}")
            fam = g(tok, f"/unholster/familiares/{cuerpo}?depth=1")
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  ! error Mallas ({cuerpo}): {e}")
            if "401" in str(e):
                tok = login()
            continue
        if not persona:
            nf += 1
            out.execute("UPDATE juez_enriched SET mallas_at=?, updated_at=? WHERE juez_key=?", (now, now, key))
            continue
        d = parse_persona(persona)
        familia = parse_familia(fam)
        fuentes = json.dumps(["PJUD sentencias", "OpenSearch persona_natural_read", "Mallas Unholster"], ensure_ascii=False)
        out.execute(
            "UPDATE juez_enriched SET edad=?,genero=?,estado_civil=?,n_hijos=?,comuna=?,nse_decil=?,"
            "patrimonio=?,avaluo=?,bienes_raices=?,conyuge=?,familia_json=?,fuentes_json=?,mallas_at=?,updated_at=? "
            "WHERE juez_key=?",
            (d["edad"], d["genero"], d["estado_civil"], d["n_hijos"], d["comuna"], d["nse_decil"],
             d["patrimonio"], d["avaluo"], d["bienes_raices"], d["conyuge"],
             json.dumps(familia, ensure_ascii=False) if familia else None, fuentes, now, now, key))
        ok += 1
        if i % 50 == 0:
            out.commit()
            print(f"  [{i}/{len(rows)}] ok={ok} not_found={nf} err={err}")
    out.commit()
    out.close()
    print(f"\nMALLAS OK · {len(rows)} jueces high · enriquecidos={ok} not_found={nf} err={err}")
    print("→ subir data/_index/jueces_enriched.sqlite3 a enigma (JUECES_DB) y desplegar backend")


if __name__ == "__main__":
    main()
