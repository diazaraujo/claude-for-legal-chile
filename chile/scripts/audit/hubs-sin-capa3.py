#!/usr/bin/env python3
# std:input chile/normativa/index/catalogo.sqlite3
# std:output stdout: backlog priorizado para capa 3
# std:deps stdlib pura
"""
Identifica las normas con MAYOR centralidad en el grafo BCN (degree
total = outgoing + incoming) que NO tienen perfil capa 3.

Sirve como backlog priorizado para el equipo curador: las normas más
"conectadas" son las que más vale la pena describir manualmente — son
hubs que aparecen en muchas consultas legales.

Filtros:
- Solo normas tipo ley, dl, dfl, cod (las core legales).
- Excluye versiones (URIs con /es@).
- Ordenado por degree desc.

Uso:
    python3 chile/scripts/audit/hubs-sin-capa3.py [--top N] [--tipos ley,dl]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DB = REPO_ROOT / "chile/normativa/index/catalogo.sqlite3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Backlog capa 3 por centralidad")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--tipos", default="ley,dl,dfl,cod")
    args = parser.parse_args()

    if not DB.exists():
        print(f"[FATAL] SQLite no existe: {DB}")
        return 1

    tipos = [t.strip() for t in args.tipos.split(",")]

    con = sqlite3.connect(str(DB))
    cur = con.cursor()

    # Combine outgoing + incoming degree por URI canónica (sin /es@ suffix)
    # Excluir URIs que NO matcheen tipos pedidos
    type_filter_outgoing = " OR ".join(
        f"src_uri LIKE '%/{t}/%'" for t in tipos
    )
    type_filter_incoming = " OR ".join(
        f"dst_uri LIKE '%/{t}/%'" for t in tipos
    )
    cur.execute(
        f"""
        WITH canonical_outgoing AS (
            SELECT
                REPLACE(REPLACE(src_uri, '/es@', '|es@'), '|es@', '') AS uri,
                COUNT(*) AS deg
            FROM relaciones
            WHERE rel = 'modifiesTo'
              AND src_uri NOT LIKE '%/es@%'
              AND ({type_filter_outgoing})
            GROUP BY 1
        ),
        canonical_incoming AS (
            SELECT
                REPLACE(REPLACE(dst_uri, '/es@', '|es@'), '|es@', '') AS uri,
                COUNT(*) AS deg
            FROM relaciones
            WHERE rel = 'modifiesTo'
              AND dst_uri NOT LIKE '%/es@%'
              AND ({type_filter_incoming})
            GROUP BY 1
        ),
        combined AS (
            SELECT uri, deg AS out_deg, 0 AS in_deg FROM canonical_outgoing
            UNION ALL
            SELECT uri, 0 AS out_deg, deg AS in_deg FROM canonical_incoming
        ),
        totals AS (
            SELECT uri, SUM(out_deg) AS out_deg, SUM(in_deg) AS in_deg,
                   SUM(out_deg) + SUM(in_deg) AS total
            FROM combined
            GROUP BY uri
        )
        SELECT t.uri, t.out_deg, t.in_deg, t.total,
               n.tipo, n.numero, n.titulo, n.capa
        FROM totals t
        LEFT JOIN normas n ON n.bcn_uri = t.uri
        ORDER BY t.total DESC
        LIMIT ?
        """,
        (args.top * 2,),  # holgura para filtrar capa 3
    )
    rows = cur.fetchall()

    sin_capa3 = []
    con_capa3 = []
    for uri, out_d, in_d, total, tipo, numero, titulo, capa in rows:
        if capa == 3:
            con_capa3.append((uri, out_d, in_d, total, tipo, numero, titulo))
        else:
            sin_capa3.append((uri, out_d, in_d, total, tipo, numero, titulo, capa))

    print(f"\n=== Top {args.top} normas SIN capa 3 (orden por degree) ===\n")
    print(f"{'out':>5} {'in':>5} {'total':>6}  {'tipo':<5} {'numero':<8}  titulo")
    print("-" * 100)
    for uri, out_d, in_d, total, tipo, numero, titulo, capa in sin_capa3[:args.top]:
        tipo_str = (tipo or "?")[:5]
        num_str = (numero or "?")[:8]
        titulo_str = (titulo or "?")[:60]
        print(f"{out_d:>5} {in_d:>5} {total:>6}  {tipo_str:<5} {num_str:<8}  {titulo_str}")

    print(f"\n=== Normas con capa 3 ya curadas (entre top) ===")
    for uri, out_d, in_d, total, tipo, numero, titulo in con_capa3:
        tipo_str = (tipo or "?")[:5]
        num_str = (numero or "?")[:8]
        titulo_str = (titulo or "?")[:60]
        print(f"  ✓ {tipo_str} {num_str}  {titulo_str}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
