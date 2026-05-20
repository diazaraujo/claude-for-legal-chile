---
ejemplo: societario-01-disenar-mpd
rama: societario
nivel: intermedio
archivos_invocados:
  - chile/normativa/leyes/ley-20393-rppj.md
  - chile/normativa/leyes/ley-21595-delitos-economicos.md
  - chile/normativa/leyes/ley-21643-acoso-laboral.md
  - chile/skills/compliance-corporativo.md
estado_revision: borrador-no-validado
---

# Ejemplo · Diseñar Modelo de Prevención del Delito (MPD)

## Escenario

> Soy gerente legal de una empresa industrial chilena de tamaño mediano
> (250 empleados, ventas de UF 800.000 anuales). Acabamos de ganar una
> licitación pública con MOP que exige acreditación de MPD. ¿Qué incluye
> un MPD válido bajo Ley 20.393 modificada por Ley 21.595? ¿Cuánto demora
> implementarlo + certificarlo?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Verificar con abogado
> penal-corporativo + auditor de cumplimiento antes de aprobar el MPD.

> **Invoca**: [`compliance-corporativo`](../skills/compliance-corporativo.md)
> + [`perfil-societario`](../perfiles/societario.md).

### Régimen aplicable

La **Ley 20.393 (RPPJ)** establece la responsabilidad penal de las
personas jurídicas y permite **eximir o atenuar** la responsabilidad si
la empresa demuestra haber implementado un MPD eficaz **antes del
delito**.

La **Ley 21.595 (Delitos Económicos, 2023)** **amplió drásticamente** el
catálogo de delitos atribuibles:

- Antes (Ley 20.393 original): cohecho, financiamiento del terrorismo,
  lavado de activos.
- Ahora (con Ley 21.595): ~250 delitos económicos atribuibles.

La **Ley 21.643 (Ley Karin, 2024)** incorporó el acoso laboral + sexual
como **delito atribuible** a la PJ si forma parte de una "**falla del
modelo**".

### Componentes de un MPD eficaz (Art. 4 Ley 20.393)

#### 1. Designación de un Encargado de Prevención (EP)

- **Persona o cuerpo colegiado** con **autonomía suficiente** del
  directorio + gerencia general.
- Acceso directo al directorio.
- Sin dependencia jerárquica de la gerencia ejecutiva.
- Recursos suficientes (presupuesto + personal + tecnología).
- **Duración**: máximo 3 años (renovable).
- En empresas pequeñas: el directorio puede asumir directamente la
  función.

#### 2. Definición de medios + facultades del EP

- Acceso a información de todos los procesos.
- Facultad de investigar denuncias.
- Reporte directo al directorio (mínimo trimestral).
- Independencia financiera.

#### 3. Sistema de prevención

Identificar:

- **Actividades** de la empresa con riesgo de generación de delitos
  (matriz de riesgos).
- **Controles** preventivos por tipo de delito.
- **Procedimientos** para registrar y reportar.
- **Sanciones internas** por incumplimiento.

#### 4. Supervisión + actualización

- **Auditorías internas** periódicas (anual mínimo).
- **Actualización** del modelo ante:
  - Cambios legislativos (Ley 21.595, Ley 21.643).
  - Cambios en el giro de la empresa.
  - Detección de nuevos riesgos.

#### 5. Canal de denuncias

- Anónimo + confidencial.
- Protección al denunciante.
- Investigación documentada.
- Cruce con Ley 21.314 (whistleblowing en SA abiertas).

#### 6. Capacitación obligatoria

- Para directores, ejecutivos, empleados.
- Documentada (asistencia + contenido + evaluación).
- Periódica (mínimo anual).

### Catálogo de delitos a cubrir (selección crítica)

| Delito | Norma | Aplicabilidad a tu empresa |
|---|---|---|
| Cohecho activo a funcionario público | Ley 20.393 + Art. 250 CP | ⚠️ ALTA (licitación MOP) |
| Cohecho entre privados | Ley 21.595 | media |
| Lavado de activos | Ley 19.913 | ⚠️ ALTA (UF 800k ventas) |
| Receptación | Ley 21.595 | media |
| Financiamiento terrorismo | Ley 18.314 | baja |
| Administración desleal | Ley 21.595 | media |
| Delitos tributarios | Ley 21.595 + CT | ⚠️ ALTA |
| Delitos contra libre competencia | Ley 21.595 + DL 211 | media-alta |
| Delitos contra el medio ambiente | Ley 21.595 + Ley 19.300 | depende sector |
| Acoso laboral / sexual (Ley Karin) | Ley 21.643 | ⚠️ ALTA |
| Delitos informáticos | Ley 21.663 | media |
| Insider trading | Ley 21.595 + LMV | baja (no SA abierta) |
| Estafa | Art. 467 CP | media |

### Cronograma de implementación

| Fase | Duración | Hitos |
|---|---|---|
| **1. Diagnóstico** | 1 mes | Matriz de riesgos por proceso |
| **2. Diseño del MPD** | 2 meses | Manual + procedimientos + canal denuncias |
| **3. Implementación inicial** | 2 meses | Designación EP + capacitación + difusión |
| **4. Operación piloto** | 3 meses | Casos reales + ajustes |
| **5. Auditoría externa** | 1 mes | Test independiente |
| **6. Certificación** | 1 mes | Por empresa certificadora autorizada |

**Total**: ~10 meses para certificación inicial.

⚠️ **Atención**: para la licitación MOP, podrías necesitar acreditar al
menos los **4 primeros pasos** + un compromiso de certificación dentro
de los siguientes 6-12 meses. Verificar bases específicas de la
licitación.

### Empresas certificadoras

Principales en Chile (sin orden de preferencia, verificar acreditación
vigente):

- Bureau Veritas.
- Deloitte.
- KPMG.
- PwC.
- AENOR.
- Algunas certificadoras especializadas en compliance corporativo.

**Costo aproximado** (referencial, varía por tamaño + complejidad):

- Diseño + asesoría: UF 500 - 2.000.
- Capacitación: UF 100 - 500.
- Auditoría + certificación: UF 300 - 1.000.
- **Total inicial**: UF 900 - 3.500.
- Mantenimiento anual: ~UF 200 - 500.

Para una empresa de UF 800.000 ventas, esto representa **0,1% - 0,4%**
de tus ventas — costo razonable para mitigar exposición + ganar
licitaciones públicas.

### Efectos prácticos del MPD certificado

1. **Atenuación / eximición de RPPJ**: si pese al MPD ocurre un delito,
   la empresa puede invocar **debido control** como defensa.
2. **Cumplimiento de bases de licitación**: muchas licitaciones
   públicas + grandes empresas privadas exigen MPD certificado.
3. **Cobertura D&O**: pólizas de directores + oficiales requieren MPD
   para coberturas completas.
4. **Due diligence M&A**: el MPD agrega valor en una venta de la
   empresa.

### Cláusula contractual mínima con proveedores + colaboradores

Una vez implementado el MPD, todos los contratos con proveedores +
colaboradores deben incluir cláusula tipo:

> "El proveedor declara conocer y comprometerse a respetar el Modelo
> de Prevención del Delito de [EMPRESA], conforme a la Ley 20.393
> y sus modificaciones. Cualquier incumplimiento dará derecho a
> [EMPRESA] a terminar el contrato sin indemnización + reportar a las
> autoridades correspondientes."

### Red flags durante el diseño + operación

- 🚩 EP designado pero sin autonomía real (reporta a la gerencia general).
- 🚩 Matriz de riesgos genérica copiada de otra empresa.
- 🚩 Canal de denuncias sin garantías al denunciante.
- 🚩 Capacitación realizada solo al equipo de compliance + sin
  acreditación de asistencia del resto.
- 🚩 MPD certificado pero sin auditoría anual de operación efectiva.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado penal-
  corporativo + auditor.
- **Ley 21.595** introdujo cambios profundos al catálogo de delitos +
  agrava penas — el MPD pre-2023 debe **actualizarse**.
- **Ley 21.643 (Karin)**: caso a caso requiere análisis de cómo el MPD
  cubre el riesgo de acoso (cruce con perfil laboral).
- **Certificación**: no garantiza eximición automática; el tribunal
  evalúa **eficacia operativa**, no sólo certificación formal.
- **Coordinación** con áreas RRHH, Auditoría, Finanzas, Operaciones es
  crítica.

## Normas + skills invocados

- [`ley-20393-rppj`](../normativa/leyes/ley-20393-rppj.md) — RPPJ +
  MPD.
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  catálogo ampliado.
- [`ley-21643-acoso-laboral`](../normativa/leyes/ley-21643-acoso-laboral.md) —
  acoso como delito atribuible.
- [`ley-19913-lavado-activos`](../normativa/leyes/ley-19913-lavado-activos.md) —
  lavado + UAF.
- [`perfil-societario`](../perfiles/societario.md) — orquestador.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) —
  skill principal.
