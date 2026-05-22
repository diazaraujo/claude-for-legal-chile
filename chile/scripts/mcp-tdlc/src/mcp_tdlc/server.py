"""MCP server TDLC."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tdlc_client import TDLCClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-tdlc")
_client = TDLCClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="tdlc_list_sentencias",
            description=(
                "Lista sentencias del Tribunal Defensa Libre Competencia "
                "(Chile) vía API REST de WordPress. Devuelve array con "
                "{id, slug, title, link, date, pdf_urls, ...}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "default": 20, "maximum": 100},
                    "page": {"type": "integer", "default": 1},
                    "search": {
                        "type": "string",
                        "description": "Búsqueda full-text",
                    },
                },
            },
        ),
        Tool(
            name="tdlc_get_sentencia",
            description=(
                "Obtiene una sentencia TDLC específica por ID (numérico "
                "interno WordPress, NO el número de la sentencia)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="tdlc_list_all_sentencias",
            description=(
                "Enumera TODAS las sentencias TDLC paginando hasta agotar. "
                "~213 sentencias publicadas (1/2003 → 213/2026)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "max_pages": {"type": "integer", "default": 50},
                },
            },
        ),
    ]


def _serialize(s) -> dict:
    return {
        "id": s.id, "slug": s.slug, "title": s.title, "link": s.link,
        "date": s.date,
        "numero_sentencia": s.numero_sentencia,
        "rol_causa": s.rol_causa,
        "pdf_urls": s.pdf_urls,
    }


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "tdlc_list_sentencias":
        results = _client.list_sentencias(
            per_page=int(arguments.get("per_page", 20)),
            page=int(arguments.get("page", 1)),
            search=arguments.get("search"),
        )
        return [TextContent(type="text", text=json.dumps({
            "count": len(results),
            "sentencias": [_serialize(s) for s in results],
        }, ensure_ascii=False, indent=2))]

    if name == "tdlc_list_all_sentencias":
        results = _client.list_all_sentencias(
            search=arguments.get("search"),
            max_pages=int(arguments.get("max_pages", 50)),
        )
        return [TextContent(type="text", text=json.dumps({
            "count": len(results),
            "sentencias": [_serialize(s) for s in results],
        }, ensure_ascii=False, indent=2))]

    if name == "tdlc_get_sentencia":
        s = _client.get_sentencia(int(arguments["id"]))
        if not s:
            return [TextContent(type="text", text=json.dumps(
                {"found": False, "id": int(arguments["id"])},
                ensure_ascii=False,
            ))]
        return [TextContent(type="text", text=json.dumps({
            "found": True, **_serialize(s),
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
