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

## Validación funcional

El MCP cumple su función a pesar de los gaps porque:
- 158/158 perfiles capa 3 resuelven via lookup ([check-mcp-resolves-capa3.py](../scripts/audit/check-mcp-resolves-capa3.py))
- Capa 3 prioriza sobre capa 1 en search/lookup → el MCP devuelve el
  perfil curado aunque el catálogo no tenga la metadata.

**El gap es de discovery, no de uso autorizado.**
