"""MCP server para Tribunal Constitucional Chile.

Tools:
- tc_get_sentencia_url(rol_id): URL del PDF de una sentencia TC.
- tc_check_sentencia(rol_id): verifica si la URL legacy retorna PDF
  (HEAD request).

NOTA: el motor de búsqueda full-text del TC está bajo JSF (Java Server
Faces) en tramitacion.tcchile.cl — no scrapeable directo. Para queries
por texto/materia, requeriría Playwright o API formal del TC.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tc_client import TCClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-tc-fallos")
_client = TCClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="tc_get_sentencia_url",
            description=(
                "Construye la URL del descargador legacy del Tribunal "
                "Constitucional de Chile para un ROL específico. Funciona "
                "para sentencias antiguas (rol_id ≲ 12000). Para sentencias "
                "más nuevas, el TC migró a www2.tribunalconstitucional.cl/"
                "wp-content/uploads/YYYY/MM/STC_Rol_N__NNNN-YY_*.pdf — "
                "requiere búsqueda diferente. Sin red."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rol_id": {
                        "type": "integer",
                        "description": (
                            "ID numérico del expediente (ej. 11533 para Rol "
                            "11.533-2021)"
                        ),
                    },
                },
                "required": ["rol_id"],
            },
        ),
        Tool(
            name="tc_check_sentencia",
            description=(
                "Verifica con HEAD si la URL del descargador legacy retorna "
                "un PDF válido para el ROL dado. Útil para detectar IDs "
                "modernos que TC migró a otra ubicación."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rol_id": {"type": "integer"},
                },
                "required": ["rol_id"],
            },
        ),
        Tool(
            name="tc_enumerate_legacy",
            description=(
                "Enumera URLs candidatas de sentencias TC legacy en rango "
                "[from_id, to_id]. Sin red por default. Útil para batch "
                "scrape posterior. IDs >12000 ya no están en legacy."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {"type": "integer", "default": 1},
                    "to_id": {"type": "integer", "default": 12000},
                    "verify": {"type": "boolean", "default": False},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "tc_get_sentencia_url":
        rol_id = int(arguments["rol_id"])
        url = _client.build_legacy_url(rol_id)
        return [TextContent(type="text", text=json.dumps({
            "rol_id": rol_id, "url": url, "type": "legacy_pdf",
            "note": "Usar tc_check_sentencia para confirmar antes de citar.",
        }, ensure_ascii=False, indent=2))]

    if name == "tc_enumerate_legacy":
        results = _client.enumerate_legacy_range(
            from_id=int(arguments.get("from_id", 1)),
            to_id=int(arguments.get("to_id", 12000)),
            verify=bool(arguments.get("verify", False)),
        )
        return [TextContent(type="text", text=json.dumps({
            "count": len(results),
            "sentencias": [
                {"rol_id": r.rol_id, "url": r.url, "type": r.type,
                 "pdf_size_bytes": r.pdf_size}
                for r in results
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "tc_check_sentencia":
        rol_id = int(arguments["rol_id"])
        result = _client.try_legacy_url(rol_id)
        if result is None:
            return [TextContent(type="text", text=json.dumps({
                "rol_id": rol_id, "available": False,
                "note": (
                    "Legacy URL no devuelve PDF. Probablemente sentencia "
                    "moderna migrada a www2.tribunalconstitucional.cl. "
                    "Búsqueda manual necesaria."
                ),
            }, ensure_ascii=False))]
        return [TextContent(type="text", text=json.dumps({
            "rol_id": result.rol_id,
            "available": True,
            "url": result.url,
            "type": result.type,
            "pdf_size_bytes": result.pdf_size,
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
