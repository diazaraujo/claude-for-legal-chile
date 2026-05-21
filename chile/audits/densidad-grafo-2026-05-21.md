---
fecha: 2026-05-21
herramienta: query SQL contra catalogo.sqlite3
muestra: 330.203 edges (modifiesTo + isModifiedBy parcial)
---

# Auditoría densidad del grafo BCN vs corpus local

Resultado de cruzar los 330k edges del grafo con las 20.712 normas
indexadas en el catálogo capa 1+2+3.

## Métricas

| Métrica | Edges | % del grafo |
|---|---:|---:|
| Total edges en grafo | 330.203 | 100% |
| src resoluble en catalog local | 27.480 | 8% |
| dst resoluble en catalog local | 18.933 | 6% |
| **ambos resolubles (denso)** | **7.454** | **2%** |
| dst fuera del catálogo (externo) | 311.270 | 94% |

## Interpretación

**El grafo BCN es 17× más grande que el corpus actual.** Cada edge
apunta principalmente a URIs que aún no tengo localmente.

Razón principal: tipos masivos no scrapeados todavía:
- `dto` (Decreto Supremo): 173.951 normas en BCN
- `res` (Resolución): 149.486 normas en BCN

Mi catálogo cubre bien los tipos "core legales" (ley/dl/dfl/cod/aa/tra
≈ 16k normas) pero falta el bulk de normas operativas.

## Implicación para el MCP

Cuando Claude pregunta `get_relaciones` de Ley 19628:
- ✅ Encuentra qué otras NORMAS modifican Ley 19628 (capa 1+2+3 cubren bien).
- ⚠️ Muchas modifications señalan a DTOs/RES que están en grafo pero
  NO localmente. URI viene; slug local = null.

El MCP funcional sigue cumpliendo: devuelve el URI BCN oficial para que
Claude lo cite, y `bcn_get_norma` puede traer el XML estructural si
es necesario. El gap es de discovery local, no de uso.

## Acción próxima

Scrape SPARQL **by-tipo** de los 323k dto+res restantes, en buckets
manejables (≤10k offset / paginación por URI). ETA ~3-6h.

Esto subiría la densidad del grafo a >70% — un MCP donde **la mayoría
de relaciones se resuelve a slug local** sin hits a BCN online.
