"""Servidor MCP que expone BCN/LeyChile como tools + resources.

Tools expuestos:
- bcn_get_norma(id_norma): metadata + estructura de una norma.
- bcn_check_vigencia(id_norma): vigencia actual contra BCN.
- bcn_get_xml(id_norma): XML estructural completo.

Stdio transport (uso local con Claude Code).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .bcn_client import BCNClient
from .local_catalog import LocalCatalog

logger = logging.getLogger(__name__)

server: Server = Server("mcp-bcn-leychile")
_client = BCNClient()
_catalog = LocalCatalog()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bcn_get_norma",
            description=(
                "Recupera metadata + estructura jerárquica (libro/título/"
                "artículo) de una norma chilena desde BCN/LeyChile. "
                "Devuelve JSON con titulo_oficial, fecha publicación, "
                "vigencia, lista de partes estructurales."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id_norma": {
                        "type": "string",
                        "description": (
                            "ID numérico BCN (ej. '1075210' para "
                            "Ley 21.400 Matrimonio Igualitario)"
                        ),
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "default": False,
                        "description": "Ignora cache local",
                    },
                },
                "required": ["id_norma"],
            },
        ),
        Tool(
            name="bcn_check_vigencia",
            description=(
                "Verifica si una norma está vigente al día de hoy según "
                "BCN. Útil para confirmar antes de citar."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id_norma": {
                        "type": "string",
                        "description": "ID numérico BCN",
                    }
                },
                "required": ["id_norma"],
            },
        ),
        Tool(
            name="bcn_get_xml",
            description=(
                "Recupera el XML estructural completo de una norma "
                "(útil para parseo avanzado por el cliente)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id_norma": {"type": "string"},
                    "force_refresh": {"type": "boolean", "default": False},
                },
                "required": ["id_norma"],
            },
        ),
        Tool(
            name="lookup_norma",
            description=(
                "Resuelve una norma chilena por número, leychile_code, o "
                "slug usando el catálogo local indexado. Devuelve "
                "metadata + ruta al .md curado. Más rápido que "
                "`bcn_get_norma` y funciona sin red. Provee uno de los "
                "tres argumentos."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": "Tipo de norma (ley, dl, dfl, dto, cod, aa, acd, tra). Requerido si usas 'numero'.",
                    },
                    "numero": {"type": "string"},
                    "leychile_code": {"type": "string"},
                    "slug": {"type": "string"},
                },
            },
        ),
        Tool(
            name="search_normas",
            description=(
                "Busca normas en el catálogo local por título (LIKE). "
                "Resultados ordenados por capa (3 = curado, 2 = "
                "estructural, 1 = catálogo). Para fuzzy/semántica, "
                "complementar con bcn_get_norma."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string"},
                    "tipo": {
                        "type": "string",
                        "description": "Filtrar por tipo (opcional)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                    },
                },
                "required": ["q"],
            },
        ),
        Tool(
            name="get_relaciones",
            description=(
                "Devuelve relaciones entre normas desde el grafo BCN "
                "(modifiesTo, isModifiedBy, regulates, isRegulatedBy, "
                "recasts, rectifies, agreeWith). Útil para entender qué "
                "modifica/deroga/reglamenta una norma."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "bcn_uri": {
                        "type": "string",
                        "description": "URI BCN (http://datos.bcn.cl/recurso/cl/...). Si no la conoces, usar lookup_norma primero.",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["outgoing", "incoming", "both"],
                        "default": "outgoing",
                    },
                },
                "required": ["bcn_uri"],
            },
        ),
        Tool(
            name="catalog_stats",
            description=(
                "Estadísticas del catálogo local: total normas, edges, "
                "por tipo. Útil para verificar cobertura."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "bcn_get_norma":
        id_norma = arguments["id_norma"]
        force = bool(arguments.get("force_refresh", False))
        try:
            xml = _client.fetch_xml(id_norma, force_refresh=force)
            meta = _client.parse_metadata(xml)
            estructura = _client.parse_estructura(xml)
            payload = {
                "id_norma": meta.id_norma,
                "tipo": meta.tipo,
                "numero": meta.numero,
                "titulo_oficial": meta.titulo,
                "fecha_publicacion": meta.fecha_publicacion,
                "organismo": meta.organismo,
                "vigencia": meta.vigencia,
                "url_consulta": meta.url_consulta,
                "estructura": [_estructura_to_dict(p) for p in estructura],
            }
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"{type(e).__name__}: {e}"},
                        ensure_ascii=False,
                    ),
                )
            ]

    if name == "bcn_check_vigencia":
        id_norma = arguments["id_norma"]
        payload = _client.check_vigencia(id_norma)
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

    if name == "bcn_get_xml":
        id_norma = arguments["id_norma"]
        force = bool(arguments.get("force_refresh", False))
        try:
            xml = _client.fetch_xml(id_norma, force_refresh=force)
            return [TextContent(type="text", text=xml)]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"{type(e).__name__}: {e}"},
                        ensure_ascii=False,
                    ),
                )
            ]

    if name == "lookup_norma":
        norma = None
        if arguments.get("slug"):
            norma = _catalog.lookup_by_slug(arguments["slug"])
        elif arguments.get("leychile_code"):
            norma = _catalog.lookup_by_leychile_code(arguments["leychile_code"])
        elif arguments.get("tipo") and arguments.get("numero"):
            norma = _catalog.lookup_by_numero(
                arguments["tipo"], arguments["numero"]
            )
        if not norma:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"found": False, "hint": "Probar bcn_get_norma con id_norma BCN."},
                        ensure_ascii=False,
                    ),
                )
            ]
        payload = {
            "found": True,
            "slug": norma.slug,
            "tipo": norma.tipo,
            "numero": norma.numero,
            "titulo": norma.titulo,
            "publicacion": norma.publicacion,
            "promulgacion": norma.promulgacion,
            "organismo": norma.organismo,
            "leychile_code": norma.leychile_code,
            "bcn_uri": norma.bcn_uri,
            "fuente_oficial": norma.fuente_oficial,
            "capa": norma.capa,
            "md_path": norma.md_path,
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
            )
        ]

    if name == "search_normas":
        q = arguments["q"]
        tipo = arguments.get("tipo")
        limit = int(arguments.get("limit", 20))
        results = _catalog.search(q, limit=limit, tipo=tipo)
        payload = {
            "query": q,
            "tipo_filter": tipo,
            "count": len(results),
            "results": [
                {
                    "slug": n.slug,
                    "tipo": n.tipo,
                    "numero": n.numero,
                    "titulo": n.titulo,
                    "capa": n.capa,
                    "leychile_code": n.leychile_code,
                    "fuente_oficial": n.fuente_oficial,
                    "md_path": n.md_path,
                }
                for n in results
            ],
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
            )
        ]

    if name == "get_relaciones":
        uri = arguments["bcn_uri"]
        direction = arguments.get("direction", "outgoing")
        edges = _catalog.relaciones(uri, direction=direction)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "bcn_uri": uri,
                        "direction": direction,
                        "count": len(edges),
                        "edges": [
                            {"src": e.src_uri, "rel": e.rel, "dst": e.dst_uri}
                            for e in edges
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        ]

    if name == "catalog_stats":
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    _catalog.stats(), ensure_ascii=False, indent=2
                ),
            )
        ]

    return [TextContent(type="text", text=json.dumps({"error": f"tool desconocido: {name}"}))]


def _estructura_to_dict(parte) -> dict[str, Any]:
    return {
        "tipo_parte": parte.tipo_parte,
        "numero": parte.numero,
        "titulo": parte.titulo,
        "texto": parte.texto[:500] + ("..." if len(parte.texto) > 500 else ""),
        "hijos": [_estructura_to_dict(h) for h in parte.hijos],
    }


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    """Entrypoint del CLI mcp-bcn-leychile."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
