"""MCP server BCN Historia de la Ley."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tramitacion_client import TramitacionClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-bcn-tramitacion")
_client = TramitacionClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bcn_historia_recientes",
            description=(
                "Lista las historias de la ley más recientemente publicadas "
                "por la Biblioteca del Congreso Nacional (típicamente 10 "
                "últimas en home). Devuelve {history_id, title, "
                "standard_url, vista_expandida_url}."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bcn_historia_url",
            description=(
                "Construye URLs (standard + vista expandida) de una historia "
                "de la ley específica por history_id. NOTA: history_id es "
                "ID interno BCN, no el número de la ley. Para encontrarlo, "
                "primero usar bcn_historia_recientes o buscar en "
                "bcn.cl/historiadelaley/."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "history_id": {"type": "integer"},
                },
                "required": ["history_id"],
            },
        ),
        Tool(
            name="bcn_historia_check",
            description=(
                "HEAD request para verificar si una historia existe con el "
                "history_id dado."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "history_id": {"type": "integer"},
                },
                "required": ["history_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "bcn_historia_recientes":
        results = _client.list_recientes()
        return [TextContent(type="text", text=json.dumps({
            "count": len(results),
            "historias": [
                {
                    "history_id": h.history_id, "title": h.title,
                    "standard_url": h.standard_url,
                    "vista_expandida_url": h.vista_expandida_url,
                }
                for h in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "bcn_historia_url":
        h = _client.build_urls(int(arguments["history_id"]))
        return [TextContent(type="text", text=json.dumps({
            "history_id": h.history_id,
            "standard_url": h.standard_url,
            "vista_expandida_url": h.vista_expandida_url,
        }, ensure_ascii=False, indent=2))]

    if name == "bcn_historia_check":
        exists = _client.check_historia(int(arguments["history_id"]))
        return [TextContent(type="text", text=json.dumps({
            "history_id": int(arguments["history_id"]),
            "exists": exists,
        }, ensure_ascii=False))]

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
