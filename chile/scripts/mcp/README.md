# MCP connectors para Claude Legal Chile

> **Estado**: roadmap Fase 4. Sin implementación productiva aún.

Conectores [Model Context Protocol](https://modelcontextprotocol.io)
que permitirán a Claude (y otros agentes compatibles) consultar fuentes
primarias chilenas en tiempo real, complementando el corpus estático
de `chile/normativa/`.

## Por qué MCP

El corpus actual (capa 1 + 2 + 3) es una **referencia estructurada
estática**: Claude lee archivos `.md` con frontmatter canónico. Funciona
perfecto para análisis sustantivo, pero tiene dos limitaciones:

1. **Sin verificación de vigencia en tiempo real**: una ley puede haber
   sido modificada ayer; el corpus se actualiza por commits.
2. **Sin acceso a fuentes con autoridad incremental**: jurisprudencia,
   dictámenes, circulares — son emisiones diarias que el corpus no
   captura.

Los conectores MCP cierran ambas brechas exponiendo **tools** y
**resources** invocables por Claude durante la conversación.

## Plan por tiers

Ver [ADR-0003 interno](../../decisions/) para racionale completo.

### Tier 1 — Normativos vigentes

| Conector | Función | Fuente |
|---|---|---|
| `mcp-bcn-leychile` | Texto normativo + estructura XML | bcn.cl/leychile |
| `mcp-bcn-sparql` | Catálogo + metadata SPARQL | datos.bcn.cl/sparql |
| `mcp-diario-oficial` | Publicaciones recientes | diariooficial.interior.gob.cl |

### Tier 2 — Judicial

| Conector | Función | Fuente |
|---|---|---|
| `mcp-pjud-buscador` | Causas + sentencias unificadas | oficinajudicialvirtual.pjud.cl |
| `mcp-cs-jurisprudencia` | Corte Suprema | suprema.pjud.cl |
| `mcp-tc-fallos` | Tribunal Constitucional | tribunalconstitucional.cl |

### Tier 3 — Administrativo + control

| Conector | Función | Fuente |
|---|---|---|
| `mcp-cgr-dictamenes` | Contraloría dictámenes | contraloria.cl |
| `mcp-cplt-decisiones` | Consejo Transparencia | consejotransparencia.cl |
| `mcp-cmf-normativa` | NCG + Circulares CMF | cmfchile.cl |
| `mcp-sii-circulares` | Circulares + Oficios SII | sii.cl |
| `mcp-dt-instrucciones` | Dirección del Trabajo | dt.gob.cl |

### Tier 4 — Especializado

| Conector | Función | Fuente |
|---|---|---|
| `mcp-tta-sentencias` | TTA tributario / aduanero | tta.cl |
| `mcp-tribunales-ambientales` | TA | tribunalambiental.cl |
| `mcp-fne-resoluciones` | FNE | fne.gob.cl |

## MVP: `mcp-bcn-leychile`

Primer connector. Razones: fuente pública sin auth, reutiliza scripts
existentes (`scripts/bcn/`), alto valor inmediato.

### Diseño tentativo

#### Tools

```python
def bcn_get_norma(id_norma: str) -> dict:
    """Recupera norma por ID BCN.
    
    Args:
        id_norma: ID numérico BCN (ej. "1075210" = Ley 21.400).
    
    Returns:
        dict con: titulo, tipo, numero, fecha_publicacion,
        ultima_modificacion, vigencia, texto_consolidado, url_canonica.
    """

def bcn_search(query: str, tipo: str | None = None,
               desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Busca normas por keyword.
    
    Args:
        query: palabra clave (ej. "acoso laboral").
        tipo: filtro por tipo (ley, dl, dfl, cod, tra, aa).
        desde, hasta: rango de fechas (YYYY-MM-DD).
    
    Returns:
        lista de matches con metadata básica.
    """

def bcn_get_xml_structure(id_norma: str) -> dict:
    """Recupera estructura jerárquica desde XML LeyChile.
    
    Returns:
        dict con árbol libro/título/parte/artículo con texto + número.
    """

def bcn_check_vigencia(id_norma: str) -> dict:
    """Verifica si la norma está vigente al día de hoy.
    
    Returns:
        dict con: vigente (bool), fecha_consulta, ultima_modificacion,
        derogada_por (slug si aplica), reemplazada_por (slug si aplica).
    """
```

#### Resources

- `bcn-leychile://catalog` — índice navegable por tipo.
- `bcn-leychile://norma/{id}` — recuperación directa.
- `bcn-leychile://search?q={q}&tipo={tipo}` — búsqueda parametrizada.

#### Caching

- **SQLite local** con TTL por tipo de dato:
  - Catálogo (metadata): TTL 30 días.
  - Estructura XML: TTL 7 días.
  - Vigencia: TTL 1 día (más sensible al tiempo).
- **Invalidación manual** vía tool `bcn_refresh(id_norma)`.

#### Rate limiting

- Máximo **1 req/segundo** a BCN.
- Backoff exponencial en 429.
- User-Agent: `claude-legal-chile-mcp/0.1 (unholster.com)`.

## Composición con el corpus estático

```
┌─────────────────────────────────────────────┐
│ Claude (con corpus chile/ cargado)          │
└────────────┬────────────────────────────────┘
             │
        consulta sobre Ley X
             │
             ▼
┌─────────────────────────────────────────────┐
│ chile/normativa/leyes/ley-X-slug.md         │  ← capa 3 (perfil)
│ + frontmatter (estado_revision)             │
└────────────┬────────────────────────────────┘
             │
        si requiere verificación de vigencia
             │
             ▼
┌─────────────────────────────────────────────┐
│ mcp-bcn-leychile.bcn_check_vigencia(X)     │  ← MCP connector
│ → vigente: true/false, ultima_mod: fecha    │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ Respuesta al usuario con:                   │
│ - cita del perfil (capa 3) si validado      │
│ - verificación de vigencia (MCP)            │
│ - disclaimer adecuado                        │
└─────────────────────────────────────────────┘
```

## Stack técnico (tentativo)

- **Lenguaje**: Python 3.11+ (consistencia con `scripts/bcn/`).
- **Servidor MCP**: `mcp-server` (oficial Python).
- **HTTP**: `urllib` stdlib (sin deps externas para empezar).
- **Storage**: SQLite stdlib.
- **XML parsing**: `xml.etree.ElementTree` stdlib.
- **Licencia**: Apache 2.0.

## Roadmap

| Semana | Hito |
|---|---|
| 1 | Diseño detallado + esquema OpenAPI-style del MVP |
| 2-3 | Implementación core (search + get + vigencia) |
| 4 | Caching + rate limiting + testing |
| 5 | Documentación + ejemplo de uso con Claude Code + release |
| 6-7 | Connector PJUD (siguiente prioridad) |

## Cómo contribuir

Cuando empezemos a implementar, las contribuciones serán bienvenidas en:

- **Nuevo connector**: seguir el patrón del MVP BCN.
- **Mejoras de cobertura**: ampliar resources / tools de connectors
  existentes.
- **Testing**: agregar casos al test set.
- **Documentación**: guías de uso por escenario.

## Referencias

- [Model Context Protocol](https://modelcontextprotocol.io) — Anthropic.
- [BCN — Datos abiertos](https://datos.bcn.cl) — fuente del corpus.
- `scripts/bcn/scrape-catalogo.py` y `promote-to-capa2.py` — código
  precursor reutilizable.
