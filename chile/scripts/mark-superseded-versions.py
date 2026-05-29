#!/usr/bin/env python3
"""Marca versiones de norma SUPERSEDED por una versión vigente más nueva.

Añade `docs_norma.superseded_by` (idNorma de la versión que reemplaza, NULL si
ninguna). Usado por el filtro `vigentes_only`: una norma con `superseded_by`
no-nulo se trata como histórica (no vigente) aunque su atributo `derogado` siga
en "no derogado" (LeyChile no marca derogado al refundido anterior cuando publica
uno nuevo).

IMPORTANTE — solo se marca lo VERIFICADO caso a caso. NO se usa detección
automática por (tipo,numero,titulo): esa clave es insegura (p.ej. certificados
"DETERMINA INTERÉS CORRIENTE..." comparten tipo+numero+titulo pero son
publicaciones periódicas distintas, no versiones de la misma norma).

Cada par requiere haberse verificado: que la versión nueva contenga (por número
y/o contenido) el articulado de la anterior, y que lo único exclusivo de la vieja
no sea derecho vigente. Registrar la evidencia en el comentario del par.

Uso:
  python3 mark-superseded-versions.py --dry-run
  python3 mark-superseded-versions.py
"""
from __future__ import annotations
import argparse
import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"

# (vieja, nueva, evidencia). Solo pares VERIFICADOS.
SUPERSEDED: list[tuple[int, int, str]] = [
    # Código del Trabajo: DFL 1 de 1994 (refundido) reemplazado por el DFL 1 de
    # 2002 (idNorma 207436, fechaVersion 2026-02-07). Verificado 2026-05-27:
    # 435/444 arts del 3471 están en 207436; los 9 exclusivos (204, 314 bis,
    # 334 bis, 374 bis, 412, 413, 428 bis, 473 bis, 478 bis) NO están en el texto
    # vigente (huecos en la secuencia del XML) → no son derecho vigente.
    (3471, 207436, "Codigo del Trabajo 1994->2002, verificado solape arts"),
]


def ensure_column(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(docs_norma)")}
    if "superseded_by" not in cols:
        conn.execute("ALTER TABLE docs_norma ADD COLUMN superseded_by INTEGER")
        conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=60)
    ensure_column(conn)

    applied, skipped = [], []
    for old, new, ev in SUPERSEDED:
        row = conn.execute(
            "SELECT derogado, superseded_by FROM docs_norma WHERE leychile_code=?",
            (old,),
        ).fetchone()
        new_exists = conn.execute(
            "SELECT 1 FROM docs_norma WHERE leychile_code=?", (new,)
        ).fetchone()
        if row is None or new_exists is None:
            skipped.append((old, new, "norma vieja o nueva ausente en docs_norma"))
            continue
        if row[1] == new:
            skipped.append((old, new, "ya marcada"))
            continue
        if not args.dry_run:
            conn.execute(
                "UPDATE docs_norma SET superseded_by=? WHERE leychile_code=?",
                (new, old),
            )
        applied.append((old, new, ev))

    if not args.dry_run:
        conn.commit()

    total = conn.execute(
        "SELECT COUNT(*) FROM docs_norma WHERE superseded_by IS NOT NULL"
    ).fetchone()[0]
    conn.close()

    tag = "DRY-RUN" if args.dry_run else "APLICADO"
    print(f"[{tag}] {len(applied)} marcadas, {len(skipped)} omitidas")
    for old, new, ev in applied:
        print(f"  {old} -> superseded_by {new}  ({ev})")
    for old, new, why in skipped:
        print(f"  SKIP {old}->{new}: {why}")
    print(f"  total superseded en docs_norma: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
