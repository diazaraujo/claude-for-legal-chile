# Instalación del MCP `mcp-bcn-leychile`

Servidor MCP local que expone el catálogo BCN indexado + acceso en
tiempo real a leychile.cl como tools para Claude Code.

## Requisitos

- Python ≥3.11
- Catálogo SQLite indexado en `chile/normativa/index/catalogo.sqlite3`
  (se construye con `python3 chile/scripts/index/build-sqlite-catalog.py`
  desde el root del repo)

## Instalar el server

Desde el root del repo `claude-for-legal-chile`:

```bash
cd chile/scripts/mcp
python3.11 -m venv .venv
.venv/bin/pip install -e .
```

Esto deja el binario en `chile/scripts/mcp/.venv/bin/mcp-bcn-leychile`.

## Registrar en Claude Code

Desde **cualquier directorio**, una sola vez:

```bash
claude mcp add bcn-leychile \
  /Volumes/SSD\ ADA/claude-for-legal-chile/chile/scripts/mcp/.venv/bin/mcp-bcn-leychile
```

(reemplazar el path por donde esté el clon del repo)

Scope `local` (default) → solo este usuario. Usar `-s user` si querés
disponible en todos los workspaces.

Verificar:

```bash
claude mcp get bcn-leychile
```

## Tools expuestas

| Tool | Función | Lat. típica |
|---|---|---|
| `catalog_stats` | Totales del catálogo + por tipo | <10ms |
| `lookup_norma` | Resuelve por tipo+numero / leychile_code / slug | <10ms |
| `search_normas` | LIKE por título, ordenado por capa | <50ms |
| `get_relaciones` | Outgoing/incoming desde grafo BCN | <50ms |
| `bcn_get_norma` | Metadata + estructura jerárquica (BCN remoto) | 200-1000ms |
| `bcn_check_vigencia` | Vigencia actual (BCN remoto) | 200-1000ms |
| `bcn_get_xml` | XML estructural completo (BCN remoto) | 500-2000ms |

## Reconstruir el índice SQLite

Después de scrapear más normas, regenerar:

```bash
cd <repo-root>
python3 chile/scripts/index/build-sqlite-catalog.py
```

(idempotente — sobrescribe el SQLite anterior; lee todo el catálogo y
las relaciones JSONL)

## Override de la BD por env var

Por default el server usa `chile/normativa/index/catalogo.sqlite3`. Si
querés apuntar a otra ubicación:

```bash
claude mcp add bcn-leychile \
  -e MCP_BCN_DB=/path/a/tu/catalogo.sqlite3 \
  /path/al/binario/mcp-bcn-leychile
```

## Troubleshooting

- **`catalog_stats` devuelve `{"available": 0}`**: el SQLite no existe.
  Correr el indexer.
- **Tools BCN remotas timeout**: leychile.cl puede estar lento; reintentar.
- **`lookup_norma` no encuentra una norma**: caer a `bcn_get_norma` con
  el `id_norma` (leychile_code).
