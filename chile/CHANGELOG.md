# Changelog — adaptación chilena

Cambios al contenido de `chile/`. Para cambios del upstream ver `git log` con
`upstream/main`.

## 0.0.1 — 2026-05-18

- Fork inicial de `anthropics/claude-for-legal`.
- Carpeta `chile/` creada con esqueleto: `README.md`, `CLAUDE.md` general,
  este `CHANGELOG.md`.
- Estado: WIP. Perfiles por rama del derecho pendientes de redacción y de
  revisión por abogado habilitado.

## 0.0.7 — 2026-05-19

- **Cluster compliance + IP + transparencia** (capa 3, 8 archivos nuevos):
  - `leyes/ley-20285-transparencia.md` — Transparencia activa + SAI, CPLT,
    amparo, causales reserva Art. 21, plazos 20+10 días hábiles.
  - `leyes/ley-20393-rppj.md` — Responsabilidad penal personas jurídicas:
    MPD, Encargado de Prevención, catálogo de delitos (ampliado 21.595),
    penas (multa, disolución, inhabilitación contratar Estado).
  - `leyes/ley-21595-delitos-economicos.md` — Reforma estructural penal 2023:
    4 categorías de delitos económicos, multas hasta 60.000 UTM, comiso
    valor equivalente, restricciones beneficios alternativos.
  - `leyes/ley-18045-mercado-valores.md` — LMV: oferta pública, hecho
    esencial, insider trading (Art. 165), manipulación bursátil, OPA
    obligatoria, Ley 21.314 gob. corp., Ley 21.521 Fintec.
  - `leyes/ley-19039-propiedad-industrial.md` — Marcas (10 años renovables),
    patentes (20 años), modelos utilidad, diseños, INAPI, TPI, Ley 21.355.
  - `leyes/ley-17336-propiedad-intelectual.md` — Derecho de autor + conexos,
    plazo vida+70, derechos morales + patrimoniales, software Art. 88,
    excepciones (cita, parodia, educación).
  - `leyes/ley-19913-lavado-activos.md` — UAF, ROS, sujetos obligados,
    diligencia debida PEP, GAFI, multas administrativas.
  - `leyes/ley-14908-alimentos.md` — Pensión 40% IMR, alimentos provisorios
    + definitivos, apremios (arraigo, suspensión licencia/pasaporte/arresto),
    RNDPA (Ley 21.389), GAM (Ley 21.515).
- **Cobertura capa 3 ahora**: 1 Constitución + 6 códigos + 25 leyes + 3 skills
  + setup interview + fuentes.md.

## 0.0.6 — 2026-05-18

- **Cluster procesal/familia/ambiental** (capa 3 borrador):
  - `leyes/ley-19968-tribunales-familia.md` — Tribunales de Familia,
    procedimiento ordinario, mediación obligatoria, medidas de protección NNA.
  - `leyes/ley-19947-matrimonio-civil.md` — Matrimonio civil con Ley 21.400
    matrimonio igualitario, divorcio mutuo acuerdo (1 año) vs unilateral (3),
    compensación económica, regímenes patrimoniales.
  - `leyes/ley-19300-medio-ambiente.md` — SEIA (DIA vs EIA), institucionalidad
    MMA/SMA/SEA/Tribunales Ambientales, sanciones SMA, delitos ambientales
    Ley 21.595, acción de reparación por daño.
- **Cobertura capa 3 ahora**: 1 Constitución + 6 códigos + 17 leyes + 3 skills
  + setup interview + fuentes.md.

## 0.0.5 — 2026-05-18

- **Skills transversales publicados** en `chile/skills/`:
  - `diagnostico.md` — protocolo de 6 pasos (jurisdicción, rama, normas,
    vigencia, complejidad, declaración) que el sistema corre antes de toda
    respuesta.
  - `citas-verificables.md` — formato canónico por tipo (constitucional,
    código, ley, jurisprudencia CS/CA/TC/TDLC/JL, doctrina administrativa
    DT/SII/CGR/CMF/SUSESO) + niveles de verificación (✅/🟨/🟧/🟥).
  - `plazos.md` — distinción días corridos vs hábiles, sábado no hábil (CPC
    Art. 66), feriado judicial, plazos críticos por rama.
- **`chile/fuentes.md`** — mapa de fuentes autoritativas (BCN, DO, PJUD, TC,
  TDLC, DT, SII, Contraloría, CMF, SUSESO, SERVEL, Registro Civil) con URLs y
  reglas de citación.
- **`chile/setup-interview.md`** y `chile/setup-output-TEMPLATE.md` — entrevista
  cold-start de 15 preguntas en 6 bloques que genera CLAUDE.md personalizado
  para la firma/práctica del usuario.
- **Cluster civil/tributario foundational** (capa 3, borrador):
  - `codigos/codigo-civil.md` — Andrés Bello 1855, 60+ artículos clave
    indexados, reformas 2014-2023.
  - `codigos/codigo-tributario.md` — DL 830, 30+ artículos clave, reforma
    21.713 anotada.
  - `leyes/dl-824-renta.md` — LIR completa: regímenes 14A/14D ProPyme, II Cat.,
    Global Compl., Adicional, retenciones, prescripción.
  - `leyes/dl-825-iva.md` — IVA 19%, débito/crédito fiscal, DTE, servicios
    digitales (Ley 21.210/21.713), exenciones, exportaciones.
  - `leyes/ley-19886-compras-publicas.md` — Bases, modalidades, ChileCompra,
    TCP, plazos.
- **Cobertura capa 3 actual**: 1 Constitución + 4 códigos + 13 leyes = 18
  archivos capa 3 borrador.

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
