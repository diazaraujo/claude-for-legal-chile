"""MCP server para búsqueda full-text sobre corpus legal chileno offline.

Tools:
- corpus_search(query, source, year, limit): full-text BM25 con snippet.
- corpus_stats(): cobertura por fuente.
- corpus_get_text(path, max_chars): texto completo de un documento.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .search_client import CorpusSearchClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-corpus-search")

_DB_PATH = os.environ.get("CORPUS_FTS_DB", "")
_client: CorpusSearchClient | None = None


def _get_client() -> CorpusSearchClient:
    global _client
    if _client is None:
        _client = CorpusSearchClient(db_path=_DB_PATH or None)
    return _client


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="corpus_search",
            description=(
                "Búsqueda full-text BM25 sobre corpus legal chileno offline "
                "(~50k documentos PDF extraídos a texto + indexados en "
                "SQLite FTS5). Sintaxis: terms separados por espacio (AND "
                "implícito). Para frase exacta: \"texto literal\". Operador "
                "NEAR(a b N) para proximidad. Fuentes disponibles: "
                "diario-oficial, tc, fne, dt, cmf, sii, tdlc, tdpi, sernac, "
                "subtel, tribunales-ambientales, sec."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Query FTS5. Ejemplos: 'despido injustificado', "
                            "'\"libre competencia\"', 'patente NEAR(rechazo 5)'"
                        ),
                    },
                    "source": {
                        "type": "string",
                        "default": "",
                        "description": (
                            "Filtrar por fuente: tc, fne, dt, cmf, sii, tdlc, "
                            "tdpi, sernac, tribunales-ambientales, etc. Vacío = todas."
                        ),
                    },
                    "year": {
                        "type": "string",
                        "default": "",
                        "description": "Filtrar por año YYYY. Vacío = todos.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Máx resultados (1-50).",
                    },
                    "snippet_len": {
                        "type": "integer",
                        "default": 240,
                        "description": "Caracteres del snippet (40-800).",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="corpus_stats",
            description=(
                "Estadísticas de cobertura del corpus indexado: total de "
                "documentos, breakdown por fuente, tamaño del índice."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="corpus_get_text",
            description=(
                "Lee el texto completo de un documento del corpus dado su "
                "path (típicamente retornado por corpus_search.path). Útil "
                "para citar texto literal verificado tras un hit de búsqueda. "
                "Truncado a max_chars (default 5000)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path absoluto al .pdf.txt",
                    },
                    "max_chars": {
                        "type": "integer",
                        "default": 5000,
                    },
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = _get_client()
    except FileNotFoundError as e:
        return [TextContent(type="text", text=json.dumps(
            {"error": str(e)}, ensure_ascii=False
        ))]

    if name == "corpus_search":
        query = str(arguments.get("query", "")).strip()
        if not query:
            return [TextContent(type="text", text=json.dumps(
                {"error": "query es requerido"}, ensure_ascii=False
            ))]
        try:
            hits = client.search(
                query=query,
                source=str(arguments.get("source", "")),
                year=str(arguments.get("year", "")),
                limit=max(1, min(50, int(arguments.get("limit", 10)))),
                snippet_len=max(40, min(800, int(
                    arguments.get("snippet_len", 240)
                ))),
            )
        except ValueError as e:
            return [TextContent(type="text", text=json.dumps(
                {"error": str(e)}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps({
            "query": query, "n_hits": len(hits),
            "results": [
                {
                    "rank": h.rank, "source": h.source, "year": h.year,
                    "path": h.path, "pdf_path": h.pdf_path,
                    "snippet": h.snippet, "score": h.score,
                } for h in hits
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "corpus_stats":
        return [TextContent(type="text", text=json.dumps(
            client.stats(), ensure_ascii=False, indent=2
        ))]

    if name == "corpus_get_text":
        path = str(arguments.get("path", ""))
        if not path:
            return [TextContent(type="text", text=json.dumps(
                {"error": "path es requerido"}, ensure_ascii=False
            ))]
        text = client.get_full_text(
            path, max_chars=int(arguments.get("max_chars", 5000))
        )
        return [TextContent(type="text", text=json.dumps({
            "path": path,
            "text": text,
            "length": len(text),
        }, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text=json.dumps(
        {"error": f"tool desconocido: {name}"}, ensure_ascii=False
    ))]


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
