"""MCP server DT dictámenes."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .dt_client import DTClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-dt-dictamenes")
_client = DTClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="dt_search_dictamenes",
            description=(
                "Busca dictámenes y ordinarios de la Dirección del Trabajo "
                "de Chile (dt.gob.cl/legislacion). Devuelve lista de "
                "{article_id, url, title}. NOTA: DT no usa números de "
                "dictamen como URL, solo IDs internos del CMS — la única "
                "forma de descubrir un dictamen es vía búsqueda por texto."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto a buscar (palabras o frase)",
                    },
                    "exact": {
                        "type": "boolean",
                        "default": False,
                        "description": "True para búsqueda por frase exacta",
                    },
                    "title_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "True para buscar solo en título",
                    },
                    "since": {
                        "type": "string",
                        "description": "Fecha desde (formato YYYY-MM-DD)",
                    },
                    "until": {
                        "type": "string",
                        "description": "Fecha hasta (formato YYYY-MM-DD)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="dt_get_dictamen_url",
            description=(
                "Construye URL canónica de un dictamen DT por ID interno "
                "(article_id) — útil cuando ya conoces el ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {"type": "integer"},
                },
                "required": ["article_id"],
            },
        ),
        Tool(
            name="dt_list_by_date_range",
            description=(
                "Lista TODOS los dictámenes DT publicados en rango de "
                "fechas (sin palabra clave). Formato YYYY-MM-DD."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "since": {"type": "string"},
                    "until": {"type": "string"},
                },
                "required": ["since", "until"],
            },
        ),
        Tool(
            name="dt_list_all_by_year",
            description=(
                "Itera mes por mes para enumerar TODOS los dictámenes DT "
                "de un año específico. Aplica principio 'toda la data'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                },
                "required": ["year"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "dt_search_dictamenes":
        results = _client.search(
            query=arguments.get("query", ""),
            exact=bool(arguments.get("exact", False)),
            title_only=bool(arguments.get("title_only", False)),
            since=arguments.get("since", ""),
            until=arguments.get("until", ""),
        )
        return [TextContent(type="text", text=json.dumps({
            "query": arguments.get("query", ""),
            "count": len(results),
            "results": [
                {"article_id": d.article_id, "url": d.url, "title": d.title}
                for d in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "dt_get_dictamen_url":
        url = _client.build_url(int(arguments["article_id"]))
        return [TextContent(type="text", text=json.dumps(
            {"article_id": int(arguments["article_id"]), "url": url},
            ensure_ascii=False,
        ))]

    if name == "dt_list_by_date_range":
        results = _client.list_by_date_range(
            arguments["since"], arguments["until"]
        )
        return [TextContent(type="text", text=json.dumps({
            "since": arguments["since"], "until": arguments["until"],
            "count": len(results),
            "results": [
                {"article_id": d.article_id, "url": d.url, "title": d.title}
                for d in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "dt_list_all_by_year":
        year = int(arguments["year"])
        results = _client.list_all_by_year(year)
        return [TextContent(type="text", text=json.dumps({
            "year": year, "count": len(results),
            "results": [
                {"article_id": d.article_id, "url": d.url, "title": d.title}
                for d in results
            ],
        }, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text=json.dumps(
        {"error": f"tool desconocido: {name}"}
    ))]


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
