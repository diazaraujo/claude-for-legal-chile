#!/usr/bin/env python3
"""Genera un resumen profesional por juez (campo `biografia` de juez_enriched)
con qwen2.5:14b en la GPU de enigma (Ollama vía túnel), a partir de su
jurisprudencia real: tribunal, competencias, materias top y tendencia de fallo
laboral/penal. NO inventa: solo redacta sobre las cifras provistas.

Uso:
  OLLAMA_GEN_URL=http://localhost:11435/api/generate \
  python3 scripts/perfiles/summarize-jueces-gpu.py [--limit N] [--workers 4]

Túnel Ollama enigma:  ssh -fN -L 11435:localhost:11434 10.0.0.3
"""
import argparse
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock

import requests

PERF = "data/_index/perfiles.sqlite3"
OUT = "data/_index/jueces_enriched.sqlite3"
OLLAMA = os.environ.get("OLLAMA_GEN_URL", "http://localhost:11435/api/generate")
MODEL = os.environ.get("GEN_MODEL", "qwen2.5:14b")


def pct(x):
    return f"{round(x * 100)}%" if isinstance(x, (int, float)) and 0 <= x <= 1 else (f"{x}" if x is not None else "—")


def materias_str(m):
    try:
        d = json.loads(m) if isinstance(m, str) else m
        if isinstance(d, dict):
            return ", ".join(f"{k} ({v})" for k, v in list(d.items())[:6])
        if isinstance(d, list):
            return ", ".join(str(x) for x in d[:6])
    except Exception:
        pass
    return str(m or "—")


def build_prompt(r):
    (key, juez, n, comp, trib, lab_n, lab_acog, lab_acep, pen_n, pen_cond, pen_dias, materias) = r
    datos = [f"Juez: {juez}"]
    if trib:
        datos.append(f"Tribunal principal: {trib}")
    if comp:
        datos.append(f"Competencias: {comp}")
    datos.append(f"Total de causas falladas: {n:,}")
    datos.append(f"Materias más frecuentes: {materias_str(materias)}")
    if lab_n:
        datos.append(f"Laboral: {lab_n:,} causas, tasa de acogida de demandas {pct(lab_acog)}")
    if pen_n:
        datos.append(f"Penal: {pen_n:,} causas, tasa de condena {pct(pen_cond)}"
                     + (f", pena promedio {round(pen_dias)} días" if pen_dias else ""))
    bloque = "\n".join(datos)
    return (
        "Eres un analista judicial de una consultora. Con los siguientes datos REALES "
        "de un juez chileno, extraídos de sus sentencias públicas, redacta un perfil "
        "profesional de 2 a 3 frases en español de Chile (tuteo formal, tono objetivo de "
        "consultora). Describe su área de especialización y su tendencia de fallo según las "
        "cifras. NO inventes datos que no aparezcan abajo. No uses viñetas ni encabezados; "
        "solo el párrafo.\n\n"
        f"{bloque}\n\nPerfil:"
    )


def generate(prompt):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.3, "num_predict": 220}}
    r = requests.post(OLLAMA, json=body, timeout=180)
    r.raise_for_status()
    return (r.json().get("response") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=int(os.environ.get("GEN_WORKERS", "4")))
    ap.add_argument("--redo", action="store_true", help="regenerar incluso si ya tiene biografia")
    args = ap.parse_args()

    out = sqlite3.connect(OUT)
    out.execute("PRAGMA busy_timeout=120000")
    done = set()
    if not args.redo:
        done = {r[0] for r in out.execute("SELECT juez_key FROM juez_enriched WHERE biografia IS NOT NULL AND biografia<>''")}

    perf = sqlite3.connect(f"file:{PERF}?mode=ro", uri=True)
    rows = perf.execute(
        "SELECT juez_key, juez, n_causas, competencias, tribunal_principal, lab_n, lab_tasa_acogida, "
        "lab_pct_aceptado, pen_n, pen_tasa_condena, pen_dias_pena_prom, materias_top "
        "FROM juez_perfil WHERE juez IS NOT NULL AND n_causas>=1 ORDER BY n_causas DESC").fetchall()
    perf.close()
    rows = [r for r in rows if r[0] not in done]
    if args.limit:
        rows = rows[:args.limit]

    now = datetime.now(timezone.utc).isoformat()
    ok = err = 0
    n_total = len(rows)
    write_lock = Lock()

    def proc(r):
        try:
            return r[0], r[1], generate(build_prompt(r)), None
        except Exception as e:
            return r[0], r[1], None, e

    seen = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(proc, r) for r in rows]
        for f in as_completed(futs):
            key, juez, bio, exc = f.result()
            seen += 1
            if exc is not None or not bio:
                err += 1
                if err <= 3:
                    print(f"  ! error GEN ({juez}): {exc}")
                continue
            with write_lock:
                out.execute(
                    "INSERT INTO juez_enriched(juez_key, nombre, biografia, updated_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(juez_key) DO UPDATE SET biografia=excluded.biografia, updated_at=excluded.updated_at",
                    (key, juez, bio, now))
                ok += 1
                if seen % 25 == 0:
                    out.commit()
                    print(f"  [{seen}/{n_total}] ok={ok} err={err}", flush=True)
    out.commit()
    out.close()
    print(f"\nRESÚMENES GPU OK · {n_total} jueces · generados={ok} err={err}")


if __name__ == "__main__":
    main()
