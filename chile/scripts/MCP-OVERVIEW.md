# MCP Connectors para Claude Legal Chile

Inventario de servidores MCP disponibles para que Claude consulte
fuentes primarias chilenas en tiempo real.

## Estado v0.7 (2026-05-22)

### Tier 1 — Normativos ✅

| Conector | Funcionalidad | Estado | Tools |
|---|---|---|---|
| [`mcp-bcn-leychile`](mcp/) | Texto + estructura + grafo BCN + catálogo local | ✅ Producción | 8 |
| [`mcp-diario-oficial`](mcp-diario-oficial/) | Publicaciones diarias DO | ✅ Funcional | 4 |
| [`mcp-sii-juris`](mcp-sii-juris/) | Circulares SII por año | ✅ Funcional | 3 |
| [`mcp-cgr-dictamenes`](mcp-cgr-dictamenes/) | Dictámenes CGR por número/año | ✅ Funcional | 2 |
| [`mcp-tc-fallos`](mcp-tc-fallos/) | Sentencias TC legacy (id ≤ 12k) | 🟡 Parcial | 2 |
| [`mcp-pjud`](mcp-pjud/) | Jurisprudencia general PJUD | 🔴 Stub | 2 |

### Tier 2 — Pendientes (próximas fases)

| Conector | Fuente | Bloqueo |
|---|---|---|
| `mcp-dt-dictamenes` | Dirección del Trabajo | CMS sin IDs predecibles |
| `mcp-sernac` | Consumidor | Investigar API |
| `mcp-sbif` / `mcp-cmf` | Financiero | API CMF |
| `mcp-tgr` | Tesorería Gral | API formal pendiente |
| `mcp-aduana` | Aduana | Investigar |
| `mcp-conadi` | Indígenas | HTML público |

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

```bash
cd chile/scripts
for d in mcp mcp-diario-oficial mcp-sii-juris mcp-cgr-dictamenes mcp-tc-fallos mcp-pjud; do
  (cd $d && python3.11 -m venv .venv && .venv/bin/pip install -e .)
done
```

Registro en Claude Code:

```bash
REPO="/Volumes/SSD ADA/claude-for-legal-chile/chile/scripts"
claude mcp add bcn-leychile "$REPO/mcp/.venv/bin/mcp-bcn-leychile"
claude mcp add diario-oficial "$REPO/mcp-diario-oficial/.venv/bin/mcp-diario-oficial"
claude mcp add sii-juris "$REPO/mcp-sii-juris/.venv/bin/mcp-sii-juris"
claude mcp add cgr-dictamenes "$REPO/mcp-cgr-dictamenes/.venv/bin/mcp-cgr-dictamenes"
claude mcp add tc-fallos "$REPO/mcp-tc-fallos/.venv/bin/mcp-tc-fallos"
# mcp-pjud es stub, instalar solo si quieres tener pjud_status disponible
```
