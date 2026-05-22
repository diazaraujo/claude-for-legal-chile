"""MCP server CGR dictámenes."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .cgr_client import CGRClient, format_dictamen_id

logger = logging.getLogger(__name__)
server: Server = Server("mcp-cgr-dictamenes")
_client = CGRClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="cgr_get_dictamen_urls",
            description=(
                "Construye URLs (HTML + PDF) de un dictamen específico de la "
                "Contraloría General de la República de Chile, por número + "
                "año. Ej: numero=66847, year=2010 → dictamen ID '066847N10'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "numero": {"type": "integer"},
                    "year": {"type": "integer"},
                },
                "required": ["numero", "year"],
            },
        ),
        Tool(
            name="cgr_check_dictamen",
            description=(
                "Verifica con HEAD si un dictamen CGR existe en el "
                "buscador público (numero+year)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "numero": {"type": "integer"},
                    "year": {"type": "integer"},
                },
                "required": ["numero", "year"],
            },
        ),
        Tool(
            name="cgr_enumerate_year",
            description=(
                "Enumera TODAS las URLs candidatas de dictámenes CGR de un "
                "año específico en rango [from_numero, to_numero]. Sin red "
                "por default (URLs sintéticas instantáneas)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "from_numero": {"type": "integer", "default": 1},
                    "to_numero": {"type": "integer", "default": 100000},
                    "verify": {"type": "boolean", "default": False},
                },
                "required": ["year"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "cgr_get_dictamen_urls":
        urls = _client.build_urls(int(arguments["numero"]), int(arguments["year"]))
        return [TextContent(type="text", text=json.dumps({
            "numero": urls.numero, "year": urls.year,
            "dictamen_id": urls.dictamen_id,
            "html_url": urls.html_url, "pdf_url": urls.pdf_url,
        }, ensure_ascii=False, indent=2))]

    if name == "cgr_enumerate_year":
        year = int(arguments["year"])
        from_numero = int(arguments.get("from_numero", 1))
        to_numero = int(arguments.get("to_numero", 100000))
        verify = bool(arguments.get("verify", False))
        results = _client.enumerate_year(
            year, from_numero=from_numero, to_numero=to_numero, verify=verify,
        )
        return [TextContent(type="text", text=json.dumps({
            "year": year, "from_numero": from_numero, "to_numero": to_numero,
            "verified": verify, "count": len(results),
            "dictamenes": [
                {
                    "numero": d.numero, "year": d.year,
                    "dictamen_id": d.dictamen_id,
                    "html_url": d.html_url, "pdf_url": d.pdf_url,
                }
                for d in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "cgr_check_dictamen":
        numero = int(arguments["numero"])
        year = int(arguments["year"])
        exists = _client.check_exists(numero, year)
        urls = _client.build_urls(numero, year)
        return [TextContent(type="text", text=json.dumps({
            "numero": numero, "year": year,
            "dictamen_id": urls.dictamen_id,
            "exists": exists,
            "html_url": urls.html_url if exists else None,
            "pdf_url": urls.pdf_url if exists else None,
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
