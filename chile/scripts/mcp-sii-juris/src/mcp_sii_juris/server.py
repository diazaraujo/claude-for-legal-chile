"""MCP server para Jurisprudencia administrativa SII Chile.

Tools:
- sii_list_circulares(year): lista todas las circulares del año.
- sii_get_circular_url(number, year): URL del PDF de una circular.
- sii_search_circulares(query, year): búsqueda por título + resumen.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .sii_client import SIIJurisClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-sii-juris")

CACHE_DIR = Path.home() / ".cache" / "mcp-sii-juris"
_client = SIIJurisClient(cache_db=CACHE_DIR / "cache.sqlite3")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sii_list_circulares",
            description=(
                "Lista todas las circulares emitidas por el SII (Servicio de "
                "Impuestos Internos de Chile) en un año específico. Devuelve "
                "array de {number, title, summary, pdf_url}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                },
                "required": ["year"],
            },
        ),
        Tool(
            name="sii_get_circular_url",
            description=(
                "Devuelve la URL del PDF de una circular específica del SII."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "year": {"type": "integer"},
                },
                "required": ["number", "year"],
            },
        ),
        Tool(
            name="sii_search_circulares",
            description=(
                "Búsqueda LIKE por título + resumen de circulares SII de un "
                "año específico."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "year": {"type": "integer"},
                },
                "required": ["query", "year"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "sii_list_circulares":
        year = int(arguments["year"])
        circulares = _client.list_circulares(year)
        payload = {
            "year": year, "count": len(circulares),
            "circulares": [
                {
                    "number": c.number, "title": c.title,
                    "summary": c.summary, "pdf_url": c.pdf_url,
                }
                for c in circulares
            ],
        }
        return [TextContent(type="text", text=json.dumps(
            payload, ensure_ascii=False, indent=2
        ))]

    if name == "sii_get_circular_url":
        url = _client.get_circular_pdf_url(
            int(arguments["year"]), int(arguments["number"])
        )
        return [TextContent(type="text", text=json.dumps(
            {"pdf_url": url}, ensure_ascii=False
        ))]

    if name == "sii_search_circulares":
        year = int(arguments["year"])
        results = _client.search_circulares(arguments["query"], year)
        payload = {
            "year": year, "query": arguments["query"],
            "count": len(results),
            "results": [
                {
                    "number": c.number, "title": c.title,
                    "summary": c.summary, "pdf_url": c.pdf_url,
                }
                for c in results
            ],
        }
        return [TextContent(type="text", text=json.dumps(
            payload, ensure_ascii=False, indent=2
        ))]

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
