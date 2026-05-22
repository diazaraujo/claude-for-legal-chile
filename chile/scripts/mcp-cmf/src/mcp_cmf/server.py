"""MCP server CMF — Normas de Carácter General (NCG) + Circulares."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .cmf_client import CMFClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-cmf")
_client = CMFClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="cmf_get_url",
            description=(
                "Construye URL canónica de una norma CMF Chile. tipo='ncg' "
                "para Normas de Carácter General o 'cir' para Circulares."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["ncg", "cir"]},
                    "numero": {"type": "integer"},
                    "year": {"type": "integer"},
                },
                "required": ["tipo", "numero", "year"],
            },
        ),
        Tool(
            name="cmf_check_norma",
            description=(
                "HEAD request para verificar si la norma CMF existe en el "
                "sitio (devuelve PDF). Útil para confirmar antes de citar."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["ncg", "cir"]},
                    "numero": {"type": "integer"},
                    "year": {"type": "integer"},
                },
                "required": ["tipo", "numero", "year"],
            },
        ),
        Tool(
            name="cmf_enumerate",
            description=(
                "Enumera URLs candidatas CMF para tipo + rango años/números. "
                "Sin red por default (URLs sintéticas instantáneas). "
                "verify=True hace HEAD a cada una (costoso)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["ncg", "cir"]},
                    "from_year": {"type": "integer", "default": 1990},
                    "to_year": {"type": "integer"},
                    "from_numero": {"type": "integer", "default": 1},
                    "to_numero": {"type": "integer", "default": 3000},
                    "verify": {"type": "boolean", "default": False},
                },
                "required": ["tipo"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "cmf_get_url":
        result = _client.get_norma_url(
            arguments["tipo"], int(arguments["numero"]), int(arguments["year"])
        )
        return [TextContent(type="text", text=json.dumps({
            "tipo": result.tipo, "numero": result.numero,
            "year": result.year, "url": result.url,
        }, ensure_ascii=False, indent=2))]

    if name == "cmf_enumerate":
        to_year = arguments.get("to_year")
        results = _client.enumerate(
            arguments["tipo"],
            from_year=int(arguments.get("from_year", 1990)),
            to_year=int(to_year) if to_year else None,
            from_numero=int(arguments.get("from_numero", 1)),
            to_numero=int(arguments.get("to_numero", 3000)),
            verify=bool(arguments.get("verify", False)),
        )
        return [TextContent(type="text", text=json.dumps({
            "tipo": arguments["tipo"],
            "count": len(results),
            "normas": [
                {"tipo": r.tipo, "numero": r.numero, "year": r.year,
                 "url": r.url, "available": r.available}
                for r in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "cmf_check_norma":
        result = _client.check_norma(
            arguments["tipo"], int(arguments["numero"]), int(arguments["year"])
        )
        return [TextContent(type="text", text=json.dumps({
            "tipo": result.tipo, "numero": result.numero,
            "year": result.year, "url": result.url,
            "available": result.available, "pdf_size": result.pdf_size,
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
