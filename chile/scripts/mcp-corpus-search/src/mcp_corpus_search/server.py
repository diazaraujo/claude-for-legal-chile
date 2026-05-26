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
import time
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .search_client import CorpusSearchClient

logger = logging.getLogger(__name__)
server: Server = Server("mcp-corpus-search")

_DB_PATH = os.environ.get("CORPUS_FTS_DB", "")
_client: CorpusSearchClient | None = None

# Telemetry: 1 JSON-line por tool call. Path overridable via CORPUS_TELEMETRY_LOG.
# Vacío explícito = telemetry off. None (default) = ~/.claude-legal-chile/telemetry.jsonl
_TELEMETRY_PATH = os.environ.get("CORPUS_TELEMETRY_LOG")
if _TELEMETRY_PATH is None:
    _TELEMETRY_PATH = str(Path.home() / ".claude-legal-chile" / "telemetry.jsonl")


def _log_telemetry(entry: dict) -> None:
    if not _TELEMETRY_PATH:
        return
    try:
        p = Path(_TELEMETRY_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # nunca romper tool call por telemetry


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
                "NEAR(a b N) para proximidad. Para listar fuentes use "
                "corpus_list_sources."
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
                            "Una sola fuente (tc, fne, dt, cmf, sii, tdlc, "
                            "tdpi, sernac, tribunales-ambientales, leychile-ley, "
                            "leychile-dfl, tc-moderno, etc.). Vacío = todas. "
                            "Para varias use 'sources'."
                        ),
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [],
                        "description": (
                            "Lista de fuentes (OR). Ej. ['tc','tc-moderno'] "
                            "para combinar sentencias TC legacy + modernas."
                        ),
                    },
                    "exclude_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [],
                        "description": (
                            "Lista de fuentes a excluir. Ej. ['diario-oficial'] "
                            "para queries que no quieren publicaciones DO."
                        ),
                    },
                    "exclude_modificadoras": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Solo aplica a fuentes leychile-*. True excluye "
                            "normas cuyo título empieza con 'MODIFICA' "
                            "(retorna la ley BASE, no las que la modifican). "
                            "RECOMENDADO=True cuando buscas la ley vigente."
                        ),
                    },
                    "vigentes_only": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Solo aplica a fuentes leychile-*. True excluye "
                            "normas marcadas como derogadas en BCN catalog. "
                            "Combinable con exclude_modificadoras para citas seguras."
                        ),
                    },
                    "year": {
                        "type": "string",
                        "default": "",
                        "description": "Año exacto YYYY. Vacío = todos.",
                    },
                    "year_from": {
                        "type": "string",
                        "default": "",
                        "description": (
                            "Inicio de rango YYYY. Combinable con year_to. "
                            "Ignorado si se especifica 'year'."
                        ),
                    },
                    "year_to": {
                        "type": "string",
                        "default": "",
                        "description": "Fin de rango YYYY.",
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
                    "rerank": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Re-rankea con Claude Haiku post-BM25. Pide a "
                            "Haiku que ordene los top-4x por relevancia "
                            "semántica real al query. Cuesta ~$0.0002 por "
                            "llamada. Requiere ANTHROPIC_API_KEY en env. "
                            "Útil para queries naturales ambiguas; "
                            "innecesario para queries con keywords precisos."
                        ),
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="corpus_recent",
            description=(
                "Últimos N documentos en una fuente (orden cronológico "
                "inverso). Útil para 'qué sentencias TC son recientes', "
                "'qué circulares SII salieron en 2025', etc. Sin query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "default": ""},
                    "sources": {
                        "type": "array", "items": {"type": "string"},
                        "default": [],
                    },
                    "year_from": {
                        "type": "string", "default": "",
                        "description": "Mínimo año YYYY (ej. '2024')",
                    },
                    "limit": {"type": "integer", "default": 10},
                },
            },
        ),
        Tool(
            name="corpus_list_sources",
            description=(
                "Lista las fuentes disponibles en el índice con: nombre, "
                "n_docs, year_min, year_max. Útil para discovery antes "
                "de filtrar searches."
            ),
            inputSchema={"type": "object", "properties": {}},
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
        Tool(
            name="corpus_cite",
            description=(
                "Genera cita formal verificable desde el path de un doc del "
                "corpus. Conoce patrones de naming de cada fuente y extrae "
                "rol/edición/año. Ejemplos: "
                "tc-moderno/STC_Rol_N_17_083-25_INA.pdf → 'STC Rol N° 17.083-2025 (INA)'; "
                "tdlc/sentencia-159-2017-... → 'TDLC Sentencia N° 159/2017'; "
                "leychile/ley/1199623.xml → 'Ley (idNorma BCN 1199623)'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path del corpus (.pdf.txt o .pdf o .xml.txt)",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="corpus_related",
            description=(
                "Encuentra los N documentos más similares al dado, vía "
                "embeddings semánticos bge-m3 (Ollama local). Score = "
                "cosine similarity, rango -1..1. Útil para 'qué sentencias "
                "tratan temas parecidos a este caso' o 'jurisprudencia "
                "relacionada con esta resolución'. El doc query debe estar "
                "indexado (o se computa on-the-fly via Ollama)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path del doc base (.pdf.txt o .xml.txt)",
                    },
                    "limit": {"type": "integer", "default": 5},
                    "same_source_only": {
                        "type": "boolean", "default": False,
                        "description": "True = restringe a la misma fuente del query",
                    },
                    "min_score": {
                        "type": "number", "default": 0.5,
                        "description": "Score cosine mínimo (0..1) para incluir",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="corpus_embeddings_status",
            description=(
                "Estado del índice de embeddings: cuántos docs tienen "
                "embedding bge-m3, breakdown por fuente, % cobertura. "
                "Útil para saber si corpus_related funciona bien para "
                "una fuente específica."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="corpus_search_articulos",
            description=(
                "Búsqueda por ARTÍCULO específico de leyes/decretos chilenos "
                "(218k artículos extraídos de XMLs LeyChile). Granularidad "
                "más fina que corpus_search. Combina query + filtros leychile_code "
                "y articulo_num. Ej: query='causales término' + leychile_code=207436 "
                "(Código Trabajo) → retorna artículos 159, 161, 168 etc. con "
                "esa frase. Para citar 'Art. X de Ley Y' verificable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", "default": "",
                        "description": "FTS5 query (puede vacío si filtras por num/code)",
                    },
                    "leychile_code": {
                        "type": "integer",
                        "description": "idNorma BCN del documento (filtra a artículos de esa norma)",
                    },
                    "articulo_num": {
                        "type": "string", "default": "",
                        "description": "Número exacto del artículo (ej '161', '1 bis')",
                    },
                    "limit": {"type": "integer", "default": 10},
                    "snippet_len": {"type": "integer", "default": 240},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="corpus_expand_query",
            description=(
                "Reformula query en lenguaje natural a términos legales "
                "chilenos precisos para FTS5. Útil cuando el usuario pregunta "
                "en jerga coloquial. Ej: 'puede despedir embarazada' → "
                "'fuero maternal OR \"artículo 174\" OR despido OR causal'. "
                "Returns: {fts_query, terms, rationale}. Sugerencia de uso: "
                "primero corpus_expand_query(natural) → luego corpus_search("
                "fts_query, ...). Requiere ANTHROPIC_API_KEY (~$0.0001/llamada)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "natural_query": {
                        "type": "string",
                        "description": "Query en lenguaje natural del usuario",
                    },
                    "max_terms": {
                        "type": "integer", "default": 8,
                        "description": "Máx términos a generar (3-15)",
                    },
                },
                "required": ["natural_query"],
            },
        ),
        Tool(
            name="corpus_verify_quote",
            description=(
                "Verifica que un texto literal aparece en un documento "
                "del corpus. Anti-hallucination crítico: antes de citar "
                "verbatim un párrafo de una sentencia/ley, llamar este "
                "tool para confirmar. Returns: found, position, "
                "context_before/after, match_type (exact|fuzzy|not_found). "
                "fuzzy=True (default) tolera errores OCR de whitespace/case."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto literal a verificar en el doc",
                    },
                    "path": {
                        "type": "string",
                        "description": "Path al .pdf.txt o .xml.txt (del search)",
                    },
                    "fuzzy": {
                        "type": "boolean", "default": True,
                        "description": "True: normaliza whitespace/case (recomendado para OCR)",
                    },
                    "context_chars": {
                        "type": "integer", "default": 200,
                        "description": "Chars de contexto before/after el match",
                    },
                },
                "required": ["text", "path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    t0 = time.time()
    err = None
    n_results = None
    try:
        result = await _call_tool_impl(name, arguments)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        raise
    finally:
        try:
            if not err and result:
                # Intentar extraer n_hits/n_results del body
                try:
                    body = json.loads(result[0].text)
                    n_results = body.get("n_hits") or body.get("n_results") or body.get("length")
                except (json.JSONDecodeError, AttributeError, KeyError, IndexError):
                    pass
            _log_telemetry({
                "ts": time.time(),
                "tool": name,
                "args_keys": sorted(arguments.keys()),
                "query": str(arguments.get("query", arguments.get("natural_query", arguments.get("text", ""))))[:200],
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "n_results": n_results,
                "error": err,
            })
        except Exception:
            pass
    return result


async def _call_tool_impl(name: str, arguments: dict[str, Any]) -> list[TextContent]:
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
                sources=arguments.get("sources") or None,
                exclude_sources=arguments.get("exclude_sources") or None,
                exclude_modificadoras=bool(arguments.get("exclude_modificadoras", False)),
                vigentes_only=bool(arguments.get("vigentes_only", False)),
                year=str(arguments.get("year", "")),
                year_from=str(arguments.get("year_from", "")),
                year_to=str(arguments.get("year_to", "")),
                limit=max(1, min(50, int(arguments.get("limit", 10)))),
                snippet_len=max(40, min(800, int(
                    arguments.get("snippet_len", 240)
                ))),
                rerank=bool(arguments.get("rerank", False)),
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

    if name == "corpus_recent":
        hits = client.recent(
            source=str(arguments.get("source", "")),
            sources=arguments.get("sources") or None,
            year_from=str(arguments.get("year_from", "")),
            limit=max(1, min(50, int(arguments.get("limit", 10)))),
        )
        return [TextContent(type="text", text=json.dumps({
            "n_hits": len(hits),
            "results": [
                {
                    "rank": h.rank, "source": h.source, "year": h.year,
                    "path": h.path, "pdf_path": h.pdf_path,
                    "snippet": h.snippet,
                } for h in hits
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "corpus_list_sources":
        return [TextContent(type="text", text=json.dumps(
            client.list_sources(), ensure_ascii=False, indent=2
        ))]

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

    if name == "corpus_cite":
        path = str(arguments.get("path", ""))
        if not path:
            return [TextContent(type="text", text=json.dumps(
                {"error": "path es requerido"}, ensure_ascii=False
            ))]
        c = client.cite(path)
        return [TextContent(type="text", text=json.dumps({
            "source": c.source,
            "citation": c.citation,
            "long_citation": c.long_citation,
            "rol": c.rol,
            "fecha": c.fecha,
            "extra": c.extra or {},
        }, ensure_ascii=False, indent=2))]

    if name == "corpus_related":
        path = str(arguments.get("path", ""))
        if not path:
            return [TextContent(type="text", text=json.dumps(
                {"error": "path es requerido"}, ensure_ascii=False
            ))]
        hits = client.related(
            path=path,
            limit=max(1, min(20, int(arguments.get("limit", 5)))),
            same_source_only=bool(arguments.get("same_source_only", False)),
            min_score=float(arguments.get("min_score", 0.5)),
        )
        return [TextContent(type="text", text=json.dumps({
            "query_path": path, "n_hits": len(hits),
            "results": [
                {
                    "rank": h.rank, "source": h.source, "year": h.year,
                    "path": h.path, "pdf_path": h.pdf_path,
                    "snippet": h.snippet, "cosine_similarity": h.score,
                } for h in hits
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "corpus_embeddings_status":
        return [TextContent(type="text", text=json.dumps(
            client.embeddings_status(), ensure_ascii=False, indent=2
        ))]

    if name == "corpus_search_articulos":
        results = client.search_articulos(
            query=str(arguments.get("query", "")),
            leychile_code=arguments.get("leychile_code"),
            articulo_num=str(arguments.get("articulo_num", "")),
            limit=max(1, min(50, int(arguments.get("limit", 10)))),
            snippet_len=max(40, min(800, int(arguments.get("snippet_len", 240)))),
        )
        return [TextContent(type="text", text=json.dumps({
            "n_hits": len(results), "results": results,
        }, ensure_ascii=False, indent=2))]

    if name == "corpus_expand_query":
        natural = str(arguments.get("natural_query", "")).strip()
        if not natural:
            return [TextContent(type="text", text=json.dumps(
                {"error": "natural_query es requerido"}, ensure_ascii=False
            ))]
        result = client.expand_query(
            natural_query=natural,
            max_terms=max(3, min(15, int(arguments.get("max_terms", 8)))),
        )
        return [TextContent(type="text", text=json.dumps(
            result, ensure_ascii=False, indent=2
        ))]

    if name == "corpus_verify_quote":
        result = client.verify_quote(
            text=str(arguments.get("text", "")),
            path=str(arguments.get("path", "")),
            fuzzy=bool(arguments.get("fuzzy", True)),
            context_chars=int(arguments.get("context_chars", 200)),
        )
        return [TextContent(type="text", text=json.dumps(
            result, ensure_ascii=False, indent=2
        ))]

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
