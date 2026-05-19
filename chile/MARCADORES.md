# Glosario canónico de marcadores

> **Fuente de verdad** para el vocabulario controlado del corpus. Cualquier
> archivo del proyecto debe usar estos marcadores con el significado declarado
> aquí. Si un caso de uso requiere un nuevo marcador, se agrega a este archivo
> primero, vía PR.

Este glosario es parte del **principio LLM-wiki**: el contenido es procesable
por LLMs sólo si los marcadores tienen significado estable. Marcadores ambiguos
o sin definición rompen la cadena de inferencia.

---

## 1. Frontmatter de perfiles capa 3

Todo archivo en `chile/normativa/leyes/`, `chile/normativa/codigos/` y
`chile/normativa/constitucion/` declara este frontmatter YAML al inicio:

```yaml
---
norma: <Texto humano legible — ej. "Ley 21.643" o "DFL 1.122 (Código de Aguas)">
slug: <kebab-case-unique — ej. "ley-21643-acoso-laboral">
titulo_oficial: <título tal como aparece en el DO/BCN>
publicacion: <YYYY-MM-DD de la fecha del DO>
fuente_oficial: <URL BCN/LeyChile>
ultima_modificacion: <YYYY-MM-DD | descripción libre>
vigencia: <vigente | vigente con escalonamiento | derogada | suspendida>
materia:
  - <lista corta de temas — operativos para búsqueda>
capa: 3
relacionada_per:
  - <slugs de otros perfiles que esta norma toca>
estado_revision: <ver §3>
validador: <null | nombre del abogado validador>
fecha_validacion: <null | YYYY-MM-DD>
---
```

### Campos obligatorios

`norma`, `slug`, `titulo_oficial`, `fuente_oficial`, `vigencia`, `capa`,
`estado_revision`.

### Campos opcionales

`publicacion`, `ultima_modificacion`, `materia`, `relacionada_per`,
`validador`, `fecha_validacion`.

---

## 2. Frontmatter de capa 1 + 2

Archivos en `chile/normativa/catalogo/<tipo>/` (capa 1 + 2 conviven en el mismo
archivo; capa 2 se promueve por enriquecimiento del cuerpo).

```yaml
---
tipo: <ley | dfl | dl | cod | tra | aa>
numero: <número con padding — ej. "21643" o "00458">
slug: <slug-bcn>
titulo: <título oficial>
fecha: <YYYY-MM-DD de publicación>
organismo: <organismo emisor — ministerio, congreso, etc.>
uri_bcn: <URI canónica BCN>
url_consulta: <URL legible para humano>
capa: <1 | 2>
estructura: <opcional; lista de partes parseadas si capa=2>
---
```

---

## 3. Marcador `estado_revision`

Aplica a perfiles capa 3. Valores permitidos:

| Valor | Significado |
|---|---|
| `borrador-no-validado` | Generado por LLM o redactor sin validación por abogado habilitado. Sistema antepone disclaimer al citarlo. |
| `en-revision` | Asignado a validador; pendiente de cierre. |
| `validada` | Revisado y firmado por abogado habilitado registrado en `validador`. Sistema cita sin disclaimer adicional. |
| `obsoleta` | Norma derogada o sustituida. Sistema redirige al perfil que la reemplaza vía `relacionada_per`. |
| `requiere-refactor-llm-wiki` | Estructura del archivo no cumple el principio LLM-wiki (frontmatter incompleto, sin headings consistentes, etc.). |
| `fuera-de-alcance` | Reconocido pero excluido por decisión de scope (ej. Ley 19.253 indígena en v1). |

---

## 4. Marcador `vigencia`

| Valor | Significado |
|---|---|
| `vigente` | En vigor sin condiciones especiales. |
| `vigente con escalonamiento` | En vigor con calendario gradual de aplicación. Sistema declara fecha de plena vigencia. |
| `vigente con reforma <año>` | En vigor con modificación estructural reciente cuyo texto refundido debe verificarse. |
| `vigencia diferida: <YYYY-MM-DD>` | Promulgada pero entra en vigor en fecha futura. |
| `derogada` | Sin efectos. Mantener perfil sólo si es referencia histórica relevante (ej. DL 600). |
| `suspendida` | Aplicación interrumpida por TC o ley posterior; verificar caso a caso. |

---

## 5. Marcador `capa`

| Valor | Significado |
|---|---|
| `1` | Solo catálogo (metadata BCN, sin contenido sustantivo). |
| `2` | Catálogo + estructura parseada desde XML LeyChile. |
| `3` | Análisis curado con disclaimer + cross-links. |

Un archivo nunca puede tener capa "0" ni "4". La capa 3 es siempre la más
reciente; las capas 1 y 2 son referencia verificable subyacente.

---

## 6. Marcador `relacionada_per`

Lista de slugs de otros perfiles capa 3 que esta norma cita o toca. Permite
navegación semántica + invalidación en cascada (si un perfil cambia, los que
lo citan se marcan para revisión).

```yaml
relacionada_per:
  - codigo-trabajo
  - ley-16744-accidentes-trabajo
  - ley-21155-fueros
```

No incluye normas de capa 1/2 (esas se citan en el cuerpo, no en frontmatter).

---

## 7. Inline markers en el cuerpo de los perfiles

Marcadores en línea que el sistema reconoce para activar comportamientos:

| Marcador | Activa |
|---|---|
| `> **Borrador no validado.**` (al inicio) | Disclaimer obligatorio antes de citar |
| `**[VERIFICAR]**` | Sistema declara la incertidumbre antes de operar sobre el item marcado |
| `**[DEROGADO desde YYYY-MM-DD]**` | Sistema rechaza la cita y deriva al perfil reemplazante |
| `**[Vigencia escalonada: <fecha plena>]**` | Sistema añade nota sobre calendario al citar |
| `**[Fuera de alcance v1]**` | Sistema declara la limitación y deriva a especialista |

---

## 8. Convención de slugs

- **kebab-case**: minúsculas + guiones; sin acentos ni eñes.
- **Prefijo del tipo** cuando el número no es único:
  - `ley-21643-acoso-laboral` (leyes — usa número y descripción corta).
  - `codigo-civil`, `codigo-trabajo` (códigos — usa nombre).
  - `dl-824-renta`, `dl-3500-pensiones` (DL — usa prefijo + número).
  - `dfl-458-urbanismo-construcciones`, `dfl-1122-codigo-aguas` (DFL — prefijo).
  - `constitucion-politica` (sin número).
- **Descripción corta opcional** después del número: 1-3 palabras, ayuda a la
  legibilidad cuando hay leyes consecutivas con números similares.
- **Estable**: una vez asignado, el slug no cambia (salvo error tipográfico).
  Es la clave primaria para cross-linking.

---

## 9. Cómo agregar un marcador nuevo

1. Abrir issue describiendo: qué marcador, qué activa, qué archivo lo usa.
2. PR que modifique este `MARCADORES.md` con la definición.
3. Después del merge, aplicar el marcador en los archivos.

No al revés: marcadores en archivos sin estar en este glosario son tratados
como `requiere-refactor-llm-wiki` por el sistema.

---

## Versión + cambios

- **v0.1.0** (2026-05-19) — primera versión, inspirada parcialmente en
  `marcadores-GLOSARIO.md` del fork argentino con adaptaciones para el
  modelo de tres capas.
