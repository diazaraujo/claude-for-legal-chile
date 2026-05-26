# mcp-corpus-search

MCP server para búsqueda full-text + semántica sobre corpus legal chileno offline. Expone 12 tools sobre ~50k documentos PDF/XML extraídos (sentencias TC/TDLC/Tribunales Ambientales/TDPI, leyes/DFL/DL de BCN LeyChile, circulares SII/CMF, dictámenes DT, dictámenes FNE, diario oficial). Índice SQLite FTS5 (BM25) + embeddings bge-m3 + chunking por artículo.

## Quick start

```bash
cd chile/scripts/mcp-corpus-search
uv venv && uv pip install -e .
CORPUS_FTS_DB=/path/to/corpus.fts.sqlite3 .venv/bin/mcp-corpus-search
```

Configurar como MCP server en Claude Code (`.mcp.json` o equivalente):

```json
{
  "mcpServers": {
    "corpus-search": {
      "command": ".venv/bin/mcp-corpus-search",
      "env": {
        "CORPUS_FTS_DB": "/Volumes/SSD ADA/claude-for-legal-chile/chile/data/_index/corpus.fts.sqlite3",
        "ANTHROPIC_API_KEY": "sk-..."
      }
    }
  }
}
```

`ANTHROPIC_API_KEY` es opcional: necesario sólo para tools con LLM (`corpus_search` con `rerank=True`, `corpus_summarize`, `corpus_expand_query`). El resto funciona puramente offline.

## Tools

### Discovery
| Tool | Propósito |
|------|-----------|
| `corpus_list_sources` | Lista fuentes disponibles con n_docs, year_min, year_max |
| `corpus_stats` | Breakdown global por fuente |
| `corpus_embeddings_status` | Cobertura de embeddings bge-m3 |

### Búsqueda
| Tool | Propósito |
|------|-----------|
| `corpus_search` | FTS5 BM25 con filtros source/year/vigentes/modificadoras. `rerank=True` → Haiku re-ordena top-4×N |
| `corpus_search_articulos` | Granular: por artículo (218k chunks XML LeyChile) |
| `corpus_recent` | Últimos N en una fuente (cronológico inverso, sin query) |
| `corpus_related` | Similares vía embeddings bge-m3 (cosine) |

### Lectura y citas
| Tool | Propósito |
|------|-----------|
| `corpus_get_text` | Texto completo del doc (truncado a max_chars) |
| `corpus_cite` | Cita formal verificada desde path (STC Rol N° X-YYYY, TDLC Sentencia N°/AAAA, etc.) |
| `corpus_verify_quote` | Anti-hallucination: confirma que un párrafo literal aparece en el doc (fuzzy OCR-tolerant) |

### LLM-augmented (requiere ANTHROPIC_API_KEY)
| Tool | Propósito |
|------|-----------|
| `corpus_expand_query` | Reformula query en lenguaje natural a términos legales FTS5 |
| `corpus_summarize` | Resumen Haiku estructurado de un doc largo (tipo, partes, decisión, fundamento) |

## Patrón típico

Para preguntas en lenguaje natural:

```
1. corpus_expand_query("puede mi empresa despedir embarazada")
   → fts_query: '"fuero maternal" OR "artículo 174" OR "despido embarazada"'

2. corpus_search(query=fts_query, sources=["leychile-ley","leychile-dfl"],
                 exclude_modificadoras=True, vigentes_only=True, rerank=True)
   → top hits con citas verificables

3. corpus_get_text(path=hit.path)  o  corpus_summarize(path=hit.path)

4. Antes de citar verbatim:
   corpus_verify_quote(text="literal a citar", path=hit.path, fuzzy=True)
```

## Telemetry

Cada tool call se logguea como JSON-line a `~/.claude-legal-chile/telemetry.jsonl` (override con env `CORPUS_TELEMETRY_LOG`; vacío = off). Schema: `ts, tool, args_keys, query, latency_ms, n_results, error`.

Inspección:

```bash
python3 chile/scripts/telemetry-stats.py            # default path
python3 chile/scripts/telemetry-stats.py --tail 100 # último N
```

Reporta p50/p95 por tool, top queries, top errores.

## Filtros de vigencia (críticos para citar)

Las fuentes `leychile-*` indexan **todas** las normas catalogadas en BCN — incluyendo las que MODIFICAN otras. Para queries que buscan la **ley vigente base** (no las que la modifican):

- `exclude_modificadoras=True` — excluye títulos que empiezan con "MODIFICA"
- `vigentes_only=True` — excluye normas marcadas como derogadas en catalog BCN

Recomendado combinar ambos para citas. Catálogo de vigencia vive en `chile/normativa/catalogo/` (frontmatter `derogado:` por norma).

## Tests

```bash
chile/scripts/tests/test_golden_queries.py
```

12 golden cases verificando que queries conocidas retornan los idNorma esperados (Código Trabajo DFL 1/2002 idNorma 207436, Ley 19.628 idNorma 141599 — NO 199093 que modifica, etc.).

## Estado actual del corpus

Ver `chile/data/_index/corpus.fts.sqlite3`. Stats vía `corpus_stats`. Indexación incremental por fuente vía scripts en `chile/scripts/build-*-index.py`.

## Licencia

Apache 2.0 (mismo que upstream anthropics/claude-for-legal).
