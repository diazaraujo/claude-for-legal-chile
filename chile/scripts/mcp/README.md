# MCP connectors para Claude Legal Chile

> **Estado v0.6**: `mcp-bcn-leychile` con **7 tools**:
> - Remoto (BCN/LeyChile XML): `bcn_get_norma`, `bcn_check_vigencia`,
>   `bcn_get_xml`
> - Local (catálogo SQLite indexado): `lookup_norma`, `search_normas`,
>   `get_relaciones`, `catalog_stats`
>
> Cache SQLite local + rate limiting + indexador desde el grafo BCN
> via SPARQL. 18 tests offline en verde.

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

## MVP implementado: `mcp-bcn-leychile`

Primer connector. Razones: fuente pública sin auth, reutiliza scripts
existentes (`scripts/bcn/`), alto valor inmediato.

### Instalación

```bash
cd chile/scripts/mcp
pip install -e .
```

Requiere Python 3.11+ y el paquete `mcp` (Anthropic SDK).

### Tools expuestos

#### `bcn_get_norma(id_norma, force_refresh=False)`

Recupera metadata + estructura jerárquica de una norma desde BCN.

Devuelve JSON con: `id_norma`, `tipo`, `numero`, `titulo_oficial`,
`fecha_publicacion`, `organismo`, `vigencia`, `url_consulta`, `estructura`
(lista de partes con tipo_parte, numero, titulo, texto, hijos).

#### `bcn_check_vigencia(id_norma)`

Verifica si la norma está vigente al día de hoy según BCN. Devuelve
`vigente` (bool), `vigencia_declarada`, `fecha_consulta`, `fuente`.

#### `bcn_get_xml(id_norma, force_refresh=False)`

XML estructural completo (útil para parseo avanzado por el cliente).

### Caching

- **SQLite local** en `~/.cache/mcp-bcn-leychile/cache.db`.
- TTL XML: 7 días (la normativa cambia lento).
- Invalidación via `force_refresh=True`.

### Rate limiting

- 1 req/segundo a BCN (configurable).
- User-Agent: `claude-legal-chile-mcp/0.1 (unholster.com)`.

### Tests

```bash
cd chile/scripts/mcp
python3 -m pytest tests/    # con pytest
```

Tests offline (fixtures XML embebidas). 7 tests verdes al 2026-05-20.

### Uso con Claude Code

Agregar al `~/.config/claude-code/mcp.json` (o equivalente):

```json
{
  "mcpServers": {
    "bcn-leychile": {
      "command": "mcp-bcn-leychile",
      "args": []
    }
  }
}
```

Claude invocará los tools automáticamente cuando una consulta requiera
verificación contra BCN.

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
