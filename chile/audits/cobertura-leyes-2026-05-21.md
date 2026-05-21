---
fecha: 2026-05-21
herramienta: chile/scripts/index/build-sqlite-catalog.py + query SQL
---

# Auditoría cobertura — Leyes por rango numérico

Catálogo actual: **5.273 entries `tipo=ley`** (capa 1+2+3 combinadas).

## Distribución

| Rango      | Tenemos | Posible | % |
|---|---:|---:|---:|
| 1..999     | 15 | 999 | 2% |
| 1000..4999 | 283 | 4000 | 7% |
| 5000..9999 | 531 | 5000 | 11% |
| 10000..14999 | 1043 | 5000 | 21% |
| 15000..17999 | 907 | 3000 | 30% |
| **18000..20999** | **2155** | **3000** | **72%** ✓ |
| 21000..21999 | 110 | 1000 | 11% |

## Diagnóstico

**Buena cobertura (1990-2020):** rango 18k-21k tiene 72%. Son las leyes
más citadas en práctica moderna.

**Gaps:**
- Pre-1990 (1..18000): cobertura baja porque muchas leyes antiguas
  fueron derogadas y BCN puede no exponerlas via SPARQL como RootNorm.
- Post-2024 (21000+): el dump SPARQL no llegó a cubrir las muy recientes
  por cortar en offset=10000 cuando endpoint dio 500.

## Acciones próximas

1. **Re-scrape específico por tipo=ley con rango full** cuando el
   endpoint SPARQL vuelva estable. Esperado: completar 21000-21999
   (Ley 21210 a Ley 21800) — ~700 leyes hoy modernas.
2. **Verificar Leyes antiguas via DTO**: muchas leyes pre-1900 están
   como decretos en el catálogo BCN.

## Hallazgo 2026-05-21: idNorma >1.000.000 faltantes

Al resolver `bcn_uri` para los 180 perfiles capa 3, **65 quedaron sin
match en SQLite**. Patrón claro por rango idNorma:

| Rango idNorma | Perfiles | Tipo |
|---|---:|---|
| 0..10.000 | 1 | antiguas (DFL 458 urbanismo) |
| 10.000..100.000 | 1 | mediano (Ley 3918 SRL) |
| 100.000..500.000 | 6 | refundidos (DL 211, DFL 2/98, DL 3063) |
| **1.000.000+** | **57** | **leyes 2010+** (Ley 20422, 20584, etc.) |

**Diagnóstico**: el scrape SPARQL inicial cortó en offset~10k antes de
completar el rango moderno. Los idNorma >1M corresponden a leyes
publicadas después de ~2010, y representan el grueso del gap.

**Fix planificado**: el `resolver-bcn-uri-capa3.py` con backoff 429
ahora resuelve uno por uno via `?n bcnnorms:leychileCode "X"`. Esperado
recuperar 50-60 URIs en 30-60 min.

Para resolver el gap masivo: `scrape-sparql-uris-grafo.py` scrapea solo
URIs del grafo (80k necesarias, ~30 min con batch VALUES).

## Validación funcional

El MCP cumple su función a pesar de los gaps porque:
- 158/158 perfiles capa 3 resuelven via lookup ([check-mcp-resolves-capa3.py](../scripts/audit/check-mcp-resolves-capa3.py))
- Capa 3 prioriza sobre capa 1 en search/lookup → el MCP devuelve el
  perfil curado aunque el catálogo no tenga la metadata.

**El gap es de discovery, no de uso autorizado.**
