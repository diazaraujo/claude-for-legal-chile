"""MCP server para Fiscalía Nacional Económica Chile.

Tools:
- fne_list_posts(category, page, per_page): lista posts por categoría.
- fne_get_post(post_id): obtiene metadata de un post.
- fne_extract_pdfs(html): extrae URLs de PDFs embedded.
- fne_list_categories(): listado de categorías legales con IDs.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .fne_client import FNEClient, LEGAL_CATEGORIES

logger = logging.getLogger(__name__)
server: Server = Server("mcp-fne")
_client = FNEClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fne_list_posts",
            description=(
                "Lista posts FNE en una categoría (paginado WP REST). "
                "Retorna metadata (id, fecha, título, link, categorías) sin "
                "contenido — WP REST esconde content.rendered en la mayoría "
                "de posts antiguos. Para el documento real, ver el link."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "integer",
                        "description": (
                            "ID de categoría (ej. 151=Dictamen, "
                            "106=Jurisprudencia, 98=Defensa Libre Competencia)"
                        ),
                    },
                    "page": {"type": "integer", "default": 1},
                    "per_page": {"type": "integer", "default": 20},
                },
                "required": ["category"],
            },
        ),
        Tool(
            name="fne_get_post",
            description="Obtiene un post FNE por ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "integer"},
                },
                "required": ["post_id"],
            },
        ),
        Tool(
            name="fne_list_categories",
            description=(
                "Listado de las 15 categorías FNE legal-relevantes (con "
                "conteos aproximados de posts por categoría)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "fne_list_posts":
        cat = int(arguments["category"])
        page = int(arguments.get("page", 1))
        per_page = max(1, min(100, int(arguments.get("per_page", 20))))
        try:
            posts, total_pages = _client.list_posts_by_category(
                cat, page=page, per_page=per_page
            )
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"error": str(e)}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps({
            "category": cat, "page": page, "total_pages": total_pages,
            "n_posts": len(posts),
            "posts": [
                {
                    "post_id": p.post_id, "date": p.date, "slug": p.slug,
                    "title": p.title, "link": p.link,
                    "categorias": p.categorias,
                } for p in posts
            ],
        }, ensure_ascii=False, indent=2))]

    if name == "fne_get_post":
        post = _client.get_post(int(arguments["post_id"]))
        if not post:
            return [TextContent(type="text", text=json.dumps(
                {"error": "post no encontrado"}, ensure_ascii=False
            ))]
        return [TextContent(type="text", text=json.dumps({
            "post_id": post.post_id, "date": post.date,
            "title": post.title, "link": post.link,
            "categorias": post.categorias,
        }, ensure_ascii=False, indent=2))]

    if name == "fne_list_categories":
        return [TextContent(type="text", text=json.dumps({
            "categorias_legales": LEGAL_CATEGORIES,
            "note": (
                "IDs catalogados manualmente desde el index FNE. Usar con "
                "fne_list_posts(category=<id>)."
            ),
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
