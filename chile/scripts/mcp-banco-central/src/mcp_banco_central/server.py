"""MCP server Banco Central de Chile (BDE)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .bcch_client import BCChClient, SERIES_COMUNES

logger = logging.getLogger(__name__)
server: Server = Server("mcp-banco-central")
_client: BCChClient | None = None


def _get_client() -> BCChClient:
    global _client
    if _client is None:
        _client = BCChClient()
    return _client


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bcch_get_series",
            description=(
                "Obtiene observaciones (fecha + valor) de una serie del "
                "Banco Central de Chile (BDE). Códigos comunes:\n"
                "- uf_diaria, uf_mensual\n"
                "- dolar_observado\n"
                "- tpm (Tasa Política Monetaria)\n"
                "- ipc_mensual (variación %)\n"
                "- utm_mensual\n"
                "También acepta código BCCh crudo (ej. F073.UFF.DIA.Z.Z.0.D)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Alias (uf_diaria, dolar_observado, tpm, etc.) o "
                            "código BCCh directo"
                        ),
                    },
                    "firstdate": {
                        "type": "string",
                        "description": "YYYY-MM-DD (opcional)",
                    },
                    "lastdate": {
                        "type": "string",
                        "description": "YYYY-MM-DD (opcional)",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="bcch_uf_hoy",
            description=(
                "Última observación de UF diaria. Útil para cálculo de "
                "reajustes, indemnizaciones, contratos en UF."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bcch_dolar_hoy",
            description="Última cotización del dólar observado.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bcch_tpm_hoy",
            description=(
                "Tasa de Política Monetaria vigente (relevante para "
                "intereses, mora, refinanciamientos)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bcch_search_series",
            description=(
                "Lista series disponibles en BDE por frecuencia (DAILY, "
                "MONTHLY, QUARTERLY, ANNUAL)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "frequency": {
                        "type": "string",
                        "enum": ["DAILY", "MONTHLY", "QUARTERLY", "ANNUAL"],
                    },
                },
                "required": ["frequency"],
            },
        ),
    ]


def _resolve_code(code: str) -> str:
    return SERIES_COMUNES.get(code, code)


def _obs_to_dict(obs) -> dict:
    return {"date": obs.date, "value": obs.value}


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = _get_client()
    except ValueError as e:
        return [TextContent(type="text", text=json.dumps(
            {"error": str(e)}, ensure_ascii=False
        ))]

    if name == "bcch_get_series":
        code = _resolve_code(arguments["code"])
        firstdate = arguments.get("firstdate", "")
        lastdate = arguments.get("lastdate", "")
        try:
            s = client.get_series(code, firstdate, lastdate)
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps({
            "code": s.code, "titulo": s.titulo,
            "count": len(s.observaciones),
            "observaciones": [_obs_to_dict(o) for o in s.observaciones],
        }, ensure_ascii=False, indent=2))]

    if name in ("bcch_uf_hoy", "bcch_dolar_hoy", "bcch_tpm_hoy"):
        method = {
            "bcch_uf_hoy": client.get_uf_hoy,
            "bcch_dolar_hoy": client.get_dolar_hoy,
            "bcch_tpm_hoy": client.get_tpm_hoy,
        }[name]
        try:
            obs = method()
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False
            ))]
        if obs is None:
            return [TextContent(type="text", text=json.dumps(
                {"error": "Sin observaciones disponibles"}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps(
            _obs_to_dict(obs), ensure_ascii=False
        ))]

    if name == "bcch_search_series":
        freq = arguments["frequency"]
        try:
            series = client.search_series(freq)
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps({
            "frequency": freq, "count": len(series), "series": series[:100],
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
