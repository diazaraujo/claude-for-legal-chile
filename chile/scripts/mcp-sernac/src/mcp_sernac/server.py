"""MCP server SERNAC."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .sernac_client import SERNACClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-sernac")
_client = SERNACClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sernac_list_documentos",
            description=(
                "Lista circulares o dictámenes interpretativos del SERNAC "
                "(Servicio Nacional del Consumidor de Chile). Devuelve "
                "array de {article_id, title, html_url, pdf_url}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["circulares", "dictamenes"],
                        "default": "circulares",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "sernac_list_documentos":
        tipo = arguments.get("tipo", "circulares")
        docs = _client.list_documentos(tipo)
        return [TextContent(type="text", text=json.dumps({
            "tipo": tipo, "count": len(docs),
            "documentos": [
                {
                    "article_id": d.article_id, "title": d.title,
                    "html_url": d.html_url, "pdf_url": d.pdf_url,
                }
                for d in docs
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
