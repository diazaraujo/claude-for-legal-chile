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

logger = logging.getLogger(__name__)

server: Server = Server("mcp-bcn-leychile")
_client = BCNClient()


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
