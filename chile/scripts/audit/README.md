# Scripts de auditoría del corpus

> Validación técnica sin depender de fuente externa. Útiles para CI +
> mantenimiento.

## Scripts disponibles

### `check-frontmatter.py`

Audita el frontmatter YAML de los 126 archivos capa 3. Chequea:

1. Frontmatter YAML válido y presente.
2. Campos obligatorios (`slug`, `titulo_oficial`, `fuente_oficial`,
   `vigencia`, `capa`, `estado_revision`).
3. Slug == nombre del archivo.
4. URL BCN con formato esperado.
5. URLs BCN duplicadas (alerta).
6. `estado_revision` valor canónico (ver `chile/MARCADORES.md`).
7. Campo `relacionada_per` (no `relacionada_con` legacy).
8. `relacionada_per` apuntan a slugs existentes (WARN si no — pueden
   ser slugs futuros intencionales).

**Uso**:

```bash
cd <repo-root>
python3 chile/scripts/audit/check-frontmatter.py
```

**Output**:
- `[ERROR] <file>`: bloqueante (campos obligatorios faltantes,
  formato inválido).
- `[WARN] <file>`: no bloqueante (slugs futuros en
  `relacionada_per`).
- `[INFO]`: información general (duplicados, resumen).

**Exit code**:
- `0`: sin errores (warnings permitidos).
- `1`: errores detectados.

**Sin dependencias externas**: stdlib pura Python 3.11+.

### `check-links.py`

Audita **links Markdown internos** en todo el corpus + perfiles +
skills + ejemplos + audits + capa 1 catálogo.

Para cada `[texto](ruta.md)`:

1. Resuelve la ruta relativa contra el archivo origen.
2. Verifica que el archivo destino exista en el repo.
3. Reporta links rotos como ERROR.

Ignora:
- URLs externas (`http`, `https`, `mailto`, etc.).
- Anchors solos (`#section`).

**Uso**:

```bash
cd <repo-root>
python3 chile/scripts/audit/check-links.py
```

Cobertura típica: ~12.700 archivos Markdown (capa 1 incluida).

**Sin dependencias externas**: stdlib pura.

## Pendientes Fase 4-5

- `check-bcn-urls.py` — verifica URLs BCN contra fuente oficial
  cuando BCN responda. Comparara `titulo_oficial` del frontmatter
  con título oficial extraído de BCN.
- `check-vigencias.py` — alerta sobre normas con vigencia escalonada
  cuya fecha límite se aproxima.

## Integración con CI

Para activar en CI (futuro):

```yaml
# .github/workflows/audit.yml
on: [push, pull_request]
jobs:
  frontmatter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: python3 chile/scripts/audit/check-frontmatter.py
```

## Hallazgos persistentes (no auto-corregidos)

| Hallazgo | Archivos | Naturaleza |
|---|---|---|
| URL BCN id=172986 compartida | `codigo-civil`, `ley-14908-alimentos` | Ambigüedad BCN (DFL refundidor 1/2000 Justicia) — documentada |
| URL BCN id=1118991 compartida | `ley-21091-educacion-superior`, `ley-21094-universidades-estatales` | Probable error copy-paste — pendiente verificación BCN |
| Slugs futuros en `relacionada_per` | 5 archivos, 6 referencias | Intencional (marcador de trabajo futuro) |

Ver detalle en `chile/audits/transversales-urls-bcn-hallazgos.md`.
