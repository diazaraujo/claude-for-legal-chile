---
perfil: societario
slug: perfil-societario
ambito: derecho societario chileno · SA, SpA, SRL, EIRL, gobierno corporativo
capa: orquestador
estado_revision: borrador-no-validado
fuente_corpus: chile/normativa/codigos/codigo-comercio.md + 10 leyes especiales
ultima_actualizacion: 2026-05-19
---

# Perfil societario — Claude Legal Chile

> **Orquestador de derecho societario, comercial y de gobierno corporativo.**
> Para detalle sustantivo de cada norma, leer el archivo referenciado.

> **Borrador no validado.** Verificar con abogado societario antes de
> aplicar en escritos.

## Cuándo se activa este perfil

- Constitución, modificación o disolución de sociedades (SA, SpA, SRL,
  EIRL, sociedades de profesionales).
- Gobierno corporativo, deberes de directores.
- OPAs, fusiones, escisiones, joint ventures.
- Mercado de valores, valores corporativos, OPRs.
- Compliance corporativo: MPD (Ley 20.393), antilavado, probidad.
- Conflictos accionarios, derecho de retiro, dividendos.
- Reorganizaciones societarias, holdings, grupos empresariales.
- Insolvencia corporativa, concursal.

## Normas que invoca este perfil

### Norma matriz

- [`codigo-comercio`](../normativa/codigos/codigo-comercio.md) — Código de
  Comercio chileno. **Pendientes Art. 351+ (sociedades colectivas y en
  comandita), Art. 425+ (SRL).**

### Tipos societarios

- [`ley-18046-sociedades-anonimas`](../normativa/leyes/ley-18046-sociedades-anonimas.md) —
  SA abiertas y cerradas. **Eje del derecho societario chileno.**
- Ley 3.918 (SRL) — sociedad de responsabilidad limitada.
- Ley 19.857 — EIRL (empresa individual de responsabilidad limitada).
- Ley 20.190 — SpA (sociedad por acciones).
- Ley 20.659 — Régimen simplificado constitución sociedades (RSCS).

### Mercado de valores

- [`ley-18045-mercado-valores`](../normativa/leyes/ley-18045-mercado-valores.md) —
  LMV: emisores, intermediarios, OPA, OPV.
- [`ley-21314-gobierno-corporativo`](../normativa/leyes/ley-21314-gobierno-corporativo.md) —
  modernización GC SA abiertas (2021): transparencia, OPR, whistleblowing.
- [`ley-21000-cmf`](../normativa/leyes/ley-21000-cmf.md) — Comisión para
  el Mercado Financiero (regulador integrado).

### Compliance + integridad corporativa

- [`ley-20393-rppj`](../normativa/leyes/ley-20393-rppj.md) — RPPJ:
  responsabilidad penal de las personas jurídicas + MPD (Modelo de
  Prevención del Delito).
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  Delitos económicos: amplía catálogo, agrava penas, MPD refuerzo.
- [`ley-19913-lavado-activos`](../normativa/leyes/ley-19913-lavado-activos.md) —
  Lavado de activos + UAF: sujetos obligados, reportes ROS.
- [`ley-20393-rppj`](../normativa/leyes/ley-20393-rppj.md) +
  [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  base del **stack compliance corporativo** chileno.

### Probidad + lobby (cuando empresa contrata con Estado)

- [`ley-20880-probidad-publica`](../normativa/leyes/ley-20880-probidad-publica.md) —
  DIP, fideicomiso ciego.
- [`ley-20730-lobby`](../normativa/leyes/ley-20730-lobby.md) — Infolobby.

### Concursal

- [`ley-20720-concursal`](../normativa/leyes/ley-20720-concursal.md) —
  Reorganización y Liquidación; Superintendencia de Insolvencia y
  Reemprendimiento.

### Libre competencia (cuando hay fusión / abuso posición)

- [`dl-211-libre-competencia`](../normativa/leyes/dl-211-libre-competencia.md) —
  FNE, TDLC, control de fusiones.
- [`ley-20169-competencia-desleal`](../normativa/leyes/ley-20169-competencia-desleal.md) —
  competencia desleal (acción civil entre competidores).

### Propiedad industrial + IP

- [`ley-19039-propiedad-industrial`](../normativa/leyes/ley-19039-propiedad-industrial.md) —
  marcas, patentes, diseños (INAPI).
- [`ley-17336-propiedad-intelectual`](../normativa/leyes/ley-17336-propiedad-intelectual.md) —
  derecho de autor (DDI).

### Bancario + financiamiento

- [`ley-18092-letras-pagares`](../normativa/leyes/ley-18092-letras-pagares.md) —
  pagarés (instrumento operativo en financiamientos).
- [`ley-18010-operaciones-credito-dinero`](../normativa/leyes/ley-18010-operaciones-credito-dinero.md) —
  OCD: UF, intereses, TMC.

### Tributario societario

Para tributación de la sociedad → derivar a [`perfil-tributario`](tributario.md):
LIR (DL 824), IVA (DL 825), Reforma 21.713, Reducción exenciones 21.420.

### Laboral del directorio

Para deberes laborales del directorio → derivar a [`perfil-laboral`](laboral.md):
Ley Karin (21.643), inclusión (21.015), 40h (21.561).

## Red flags societarios (activación automática)

### En constitución / modificación

1. **Capital "aportado" no efectivamente pagado** → riesgo nulidad ante CMF
   en SA abierta; en cerradas, responsabilidad personal del accionista.
2. **Estatuto que prohíbe el derecho de retiro** → cláusula nula.
3. **Directorio sin independientes** en SA abierta → infringe Ley 18.046
   (3 directores indep. mínimo, según tamaño).
4. **Pactos de accionistas no inscritos** → no oponibles a terceros pero
   sí entre partes.
5. **Auditor externo sin rotación** después de período permitido → reclamo
   CMF.

### En gobierno corporativo

1. **Conflicto de interés del director** sin declaración + abstención →
   nulidad del acuerdo + responsabilidad civil.
2. **OPR (operación con partes relacionadas)** sin condiciones de mercado
   o sin aprobación del comité → riesgo CMF + acción de daños.
3. **Falta de comité de directores** en SA abierta sujeta a Ley 21.314 →
   infracción regulatoria.
4. **Filtración de información reservada** (insider trading) → cruce con
   Ley 18.045 + querella penal.
5. **Whistleblowing sin canal independiente** → infringe Ley 21.314.
6. **Acta de directorio sin firma de todos los asistentes** → no
   probatoria; riesgo procesal.

### En compliance / MPD

1. **MPD sin oficial de cumplimiento autónomo** (Art. 4 Ley 20.393) →
   no eficaz; no exime de RPPJ.
2. **MPD sin certificación** vigente → no opera la atenuación.
3. **MPD sin canal de denuncias** → no eficaz.
4. **MPD sin matriz de riesgos** documentada y actualizada → debilita
   defensa.
5. **Pago a funcionarios públicos** sin registro en Infolobby → riesgo
   delito + RPPJ.
6. **No reporte de operación sospechosa** (ROS) ante UAF en sujeto
   obligado → infracción + multa.

### En fusiones / OPA

1. **OPA sin folleto explicativo** o con información incompleta → CMF
   anula + sanción.
2. **Operación entre matriz y filial** sin OPR válida → impugnable por
   accionistas minoritarios.
3. **Fusión sin notificación a FNE** cuando aplica → multa hasta 30% de
   ventas + retroceso de la operación.

### En concursal

1. **Empresa en cesación de pagos prolongada** sin solicitud → directorio
   responde con su patrimonio (Art. 41 Ley 20.720).
2. **Pagos preferentes a acreedores relacionados** dentro del período
   sospechoso (1-2 años) → nulos por acción revocatoria concursal.
3. **Operaciones del directorio con conflicto durante insolvencia** →
   responsabilidad personal + civil + penal.

### En libre competencia

1. **Acuerdos horizontales** entre competidores (precios, mercados,
   licitaciones) → delación compensada o multa hasta 30% ventas.
2. **Cláusula de exclusividad** en contrato de distribución → análisis
   bajo TDLC.
3. **Operación de concentración no notificada** a FNE → multa + retroceso.

## Plazos críticos societarios

| Plazo | Norma | Días | Tipo |
|---|---|---|---|
| Convocatoria junta SA | Art. 59 Ley 18.046 | 15 / 30 | corridos |
| Derecho de retiro (declarar) | Art. 70 Ley 18.046 | 30 | hábiles |
| Aviso fusión a FNE | DL 211 | variable (umbral) | — |
| Información esencial a CMF | NCG 30 | hechos esenciales: día siguiente | — |
| Notificación de OPA | LMV | 5 | hábiles desde plan |
| Solicitud reorganización (procedimiento concursal) | Ley 20.720 | sin plazo legal pero diligencia | — |
| Período sospechoso revocatoria concursal | Ley 20.720 | 1-2 años retrospectivo | corridos |
| Renovación MPD (recomendado) | Práctica | 2-3 años | — |

## Skills que orquesta este perfil

- [`diagnostico`](../skills/diagnostico.md) — clasifica + activa este perfil
  si detecta keywords societarios.
- [`citas-verificables`](../skills/citas-verificables.md) — citas precisas
  a Código Comercio, Ley 18.046, LMV, etc.
- [`plazos`](../skills/plazos.md) — junta, retiro, OPA, etc.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) — eje
  para MPD, lobby, probidad, antilavado. **Skill principal de este perfil.**

## Casos típicos

(Pendientes — Fase 3:)

- Diseño / actualización de MPD para empresa mediana.
- Conflicto de interés del director: protocolo de abstención + acta.
- OPA en SA abierta: requisitos + plazos.
- Reorganización concursal vs liquidación: criterios.
- Pacto de accionistas: oponibilidad + cláusulas críticas.
- Joint venture entre empresas chilenas e internacionales.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado societario.
- Para SA abiertas, NCG + Circulares CMF son operativamente centrales
  (verificar siempre).
- Para grupos multinacionales, considerar tratados bilaterales,
  convenios de doble tributación, FATCA, CRS.
- Compliance bajo Ley 20.393 + Ley 21.595 es **técnico**: consultar
  abogado penal-corporativo + auditor de cumplimiento.

## Conexiones con otros perfiles

- [`perfil-tributario`](tributario.md) — toda dimensión fiscal.
- [`perfil-laboral`](laboral.md) — deberes del empleador, Ley Karin como
  delito atribuible.
- [`perfil-penal`](penal.md) — delitos corporativos, RPPJ, lavado.
- [`perfil-civil`](civil.md) — responsabilidad civil contractual y
  extracontractual de directores.
- [`perfil-concursal`](concursal.md) — insolvencia + reorganización.
