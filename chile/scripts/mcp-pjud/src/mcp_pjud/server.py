"""MCP server STUB para PJUD jurisprudencia.

Estado: stub. juris.pjud.cl requiere browser automation (reCAPTCHA).
Ver README.md para vías de implementación.

Por ahora expone una tool `pjud_buscador_url` que construye la URL del
buscador para que el usuario haga la búsqueda manual.
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.parse
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)
server: Server = Server("mcp-pjud")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="pjud_buscador_url",
            description=(
                "Construye la URL del Portal Unificado de Sentencias del "
                "Poder Judicial de Chile (juris.pjud.cl) con los filtros "
                "indicados. NOTA: el portal requiere reCAPTCHA; este tool "
                "solo devuelve la URL — la búsqueda real debe hacerla un "
                "humano o un agente con browser headless."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rol": {
                        "type": "string",
                        "description": "ROL de la causa (ej. '12345-2024')",
                    },
                    "query": {
                        "type": "string",
                        "description": "Texto libre",
                    },
                    "tribunal": {
                        "type": "string",
                        "description": "corte_suprema | corte_apelaciones | ...",
                    },
                },
            },
        ),
        Tool(
            name="pjud_status",
            description=(
                "Devuelve el estado del conector PJUD. Actualmente STUB — "
                "no soporta queries programáticas por restricción "
                "reCAPTCHA del portal."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "pjud_buscador_url":
        params: dict[str, str] = {}
        if (rol := arguments.get("rol")):
            params["rol"] = rol
        if (q := arguments.get("query")):
            params["q"] = q
        if (t := arguments.get("tribunal")):
            params["tribunal"] = t
        url = "https://juris.pjud.cl/busqueda"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return [TextContent(type="text", text=json.dumps({
            "url": url,
            "note": (
                "Portal requiere reCAPTCHA. Abrir URL en navegador para "
                "completar la búsqueda."
            ),
        }, ensure_ascii=False))]

    if name == "pjud_status":
        return [TextContent(type="text", text=json.dumps({
            "status": "stub",
            "reason": "juris.pjud.cl es SPA con reCAPTCHA — bloquea HTTP simple",
            "alternatives": [
                "Playwright headless + 2captcha",
                "API formal via Corporación Admin PJUD (contacto Unholster)",
                "Compendios jurisprudencia DDHH (sub-paths sin reCAPTCHA)",
                "Tribunal Constitucional (separado, HTML público)",
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
