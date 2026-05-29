#!/usr/bin/env python3
"""Indexa sentencias PJUD (juris.pjud.cl) en el FTS `docs`.

Lee las páginas `data/pjud/{buscador}/page-*.json.gz` (Solr JSON, 100
sentencias c/u) producidas por scrape-pjud-juris.py, arma para cada
sentencia un encabezado con metadata (rol, caratulado, corte, sala,
fecha, recurso, resultado, ministros) + el `texto_sentencia` limpio, y
lo inserta en `docs` + `docs_meta`.

path sintético: `pjud/{buscador}/{id}.txt` (id = Solr id, único).
source: `pjud-{slug}` (ej. pjud-corte-suprema).

Idempotente: skip si el path ya está en docs_meta. Después, correr
build-considerandos-index.py --sources pjud-corte-suprema para particionar
en considerandos, y los builders de embeddings.

Uso:
  python3 index-pjud-sentencias.py --buscador Corte_Suprema
  python3 index-pjud-sentencias.py --buscador Corte_Suprema --max 200
"""
from __future__ import annotations
import argparse
import glob
import gzip
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
PJUD_ROOT = _REPO_ROOT / "chile/data/pjud"
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"

_TAG_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG_ANY = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")
_NL = re.compile(r"\n{3,}")


def clean_text(html: str) -> str:
    t = _TAG_BR.sub("\n", html or "")
    t = _TAG_ANY.sub("", t)
    t = _WS.sub(" ", t)
    t = _NL.sub("\n\n", t)
    return t.strip()


def build_content(s: dict) -> str:
    rol = s.get("rol_era_sup_s") or s.get("rol_sup_s") or ""
    fecha = (s.get("fec_sentencia_sup_dt") or "")[:10]
    mins = s.get("gls_ministro_ss") or []
    if isinstance(mins, str):
        mins = [mins]
    def _clean_persona(v: str) -> str:
        # Filtra placeholders que no aportan info ("no identificado", "sin relator", etc).
        if not v:
            return ""
        low = v.strip().lower()
        if "no identificado" in low or low.startswith("sin ") or low in ("", "-", "n/a"):
            return ""
        return v.strip()
    redactor = _clean_persona(s.get("gls_redactor_s") or "")
    relator = _clean_persona(s.get("gls_relator_s") or "")
    header_lines = [
        f"Rol: {rol}" if rol else "",
        f"Caratulado: {s.get('caratulado_s','')}" if s.get("caratulado_s") else "",
        f"Corte: {s.get('gls_corte_s','')}" if s.get("gls_corte_s") else "",
        f"Sala: {s.get('gls_sala_sup_s','')}" if s.get("gls_sala_sup_s") else "",
        f"Fecha: {fecha}" if fecha else "",
        f"Recurso: {s.get('gls_tip_recurso_sup_s','')}" if s.get("gls_tip_recurso_sup_s") else "",
        f"Resultado: {s.get('resultado_recurso_sup_s','')}" if s.get("resultado_recurso_sup_s") else "",
        f"Ministros: {', '.join(mins)}" if mins else "",
        f"Redactor: {redactor}" if redactor else "",
        f"Relator: {relator}" if relator else "",
    ]
    header = "\n".join(h for h in header_lines if h)
    body = clean_text(s.get("texto_sentencia", ""))
    return (header + "\n\n" + body).strip()


def iter_docs(buscador_dir: Path):
    for page in sorted(glob.glob(str(buscador_dir / "page-*.json.gz"))):
        try:
            data = json.loads(gzip.open(page).read())
        except Exception:
            continue
        docs = data.get("response", {}).get("docs") or data.get("docs") or []
        for s in docs:
            yield s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--buscador", default="Corte_Suprema")
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--source", default="")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--commit-every", type=int, default=2000)
    ap.add_argument("--reset", action="store_true",
                    help="Borra docs y docs_meta de este source antes de re-indexar")
    args = ap.parse_args()

    source = args.source or ("pjud-" + args.buscador.lower().replace("_", "-"))
    bdir = PJUD_ROOT / args.buscador
    if not bdir.is_dir():
        print(f"no existe {bdir}")
        return 1

    conn = sqlite3.connect(args.db, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=120000")
    if args.reset:
        n_d = conn.execute(
            "DELETE FROM docs WHERE source = ?", (source,),
        ).rowcount
        n_m = conn.execute(
            "DELETE FROM docs_meta WHERE path LIKE ?",
            (f"pjud/{args.buscador}/%",),
        ).rowcount
        conn.commit()
        print(f"[reset] borrados {n_d} docs + {n_m} meta de {source}", flush=True)
    existing = set(
        r[0] for r in conn.execute(
            "SELECT path FROM docs_meta WHERE path LIKE ?",
            (f"pjud/{args.buscador}/%",),
        )
    )

    n_ok = n_skip = n_empty = n_dup = 0
    seen: set[str] = set()
    t0 = time.time()
    now = time.time()
    for s in iter_docs(bdir):
        sid = str(s.get("id") or s.get("sent__crr_documento_i") or "")
        if not sid:
            continue
        path = f"pjud/{args.buscador}/{sid}.txt"
        if path in existing or path in seen:
            n_dup += 1
            continue
        seen.add(path)
        content = build_content(s)
        if len(content) < 50:
            n_empty += 1
            continue
        year = (s.get("fec_sentencia_sup_dt") or "")[:4]
        conn.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, source, year, content),
        )
        conn.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % args.commit_every == 0:
            conn.commit()
            rate = n_ok / (time.time() - t0)
            print(f"  ok={n_ok} skip_dup={n_dup} empty={n_empty} | {rate:.0f}/s",
                  flush=True)
        if args.max and n_ok >= args.max:
            break
    conn.commit()
    conn.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | source={source} "
          f"ok={n_ok} dup/skip={n_dup} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
