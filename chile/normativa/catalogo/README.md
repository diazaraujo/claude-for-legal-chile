# Catálogo capa 1 — corpus chileno

Este directorio contiene la **capa 1** del corpus normativo chileno: metadata
estructurada por norma generada automáticamente desde el endpoint **SPARQL público
de BCN/LeyChile** (`https://datos.bcn.cl/sparql`, ontología `bcn-norms`).

Cada archivo es un markdown mínimo con frontmatter canónico y referencia a la fuente
oficial. **No contiene texto íntegro ni análisis legal** — eso es responsabilidad de
las capas 2 (resumen estructural) y 3 (análisis operativo curado).

## Contenido actual

| Tipo | Carpeta | Cantidad |
|---|---|---|
| Códigos | [`cod/`](cod/) | 11 |
| Tratados internacionales | [`tra/`](tra/) | 167 |
| Auto acordados Corte Suprema | [`aa/`](aa/) | 27 |
| Decretos con Fuerza de Ley | [`dfl/`](dfl/) | 3.171 |
| Decretos Ley | [`dl/`](dl/) | 4.167 |
| Leyes | [`ley/`](ley/) | 4.670 |
| **TOTAL** | | **12.213** |

## Convención de filename

- Para tipos con **número único en el ordenamiento** (códigos y leyes): `<numero>.md`
  con padding (`00012.md`).
- Para tipos donde el número se **reusa por año o por organismo** (DFL, DL, DTO, RES,
  TRA): `<numero>-<YYYY-MM-DD>-<emisor>.md`.

## Frontmatter canónico

```yaml
---
norma: Ley 19628                          # nombre corto
slug: ley-19628                           # kebab-case
tipo: ley                                 # ley | cod | dfl | dl | tra | aa | dto | res
numero: "19628"
titulo_oficial: "..."                     # de BCN
publicacion: 1999-08-28                   # YYYY-MM-DD
promulgacion: 1999-08-18                  # YYYY-MM-DD (a veces "desconocida")
emisor: ministerio-secretaria-general-de-la-presidencia
leychile_code: 141599
fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma=141599
bcn_uri: http://datos.bcn.cl/recurso/cl/ley/...
capa: 1                                   # capa del corpus
estado_revision: catalogo-auto            # nunca validado en capa 1
validador: null
fecha_validacion: null
---
```

## Limitaciones conocidas

- **Cobertura parcial de leyes**: BCN catálogo total reporta ~16.700 leyes vigentes;
  el endpoint SPARQL no permite paginación estable con OFFSET sobre 17K registros
  porque las queries se ordenan por hash interno cambiante. Re-ejecuciones agregan
  nuevas leyes incrementalmente. Cobertura actual del corpus capa 1: ~28%.
- **DTO y RES no incluidos en v1**: representan ~325K normas vigentes,
  mayoritariamente administrativas puntuales (nombramientos, autorizaciones, etc.)
  con baja relevancia normativa. Se considerará incluir un subset filtrado en v2.
- **Sin texto íntegro**: la fuente autoritativa del texto vigente es BCN/LeyChile.
- **Sin contenido editorial**: la capa 1 es solo metadata. Para análisis operativo
  ver [`chile/normativa/leyes/`](../leyes/), [`chile/normativa/codigos/`](../codigos/),
  [`chile/normativa/constitucion/`](../constitucion/).

## Cómo regenerar / extender

El script `scripts/bcn/scrape-catalogo.py` es idempotente. Se invoca:

```bash
# Regenerar un tipo completo
python scripts/bcn/scrape-catalogo.py --tipos ley

# Pequeño (sin partición)
python scripts/bcn/scrape-catalogo.py --tipos cod,tra,aa

# Múltiples tipos
python scripts/bcn/scrape-catalogo.py --tipos dfl,dl,ley --sleep-ms 1000

# Solo sobreescribir existentes
python scripts/bcn/scrape-catalogo.py --tipos ley --force

# Limitar (para pruebas)
python scripts/bcn/scrape-catalogo.py --tipos ley --limit 100
```

Re-ejecutar tras intervalos (semanas) permite capturar nuevas leyes publicadas y
actualizaciones del catálogo BCN.

## Próxima capa

Las entradas capa 1 pueden ser **promovidas a capa 2** (resumen estructural) mediante
un pipeline LLM-asistido que descarga texto BCN y genera estructura por
libros/títulos/artículos + conceptos clave. Y de capa 2 a capa 3 mediante curación
manual + validación legal.

Ver `decisions/ADR-0002-estrategia-tres-capas-corpus.md` (en el STD wrapper interno).
