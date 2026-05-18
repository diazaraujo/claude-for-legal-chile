# Changelog — adaptación chilena

Cambios al contenido de `chile/`. Para cambios del upstream ver `git log` con
`upstream/main`.

## 0.0.1 — 2026-05-18

- Fork inicial de `anthropics/claude-for-legal`.
- Carpeta `chile/` creada con esqueleto: `README.md`, `CLAUDE.md` general,
  este `CHANGELOG.md`.
- Estado: WIP. Perfiles por rama del derecho pendientes de redacción y de
  revisión por abogado habilitado.

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
