# Changelog — adaptación chilena

Cambios al contenido de `chile/`. Para cambios del upstream ver `git log` con
`upstream/main`.

## 0.0.1 — 2026-05-18

- Fork inicial de `anthropics/claude-for-legal`.
- Carpeta `chile/` creada con esqueleto: `README.md`, `CLAUDE.md` general,
  este `CHANGELOG.md`.
- Estado: WIP. Perfiles por rama del derecho pendientes de redacción y de
  revisión por abogado habilitado.

## 0.0.4 — 2026-05-18

- **Constitución Política de la República** publicada (`constitucion/constitucion-politica.md`),
  base de todo el ordenamiento; índice de Capítulos I-XVI, Art. 19 con 26 numerales
  tabulados, Recurso de Protección (Art. 20), inaplicabilidad por
  inconstitucionalidad, Art. 5 inc. 2° sobre tratados de DD.HH.
- **Estrategia de tres capas** documentada como ADR-0002 en el STD wrapper. Define
  cómo escalar el corpus: capa 1 catálogo auto (BCN scraping), capa 2 estructural
  semi-auto, capa 3 análisis operativo curado + validado. Frontmatter `capa: N`
  agregado en archivos curados.
- **Cluster civil/comercial inicial**: `codigo-comercio.md` (actos de comercio,
  sociedades de personas, materias migradas a leyes especiales) +
  `ley-18046-sociedades-anonimas.md` (gobierno corporativo, OPR, OPA, deberes
  fiduciarios) + `ley-19496-consumidor.md` (LPC: cláusulas abusivas, garantía legal,
  SERNAC Financiero, retracto).
- **Cobertura ampliada**: ahora 1 Constitución + 2 códigos + 11 leyes = 14 archivos
  capa 3 borrador. Cubre operativamente: laboral, privacidad, B2C, societario, marco
  constitucional.

## 0.0.3 — 2026-05-18

- **Cluster laboral completo en el corpus** (todos en `borrador-no-validado`):
  - `leyes/ley-16744-accidentes-trabajo.md` — seguro social, Mutuales, DIAT, DS 40/54
  - `leyes/ley-20123-subcontratacion.md` — responsabilidad subsidiaria/solidaria, F30,
    EST
  - `leyes/ley-21561-reduccion-jornada.md` — calendario 45→44→42→40h hasta 2028
  - `leyes/ley-21220-teletrabajo.md` — pacto, derecho a desconexión, reversibilidad
  - `leyes/ley-21015-inclusion-laboral.md` — cuota 1% en empresas 100+
- **Cobertura laboral actual**: Código del Trabajo + 6 leyes especiales (16.744,
  20.123, 21.015, 21.220, 21.561, 21.643). Permite responder consultas operativas
  laborales típicas (terminación, jornada, subcontratación, teletrabajo, acoso,
  accidentes, inclusión) sin gaps mayores.
- **Total corpus publicado**: 1 código + 8 leyes (9 archivos, todos
  `borrador-no-validado`).

## 0.0.2 — 2026-05-18

- **Pivot arquitectónico**: el corpus normativo (códigos, leyes, decretos) pasa a ser
  el eje del sistema, en lugar de perfiles por rama. Coherente con tradición civil law
  chilena.
- Estructura `chile/normativa/{codigos,leyes,decretos,dictamenes}` creada con índices.
- Estructura `chile/{perfiles,skills,ejemplos}` creada para vistas/skills/casos.
- Esquema de archivo de norma definido en `normativa/README.md` (frontmatter con
  vigencia, modificaciones, estado de revisión, conexiones).
- Primeros 4 archivos de norma publicados (todos `borrador-no-validado`):
  - `leyes/ley-19628-proteccion-datos.md` (LPD vigente)
  - `leyes/ley-21719-modificacion-lpd.md` (modificación + APDP, vigencia 2026-12-01)
  - `leyes/ley-21643-acoso-laboral.md` (Ley Karin)
  - `codigos/codigo-trabajo.md` (DFL 1/2002, ~22 artículos clave indexados)
- Índices de leyes (19 entradas), códigos (12) y decretos (4) listados con estado.
- `CLAUDE.md` general actualizado para apuntar al corpus normativo como spine.
- `README.md` reescrito para explicar la arquitectura normativa-spine y diferenciación
  vs el fork argentino.
