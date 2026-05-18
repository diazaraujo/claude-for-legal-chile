# normativa/ — corpus normativo chileno

Este directorio es la **fuente autoritativa** del conocimiento jurídico chileno del fork.
Toda referencia normativa (sea desde `chile/CLAUDE.md`, desde un perfil por rama o desde un
skill) apunta a algún archivo bajo esta carpeta.

## Estructura

```
normativa/
├── codigos/           Códigos chilenos vigentes
├── leyes/             Leyes especiales con identidad propia
├── decretos/          Reglamentos y decretos supremos relevantes
└── dictamenes/        Dictámenes oficiales (DT, SII, Contraloría) — v2
```

## Esquema de archivo de norma

Cada archivo de norma sigue este formato canónico:

```markdown
---
norma: <nombre corto>                # ej. "Ley 19.628"
slug: <kebab-case>                   # ej. "ley-19628-proteccion-datos"
titulo_oficial: <título completo>    # ej. "Ley sobre Protección de la Vida Privada"
publicacion: YYYY-MM-DD              # fecha de publicación en DO
fuente_oficial: <URL BCN/LeyChile>   # https://www.bcn.cl/leychile/...
ultima_modificacion: YYYY-MM-DD (<norma modificatoria>)
vigencia: <vigente | derogada | en vigencia diferida | parcialmente vigente>
materia: <listado de materias>
relacionada_con:                     # slugs de normas conectadas
  - codigo-civil
  - ley-21719-modificacion-lpd
estado_revision: <borrador-no-validado | revision-legal-en-curso | validada>
validador: <vacío | nombre/firma>
fecha_validacion: <vacío | YYYY-MM-DD>
---

# <Título>

## Resumen
[1-3 párrafos: qué regula, a quién aplica, para qué se invoca]

## Estructura
[Libros / títulos / capítulos relevantes]

## Conceptos clave
[Tabla o lista con definiciones operativas]

## Artículos relevantes
[Selección curada; NO copia literal completa. El texto íntegro vive en BCN/LeyChile]

## Modificaciones relevantes
[Historia normativa]

## Conexiones con otras normas

## Cuándo invocar esta norma
[Tipos de pregunta / situación que mapean a esta norma]

## Disclaimers
[WIP, validación pendiente, etc.]
```

## Reglas

1. **No se copia el texto íntegro** de la norma — eso es responsabilidad del **Repositorio
   Legal de la Biblioteca del Congreso Nacional (BCN/LeyChile)**. El archivo es metadata
   estructurada + resumen útil para el LLM.
2. **Toda norma se cita por su número y fuente oficial** (URL BCN).
3. **Estado de revisión declarado** — ningún archivo se publica sin marcar
   `estado_revision`. Solo archivos `validada` pueden eliminar disclaimer de WIP.
4. **Conexiones explícitas** — cada norma declara con qué otras normas se relaciona; eso
   permite al LLM razonar sobre el sistema, no sobre piezas aisladas.

## Estado del corpus

Ver `00-indice.md` en cada subcarpeta para el listado vigente y su estado de revisión.

## Fuente oficial autoritativa

**BCN — Biblioteca del Congreso Nacional** · https://www.bcn.cl/leychile

Para verificación de texto vigente, vigencias, modificaciones y enlaces oficiales,
**siempre** consultar LeyChile. Este corpus es metadata + síntesis, no reemplaza la
fuente oficial.
