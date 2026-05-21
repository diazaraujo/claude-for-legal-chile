#!/usr/bin/env python3
# std:input chile/normativa/{leyes,codigos,decretos}/*.md (capa 3)
# std:output modifica frontmatter agregando grafo_relaciones (idempotente)
# std:deps stdlib pura
"""
Enriquecer perfiles capa 3 con relaciones del grafo BCN.

Para cada .md capa 3:
1. Lee leychile_code (del frontmatter o derivado de fuente_oficial).
2. Resuelve bcn_uri del catálogo SQLite por leychile_code.
3. Query relaciones del grafo (modifiesTo, isModifiedBy).
4. Agrega/reemplaza bloque `grafo_relaciones:` en frontmatter:
   - outgoing: lista de URIs que esta norma modifica
   - incoming: lista de URIs que modifican a esta norma

Idempotente: si el bloque existe, lo reemplaza.

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: sólo persiste
relaciones explícitas del grafo BCN. Distinto del campo `relacionada_per`
que es curado manualmente.

Uso:
    python3 chile/scripts/audit/enriquecer-capa3-grafo.py [--apply] [--max-edges N]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DB = REPO_ROOT / "chile/normativa/index/catalogo.sqlite3"
CAPA3_DIRS = [
    REPO_ROOT / "chile/normativa/leyes",
    REPO_ROOT / "chile/normativa/codigos",
    REPO_ROOT / "chile/normativa/decretos",
]

LEYCHILE_RE = re.compile(r"idNorma=(\d+)")
GRAFO_BLOCK_RE = re.compile(
    r"^grafo_relaciones:\n(?:  .*\n)*",
    re.MULTILINE,
)


def parse_fm(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm: dict[str, str] = {}
    for line in text[4:end].split("\n"):
        if not line or line.startswith("  ") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip('"')
        fm[k.strip()] = v
    return fm


def find_uri_by_leychile(con: sqlite3.Connection, code: str) -> str | None:
    cur = con.cursor()
    # Buscar bcn_uri en el catálogo capa 1 con este leychile_code
    row = cur.execute(
        "SELECT bcn_uri FROM normas WHERE leychile_code = ? "
        "AND bcn_uri IS NOT NULL AND bcn_uri NOT LIKE '%/es@%' LIMIT 1",
        (code,),
    ).fetchone()
    return row[0] if row else None


def get_relaciones(
    con: sqlite3.Connection, uri: str, max_edges: int
) -> tuple[list[str], list[str]]:
    """Devuelve (outgoing modifiesTo, incoming modifiesTo)."""
    cur = con.cursor()
    out_rows = cur.execute(
        "SELECT DISTINCT dst_uri FROM relaciones "
        "WHERE rel='modifiesTo' AND src_uri = ? AND dst_uri NOT LIKE '%/es@%' "
        "LIMIT ?",
        (uri, max_edges),
    ).fetchall()
    in_rows = cur.execute(
        "SELECT DISTINCT src_uri FROM relaciones "
        "WHERE rel='modifiesTo' AND dst_uri = ? AND src_uri NOT LIKE '%/es@%' "
        "LIMIT ?",
        (uri, max_edges),
    ).fetchall()
    return [r[0] for r in out_rows], [r[0] for r in in_rows]


def shorten_uri(uri: str) -> str:
    """Convierte URI BCN a slug corto si está en catálogo."""
    return uri.replace("http://datos.bcn.cl/recurso/cl/", "")


def build_grafo_block(out_uris: list[str], in_uris: list[str]) -> str:
    if not out_uris and not in_uris:
        return ""
    block = "grafo_relaciones:\n"
    if out_uris:
        block += "  modifica:\n"
        for u in out_uris:
            block += f"    - {shorten_uri(u)}\n"
    if in_uris:
        block += "  modificada_por:\n"
        for u in in_uris:
            block += f"    - {shorten_uri(u)}\n"
    return block


def replace_grafo_block(content: str, new_block: str) -> str:
    """Reemplaza o inserta el bloque grafo_relaciones en el frontmatter."""
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---\n", 4)
    if end == -1:
        return content
    fm_raw = content[4:end]
    body = content[end:]

    # Remove existing block
    fm_raw = GRAFO_BLOCK_RE.sub("", fm_raw).rstrip()

    # Append new block if non-empty
    if new_block:
        fm_raw += "\n" + new_block.rstrip()
    fm_raw += "\n"

    return f"---\n{fm_raw}{body}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich capa 3 con grafo BCN")
    parser.add_argument("--apply", action="store_true", help="Escribe los .md")
    parser.add_argument(
        "--max-edges", type=int, default=20,
        help="Tope de outgoing/incoming por perfil (default 20)",
    )
    args = parser.parse_args()

    if not DB.exists():
        print(f"[FATAL] SQLite no existe: {DB}")
        return 1

    con = sqlite3.connect(str(DB))

    files: list[Path] = []
    for d in CAPA3_DIRS:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))

    print(f"[INFO] Procesando {len(files)} perfiles capa 3\n")

    enriquecidos = 0
    sin_uri = 0
    sin_edges = 0
    total_edges = 0

    for f in files:
        content = f.read_text(encoding="utf-8")
        fm = parse_fm(content)

        leychile = fm.get("leychile_code")
        if not leychile and (fuente := fm.get("fuente_oficial")):
            m = LEYCHILE_RE.search(fuente)
            if m:
                leychile = m.group(1)
        if not leychile:
            sin_uri += 1
            continue

        uri = find_uri_by_leychile(con, leychile)
        if not uri:
            sin_uri += 1
            continue

        out_uris, in_uris = get_relaciones(con, uri, args.max_edges)
        if not out_uris and not in_uris:
            sin_edges += 1
            continue

        block = build_grafo_block(out_uris, in_uris)
        new_content = replace_grafo_block(content, block)

        if new_content != content:
            if args.apply:
                f.write_text(new_content, encoding="utf-8")
            enriquecidos += 1
            total_edges += len(out_uris) + len(in_uris)
            print(
                f"  {f.stem}: out={len(out_uris)} in={len(in_uris)}",
                flush=True,
            )

    print(f"\n[RESUMEN]")
    print(f"  Perfiles enriquecidos:    {enriquecidos}")
    print(f"  Sin URI en catálogo:      {sin_uri}")
    print(f"  URI pero sin edges:       {sin_edges}")
    print(f"  Total edges agregados:    {total_edges}")
    print(f"  Apply: {'SÍ' if args.apply else 'no (dry-run)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
