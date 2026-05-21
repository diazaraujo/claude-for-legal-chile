"""CLI directo para queries al catálogo local sin Claude Code.

Útil para debugging, integración con scripts shell, o explorar el grafo
desde la línea de comandos.

Subcomandos:
  lookup        — resuelve norma por slug/leychile_code/(tipo,numero)
  search        — búsqueda por título
  relaciones    — edges del grafo
  stats         — totales del catálogo
  hubs          — top normas por degree (más modifican o son modificadas)

Ejemplo:
  python3 -m mcp_bcn_leychile.cli stats
  python3 -m mcp_bcn_leychile.cli lookup --tipo ley --numero 21643
  python3 -m mcp_bcn_leychile.cli search "acoso laboral"
  python3 -m mcp_bcn_leychile.cli hubs --rel modifiesTo --top 10
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .local_catalog import LocalCatalog


def _dump(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_lookup(args: argparse.Namespace) -> int:
    cat = LocalCatalog()
    n = None
    if args.slug:
        n = cat.lookup_by_slug(args.slug)
    elif args.leychile_code:
        n = cat.lookup_by_leychile_code(args.leychile_code)
    elif args.tipo and args.numero:
        n = cat.lookup_by_numero(args.tipo, args.numero)
    if not n:
        _dump({"found": False})
        return 1
    _dump({
        "found": True,
        "slug": n.slug,
        "tipo": n.tipo,
        "numero": n.numero,
        "titulo": n.titulo,
        "publicacion": n.publicacion,
        "leychile_code": n.leychile_code,
        "fuente_oficial": n.fuente_oficial,
        "bcn_uri": n.bcn_uri,
        "capa": n.capa,
        "md_path": n.md_path,
    })
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    cat = LocalCatalog()
    results = cat.search(args.q, limit=args.limit, tipo=args.tipo)
    _dump([
        {
            "slug": n.slug,
            "tipo": n.tipo,
            "numero": n.numero,
            "titulo": n.titulo,
            "capa": n.capa,
            "leychile_code": n.leychile_code,
        }
        for n in results
    ])
    return 0


def cmd_relaciones(args: argparse.Namespace) -> int:
    cat = LocalCatalog()
    edges = cat.relaciones(args.uri, direction=args.direction)
    _dump([
        {"src": e.src_uri, "rel": e.rel, "dst": e.dst_uri} for e in edges
    ])
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    cat = LocalCatalog()
    _dump(cat.stats())
    return 0


def cmd_hubs(args: argparse.Namespace) -> int:
    cat = LocalCatalog()
    if not cat.available:
        _dump({"error": "SQLite no disponible"})
        return 1
    con = sqlite3.connect(str(cat.db_path))
    cur = con.cursor()
    if args.direction == "outgoing":
        rows = cur.execute(
            "SELECT src_uri, COUNT(*) AS n FROM relaciones "
            "WHERE rel = ? GROUP BY src_uri ORDER BY n DESC LIMIT ?",
            (args.rel, args.top),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT dst_uri, COUNT(*) AS n FROM relaciones "
            "WHERE rel = ? GROUP BY dst_uri ORDER BY n DESC LIMIT ?",
            (args.rel, args.top),
        ).fetchall()
    _dump([{"uri": uri, "count": n} for uri, n in rows])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp-bcn-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lookup")
    p.add_argument("--slug")
    p.add_argument("--leychile-code", dest="leychile_code")
    p.add_argument("--tipo")
    p.add_argument("--numero")
    p.set_defaults(func=cmd_lookup)

    p = sub.add_parser("search")
    p.add_argument("q")
    p.add_argument("--tipo")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("relaciones")
    p.add_argument("uri")
    p.add_argument(
        "--direction", choices=["outgoing", "incoming", "both"],
        default="outgoing",
    )
    p.set_defaults(func=cmd_relaciones)

    p = sub.add_parser("stats")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("hubs")
    p.add_argument(
        "--rel", default="modifiesTo",
        choices=[
            "modifiesTo", "isModifiedBy", "regulates", "isRegulatedBy",
            "recasts", "isRecastedBy", "rectifies", "isRectifiedBy",
            "agreeWith", "hasVersion",
        ],
    )
    p.add_argument(
        "--direction", choices=["outgoing", "incoming"], default="outgoing",
    )
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(func=cmd_hubs)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
