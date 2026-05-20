---
ejemplo: concursal-01-reorganizacion-vs-liquidacion
rama: concursal
nivel: avanzado
archivos_invocados:
  - chile/normativa/leyes/ley-20720-concursal.md
  - chile/normativa/leyes/ley-18046-sociedades-anonimas.md
  - chile/normativa/codigos/codigo-trabajo.md
  - chile/perfiles/concursal.md
estado_revision: borrador-no-validado
---

# Ejemplo · Empresa en cesación de pagos: reorganización vs. liquidación

## Escenario

> Asesoro a una empresa manufacturera chilena con 5 años en el mercado.
> Tiene activos por $800M, pasivos por $1.200M (incluyen $400M con bancos
> + $300M proveedores + $200M créditos laborales + $150M previsionales +
> $150M impuestos). Ventas en caída los últimos 18 meses. Tiene 35
> trabajadores. ¿Procedimiento concursal de reorganización o
> liquidación? ¿Cuál es la mejor estrategia?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Pendiente revisión
> por abogado concursal habilitado.

> **Invoca**: [`perfil-concursal`](../perfiles/concursal.md).

### Diagnóstico inicial

#### Indicadores de salud financiera

| Indicador | Valor |
|---|---|
| Activos | $800M |
| Pasivos | $1.200M |
| **Patrimonio** | **-$400M** (negativo) |
| Ratio cobertura | 0.67 |
| Cesación de pagos | confirmada por ratio |
| Trabajadores | 35 |
| Tendencia | en caída |

**Conclusión**: la empresa está **insolvente** (pasivos > activos) y en
**cesación de pagos efectiva**. Sin acción concursal pronto, los
directores incurren en **responsabilidad personal** por Art. 41 Ley
20.720.

⚠️ **Riesgo legal**: si los directores continúan operando sabiendo de
la insolvencia + sin acción concursal, pueden:

1. Responder con su patrimonio personal por deudas posteriores.
2. Configurar delitos de la **Ley 21.595** (administración desleal en
   contexto concursal).

### Modalidades aplicables

#### Reorganización (Empresa Deudora)

**Requisitos del Art. 53 Ley 20.720**:

- Empresa con **viabilidad económica** demostrable.
- **Estados financieros** del último período.
- **Propuesta de acuerdo** con acreedores.
- **Caja** suficiente para los próximos 30 días.

**Modalidades**:

- **Reorganización judicial**: con protección concursal completa
  (suspensión de cobranzas).
- **Reorganización simplificada** (extrajudicial): vía veedor + sin
  protección judicial completa.

**Plazo**: 30 días iniciales + extensión a 90 días para acuerdo.

**Aprobación del acuerdo**: requiere mayorías cualificadas por categoría
de acreedor (Art. 79 Ley 20.720).

#### Liquidación

**Modalidades**:

- **Voluntaria**: el deudor solicita.
- **Forzosa**: un acreedor con título ejecutivo demuestra cesación de
  pagos.

**Efecto**: liquidador toma control + venta de activos + pago en orden
de prelación.

### Análisis del caso

#### ¿Es viable la reorganización?

| Factor | Análisis |
|---|---|
| Caída de ventas 18 meses | ⚠️ Tendencia negativa fuerte |
| Patrimonio negativo $400M | ⚠️ Insolvencia estructural |
| Activos $800M | ✅ Significativos para garantías |
| 35 trabajadores | ✅ Operación significativa |
| Producto / mercado | ⏸ Verificar |
| Plan de negocio viable | ⏸ Verificar |
| Apoyo de bancos / proveedores | ⏸ Verificar |
| Caja para 30 días | ⏸ Verificar |

**Conclusión condicionada**: La reorganización requiere:

1. **Plan de negocio creíble** que muestre vuelta a viabilidad.
2. **Acuerdo previo informal** con acreedores principales (bancos +
   proveedores top 10).
3. **Caja** para los primeros 30 días + acreedores menores.
4. **Voluntad** del directorio para reducción de costos.

Si **estos 4 elementos no están**: liquidación es más realista +
ordenada.

### Comparación de alternativas

#### Opción A — Reorganización judicial

**Cómo funciona**:

1. Presentación de solicitud ante TR.
2. Resolución de admisibilidad + nombramiento de **Veedor**.
3. **Protección concursal**: suspende cobranzas + acciones ejecutivas.
4. **Junta de acreedores** para votar acuerdo.
5. Si se aprueba: cumplimiento del plan + supervisión del veedor.

**Pros**:

- **Protección automática** contra cobranzas.
- **Período para reorganizar** sin presión.
- **Continuidad de operaciones** posible.
- **Conservación de empleo** si viable.

**Contras**:

- **Costos** del procedimiento (honorarios veedor + abogados + auditorías).
- **Tiempo** (3-12 meses).
- **Reputacional**: la empresa queda marcada en el mercado.
- **Si falla**: deriva a liquidación con más pérdida.

#### Opción B — Liquidación voluntaria

**Cómo funciona**:

1. Solicitud del propio deudor.
2. Resolución de liquidación + nombramiento **Liquidador**.
3. Inventario + tasación de activos.
4. Venta de activos (subasta o trato directo según caso).
5. **Pago a acreedores en orden de prelación**.

**Pros**:

- **Ordenado**: el deudor controla el momento (no espera ser demandado).
- **Limitación de responsabilidad** personal de directores.
- **Cierre limpio** del negocio.
- **Trabajadores** cobran en su orden privilegiado.

**Contras**:

- **Pérdida** del negocio como negocio en marcha.
- **Activos** suelen venderse a precio menor en liquidación.
- **Reputacional** total.
- **Tiempo**: 1-3 años.

#### Opción C — Reorganización simplificada (extrajudicial)

- Menor formalidad.
- Sin protección judicial completa.
- Para empresas más pequeñas con acreedores cooperativos.
- **No es óptima** para este caso (empresa mediana con $1.200M en
  pasivos).

#### Opción D — Acuerdo de Reorganización Extrajudicial (ARE)

- Acuerdo preventivo extrajudicial con acreedores.
- Sin TR pero con homologación judicial.
- Requiere consenso amplio.

### Análisis de prelación de créditos (clave para decisión)

El **Art. 2470+ CC** + **Ley 20.720** definen el orden de pago en
liquidación. Aplicado a tu caso:

| Categoría | Monto | Probabilidad de cobro |
|---|---|---|
| **1. Costas del procedimiento** | ~$30-50M | 100% |
| **2. Créditos laborales (superprivilegio)** | $200M | 100% |
| **3. Créditos previsionales (privilegio)** | $150M | 100% |
| **4. Créditos tributarios (privilegio)** | $150M | 80% (depende de monto) |
| **5. Créditos con prenda/hipoteca específica** | $400M (bancos con garantía) | 90% del valor de la garantía |
| **6. Créditos quirografarios** | $300M (proveedores) | **10-30%** |

**Conclusión**:

- Trabajadores: cobran completo (prioridad legal).
- Bancos garantizados: cobran sobre los activos hipotecados.
- Previsionales + tributarios: cobran completo (privilegio).
- **Proveedores sin garantía**: probablemente recuperen 10-30% solamente.

Esto significa que en la **liquidación**, los proveedores quirografarios
podrían **preferir un acuerdo de reorganización** que les ofrezca un %
mayor (ej. 50% en cuotas vs 10-30% en liquidación).

### Recomendación operativa

#### Si se cumplen las 4 condiciones de la reorganización

**Opción A — Reorganización judicial** con plan que incluya:

- **Quita** del 30%-50% sobre créditos quirografarios (proveedores).
- **Espera** de 24-36 meses para créditos garantizados.
- **Pago completo** a trabajadores + previsionales + tributarios.
- **Reducción de personal** (con indemnización conforme a CT).
- **Reorientación del negocio** (cambio de producto, mercado, gestión).

**Probabilidad de éxito** del acuerdo: media (60-70%) si los acreedores
ven viable la propuesta + comparan con su recuperación en liquidación.

#### Si las condiciones NO se cumplen

**Opción B — Liquidación voluntaria** ahora, antes de:

- Que un acreedor solicite liquidación forzosa (peor reputacional).
- Que los directores incurran en responsabilidad personal (Art. 41).
- Que se configuren delitos concursales (Ley 21.595).

### Plan operativo siguiente

#### Semana 1 — Diagnóstico

1. **Auditoría exprés** de viabilidad operativa:
   - Análisis de la causa de la caída (mercado, gestión, producto).
   - Proyección a 12 meses con + sin acción concursal.
   - Estimación de quita / espera viable.
2. **Sondeo informal** con bancos principales + proveedores top 10:
   - ¿Aceptarían un acuerdo de reorganización?
   - ¿Qué condiciones son razonables?
3. **Análisis legal** del riesgo penal-corporativo (Art. 41 Ley 20.720
   + Art. 470 Ley 21.595).

#### Semana 2 — Decisión

Reunión del directorio + accionistas + asesores legales + auditor:

- **Decisión**: reorganización vs liquidación.
- **Plan de comunicación** a trabajadores (cuándo + cómo).
- **Continuidad operativa** durante el procedimiento.

#### Semana 3-4 — Presentación

Si reorganización:

- **Solicitud** al TR con plan + propuesta + acreedores categorizados.
- **Comunicación** a trabajadores + sindicato (si existe).
- **Coordinación** con bancos para mantener líneas operativas.

Si liquidación:

- **Solicitud** ante TR.
- **Comunicación** ordenada.
- **Plan de venta** ordenada de activos.

#### Mes 2-3 — Procedimiento

Trabajo intenso con veedor o liquidador según opción.

### Responsabilidad de directores

#### Si actúan ahora (antes de presión externa)

- **Limitación** de responsabilidad personal.
- Cumplimiento del **deber fiduciario**.
- Protección en caso de futuros litigios.

#### Si continúan operando sin acción

- **Responsabilidad personal** Art. 41 Ley 20.720 por deudas
  posteriores a la cesación de pagos.
- **Delitos concursales** (Ley 21.595 + Art. 470+ CP).
- **Acción derivativa** de los accionistas minoritarios.
- **Acción de los acreedores** contra el patrimonio personal.

### Trabajadores: protección especial

#### En liquidación

- **Superprivilegio** del Art. 2472 CC: cobran primero.
- **Indemnizaciones** legales por años de servicio.
- **Cesantía AFC**: el seguro cubre parte de la transición.
- **DT** activa para resguardar derechos.

#### En reorganización

- El plan **debe respetar** la continuidad laboral.
- Si hay despidos, **indemnizaciones** se pagan conforme a CT.
- El **Fondo de Solidaridad** de cesantía está disponible.

## Red flags activadas (perfil concursal)

- 🚩 **Empresa con cesación de pagos** sin acción concursal:
  responsabilidad personal del directorio (Art. 41).
- 🚩 **Pagos a relacionados** en período sospechoso (1-2 años):
  revocables.
- 🚩 **Continuidad operacional** sin autorización: ineficacia de actos
  durante liquidación.
- ⚠️ **Distribución de dividendos** en insolvencia: nula + revocable.
- ⚠️ **Pagos preferenciales** a acreedores conocidos pre-concurso:
  revocables.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado concursal +
  contador-auditor.
- **Decisión** entre reorganización vs liquidación requiere análisis
  caso a caso de los **4 elementos clave** (viabilidad, acreedores,
  caja, voluntad directorio).
- **Plazos perentorios**: período sospechoso (1-2 años retrospectivo),
  acción revocatoria.
- **SIR** dictámenes operativamente centrales.
- **Sectores regulados** (banca, seguros, AFP) tienen régimen especial.

## Normas + skills invocados

- [`ley-20720-concursal`](../normativa/leyes/ley-20720-concursal.md) —
  reorganización + liquidación + SIR.
- [`ley-18046-sociedades-anonimas`](../normativa/leyes/ley-18046-sociedades-anonimas.md) —
  responsabilidad directores.
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  delitos concursales.
- [`codigo-trabajo`](../normativa/codigos/codigo-trabajo.md) —
  superprivilegio + indemnizaciones.
- [`codigo-civil`](../normativa/codigos/codigo-civil.md) — Art. 2470+
  (prelación de créditos).
- [`perfil-concursal`](../perfiles/concursal.md) — orquestador.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) —
  prevención + defensa.
