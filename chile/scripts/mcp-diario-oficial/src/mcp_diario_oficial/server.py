"""MCP server para Diario Oficial chileno.

Tools expuestos:
- do_list_today: lista publicaciones de la edición actual.
- do_list_edition: lista publicaciones de una edición específica.
- do_get_pdf_url: URL del PDF de una publicación específica.
- do_get_sumario_url: URL del sumario PDF de la edición.

NO descarga PDFs (los devuelve como URLs para que Claude los obtenga
con su propio fetch).
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

from .do_client import DiarioOficialClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-diario-oficial")

CACHE_DIR = Path.home() / ".cache" / "mcp-diario-oficial"
_client = DiarioOficialClient(cache_db=CACHE_DIR / "cache.sqlite3")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="do_list_today",
            description=(
                "Lista las publicaciones del Diario Oficial de Chile del "
                "día actual. Devuelve fecha, edición, y array de "
                "{cve, title, pdf_url}."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="do_list_edition",
            description=(
                "Lista publicaciones de una edición específica del Diario "
                "Oficial. Útil para revisar publicaciones de una fecha pasada."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Fecha DD-MM-YYYY (ej. '22-05-2026')",
                    },
                    "edition": {
                        "type": "string",
                        "description": "Número de edición (ej. '44455')",
                    },
                },
                "required": ["date", "edition"],
            },
        ),
        Tool(
            name="do_get_pdf_url",
            description=(
                "Devuelve la URL del PDF de una publicación específica del "
                "Diario Oficial (por CVE)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cve": {"type": "string"},
                    "date": {"type": "string", "description": "DD-MM-YYYY"},
                    "edition": {"type": "string"},
                },
                "required": ["cve", "date", "edition"],
            },
        ),
        Tool(
            name="do_get_sumario_url",
            description=(
                "URL del PDF sumario (tabla de contenidos) de una edición."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "edition": {"type": "string"},
                },
                "required": ["date", "edition"],
            },
        ),
        Tool(
            name="do_fetch_by_date",
            description=(
                "Resuelve la edición del Diario Oficial de un día específico "
                "(DD-MM-YYYY) sin necesidad de conocer el número de edición. "
                "Devuelve {date, edition, publicaciones}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "DD-MM-YYYY"},
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="do_enumerate_date_range",
            description=(
                "Enumera TODAS las ediciones del Diario Oficial entre dos "
                "fechas. Skip fines de semana/festivos. Histórico desde "
                "01-01-2010 está disponible vía edición electrónica."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_date": {"type": "string", "description": "DD-MM-YYYY"},
                    "to_date": {"type": "string", "description": "DD-MM-YYYY"},
                },
                "required": ["from_date", "to_date"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "do_list_today":
        date, edition, pubs = _client.list_today()
        return [TextContent(type="text", text=json.dumps({
            "date": date, "edition": edition, "count": len(pubs),
            "publicaciones": [
                {"cve": p.cve, "title": p.title, "pdf_url": p.pdf_url}
                for p in pubs
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "do_list_edition":
        date = arguments["date"]
        edition = arguments["edition"]
        html = _client.fetch_edition_html(date, edition)
        pubs = _client.parse_publicaciones(html, edition, date)
        return [TextContent(type="text", text=json.dumps({
            "date": date, "edition": edition, "count": len(pubs),
            "publicaciones": [
                {"cve": p.cve, "title": p.title, "pdf_url": p.pdf_url}
                for p in pubs
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "do_get_pdf_url":
        url = _client.get_publicacion_pdf_url(
            arguments["cve"], arguments["date"], arguments["edition"]
        )
        return [TextContent(type="text", text=json.dumps(
            {"pdf_url": url}, ensure_ascii=False
        ))]

    if name == "do_fetch_by_date":
        date, edition, pubs = _client.fetch_by_date(arguments["date"])
        return [TextContent(type="text", text=json.dumps({
            "date": date, "edition": edition,
            "count": len(pubs),
            "publicaciones": [
                {"cve": p.cve, "title": p.title, "pdf_url": p.pdf_url}
                for p in pubs
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "do_enumerate_date_range":
        results = _client.enumerate_date_range(
            arguments["from_date"], arguments["to_date"]
        )
        return [TextContent(type="text", text=json.dumps({
            "from_date": arguments["from_date"],
            "to_date": arguments["to_date"],
            "edition_count": len(results),
            "total_publicaciones": sum(len(p) for _, _, p in results),
            "ediciones": [
                {
                    "date": d, "edition": e,
                    "publicaciones": [
                        {"cve": p.cve, "title": p.title, "pdf_url": p.pdf_url}
                        for p in pubs
                    ],
                }
                for d, e, pubs in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "do_get_sumario_url":
        url = _client.get_sumario_pdf_url(
            arguments["date"], arguments["edition"]
        )
        return [TextContent(type="text", text=json.dumps(
            {"sumario_url": url}, ensure_ascii=False
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
