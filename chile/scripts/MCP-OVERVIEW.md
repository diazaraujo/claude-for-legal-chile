# MCP Connectors para Claude Legal Chile

Inventario de servidores MCP disponibles para que Claude consulte
fuentes primarias chilenas en tiempo real.

## Estado v0.7.2 (2026-05-22)

### Tier 1 — Conectores MCP ✅

| Conector | Funcionalidad | Estado | Tools |
|---|---|---|---|
| [`mcp-bcn-leychile`](mcp/) | Texto + estructura + grafo BCN + catálogo local | ✅ Producción | 8 |
| [`mcp-diario-oficial`](mcp-diario-oficial/) | Publicaciones diarias DO | ✅ Funcional | 4 |
| [`mcp-sii-juris`](mcp-sii-juris/) | Circulares SII por año | ✅ Funcional | 3 |
| [`mcp-cgr-dictamenes`](mcp-cgr-dictamenes/) | Dictámenes CGR (antiguo + moderno E{NNNNNN}N{YY}) | ✅ Funcional | 2 |
| [`mcp-cmf`](mcp-cmf/) | NCG + Circulares CMF (financiero) | ✅ Funcional | 2 |
| [`mcp-dt-dictamenes`](mcp-dt-dictamenes/) | DT con period_id enumerator (4.974 dictámenes) | ✅ Funcional | 4 |
| [`mcp-sernac`](mcp-sernac/) | Circulares + Dictámenes interpretativos SERNAC | ✅ Funcional | 1 |
| [`mcp-banco-central`](mcp-banco-central/) | BDE BCCh — UF, dólar, TPM, IPC, UTM (req. registro) | ✅ Funcional | 5 |
| [`mcp-bcn-tramitacion`](mcp-bcn-tramitacion/) | Historia de la Ley — tramitación legislativa | ✅ Funcional | 3 |
| [`mcp-fne`](mcp-fne/) | FNE WP REST — 13k posts, 15 categorías legal | ✅ Funcional | 3 |
| [`mcp-tdlc`](mcp-tdlc/) | TDLC sentencias y consultas | ✅ Funcional | 2 |
| [`mcp-tc-fallos`](mcp-tc-fallos/) | Sentencias TC legacy (id ≤ 12k) | 🟡 Parcial | 2 |
| [`mcp-pjud`](mcp-pjud/) | Jurisprudencia general PJUD | 🔴 Stub | 2 |
| [`mcp-ine`](mcp-ine/) | INE (series ya en BCCh) | 🔴 Stub (doc) | 0 |

### MCP corpus-search — búsqueda offline + semantic + citas

[`mcp-corpus-search`](mcp-corpus-search/) expone 8 tools al runtime
Claude sobre el corpus indexado:

| Tool | Función |
|---|---|
| `corpus_search` | BM25 FTS5 con multi-source, year range, exclude |
| `corpus_recent` | Últimos N por fuente sin query |
| `corpus_list_sources` | Catálogo con n_docs + año min/max |
| `corpus_stats` | Totales + breakdown |
| `corpus_get_text` | Texto verbatim para citas |
| `corpus_cite` | Path → cita formal (ej. "STC Rol N° 17.083-2025 (INA)") |
| `corpus_related` | Cosine similarity bge-m3 (Ollama local) |
| `corpus_embeddings_status` | Cobertura del índice semántico |

### Bulk downloaders + corpus offline

13 fuentes bajadas a `chile/data/`. Total: **54.792+ documentos / 29.72 GB**.
- FTS5 BM25 sobre 46.432 docs (902 MB texto + 1.24 GB índice)
- Embeddings bge-m3 (Ollama local) — indexing on-going
- 4.117 PDFs solo-imagen recuperados via Tesseract OCR (en curso)
- Texto íntegro 1.100+ XMLs LeyChile via Zyte API
- 49 últimas sentencias TC modernas via JSF reverse-engineered

Ver [`bulk-downloaders/README.md`](bulk-downloaders/README.md) para detalle.

```bash
# CLI legacy (FTS5 simple)
python3 chile/scripts/search.py "huelga ilegal" --source dt
python3 chile/scripts/search.py "patente invención" --source tdpi
```

## Bloqueos técnicos comunes

1. **reCAPTCHA en SPAs** (PJUD juris.pjud.cl): bloquea HTTP simple.
   Requiere Playwright + 2captcha service.
2. **JSF postbacks** (Tribunal Constitucional búsqueda):
   tramitacion.tcchile.cl usa ViewState — no scrapeable directo.
3. **CMS con IDs internos no-predecibles** (DT): `articles-NNNNN_recurso`
   sin mapping a número de dictamen.

## Patrón de diseño

Todos los MCPs nuevos siguen el mismo template:

```
mcp-{nombre}/
├── pyproject.toml          # mcp>=0.9.0, console script main
├── README.md
├── src/mcp_{nombre}/
│   ├── __init__.py
│   ├── {servicio}_client.py  # Lógica HTTP + parsing
│   └── server.py             # MCP server con tools
└── tests/                  # unittest puro, sin pytest
```

**Principio común**: NO descargar contenido a disco. Devolver URLs
canónicas a Claude para que él consulte. Cache solo para HTML index.

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: cada conector
solo retorna IDs/URLs que la fuente oficial confirma.

## Instalación rápida (todos los MCPs)

Script automatizado que crea venvs aislados + registra en Claude Code:

```bash
bash chile/scripts/install-all-mcps.sh           # instala + registra
bash chile/scripts/install-all-mcps.sh --no-register   # solo instala
```

Manual:

```bash
cd chile/scripts
for d in mcp mcp-diario-oficial mcp-sii-juris mcp-cgr-dictamenes mcp-cmf mcp-tc-fallos mcp-pjud; do
  (cd $d && python3.11 -m venv .venv && .venv/bin/pip install -e .)
done

REPO="$(pwd)"
claude mcp add bcn-leychile "$REPO/mcp/.venv/bin/mcp-bcn-leychile"
claude mcp add diario-oficial "$REPO/mcp-diario-oficial/.venv/bin/mcp-diario-oficial"
claude mcp add sii-juris "$REPO/mcp-sii-juris/.venv/bin/mcp-sii-juris"
claude mcp add cgr-dictamenes "$REPO/mcp-cgr-dictamenes/.venv/bin/mcp-cgr-dictamenes"
claude mcp add cmf "$REPO/mcp-cmf/.venv/bin/mcp-cmf"
claude mcp add tc-fallos "$REPO/mcp-tc-fallos/.venv/bin/mcp-tc-fallos"
# pjud es stub — instalar solo si quieres tener pjud_status disponible
```
