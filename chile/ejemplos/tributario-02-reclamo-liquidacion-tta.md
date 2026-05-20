---
ejemplo: tributario-02-reclamo-liquidacion-tta
rama: tributario
nivel: avanzado
archivos_invocados:
  - chile/normativa/codigos/codigo-tributario.md
  - chile/normativa/leyes/dl-824-renta.md
  - chile/perfiles/tributario.md
  - chile/skills/plazos.md
estado_revision: borrador-no-validado
---

# Ejemplo · Reclamo de liquidación SII ante TTA

## Escenario

> Soy gerente financiero de una empresa que recibió hace 60 días una
> liquidación del SII por ~$80 millones, alegando gastos rechazados +
> ingresos no declarados del año tributario 2022. No respondimos la
> citación previa por desorganización interna. ¿Tenemos opciones?
> ¿Cuánto cuesta + dura?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Verificar con
> tributarista antes de presentar el reclamo.

> **Invoca**: [`perfil-tributario`](../perfiles/tributario.md) +
> [`skill plazos`](../skills/plazos.md).

### Diagnóstico inmediato

⚠️ **Plazo crítico**: el reclamo ante TTA tiene **90 días** desde la
notificación (Art. 124 CT). Si recibieron la liquidación hace 60 días,
**quedan ~30 días**.

⚠️ **Pasaron la oportunidad de la Reposición Administrativa Voluntaria
(RAV)** del Art. 123 bis CT que solo tenía 30 días desde la liquidación.

### Régimen aplicable

Procedimiento de reclamación tributaria del **Art. 123+ del Código
Tributario** ante los **Tribunales Tributarios y Aduaneros (TTA)**, 17
regionales en Chile + segunda instancia ante la **Corte de
Apelaciones** correspondiente + casación ante la **Corte Suprema**.

### Opciones disponibles según etapa

| Etapa | Plazo | Disponible HOY |
|---|---|---|
| Respuesta a Citación | 1 mes desde citación | ❌ Vencida |
| RAV (Reposición Administrativa Voluntaria) | 30 días desde liquidación | ❌ Vencida |
| **Reclamo ante TTA** | **90 días desde liquidación** | ✅ **Quedan ~30 días** |
| Apelación a Corte de Apelaciones | 15 días desde sentencia TTA | n/a aún |
| Casación a CS | 15 días desde sentencia CA | n/a aún |

**Vía única hoy**: reclamo ante TTA. **Plazo crítico**.

### Acción operativa inmediata (próximos 30 días)

#### Día 1-3 — Análisis preliminar

- Solicitar todos los antecedentes de la auditoría SII.
- Revisar la liquidación: causales + cálculos + normas invocadas.
- Identificar **puntos de impugnación**:
  - Errores de derecho (interpretación legal SII vs jurisprudencia).
  - Errores de hecho (cálculos incorrectos).
  - Vicios procedimentales (notificaciones, fundamentación).
  - Prescripción (¿está en plazo el SII?).
- Calcular costo-beneficio del reclamo vs **pago + descuento de mora**.

#### Día 4-10 — Decisión estratégica

Tres opciones:

**A. Reclamar íntegramente** (cuando hay buenos argumentos):
- Pretender nulidad o reducción total.
- Mayor potencial de éxito pero mayor riesgo.

**B. Reclamar parcialmente + pagar lo no impugnado** (mixto):
- Reconocer lo correcto + impugnar lo discutible.
- Mantiene buena fe + reduce exposición.

**C. Acordar con SII vía RAVF** (Reposición Administrativa Voluntaria
Fundada):
- Aunque venció la RAV ordinaria, pueden negociar facilidades de pago.
- Beneficio: condonación parcial de multas + intereses según Ley
  21.039 (Subdirección de Fiscalización).

Para tu caso (sin haber contestado citación): **opción B o C** suelen
ser más realistas. Opción A requiere argumentos jurídicos sólidos.

#### Día 11-25 — Preparación del reclamo

- **Patrocinio de abogado habilitado** (obligatorio en TTA).
- **Recopilación de documentación**:
  - Facturas + contratos + libros contables del período.
  - Estados financieros auditados.
  - Documentación de respaldo de gastos cuestionados.
  - Antecedentes de la auditoría.
- **Peritajes** si requeridos (contable, técnico, especialista en
  industria).
- **Argumentación jurídica**:
  - Interpretación correcta de las normas LIR + CT.
  - Jurisprudencia favorable (CS Sala Tributaria + Cortes).
  - Doctrina relevante.

#### Día 26-30 — Presentación

- **Escrito de reclamo** ante TTA competente (regional o RM según
  domicilio tributario).
- **Acompañar todos los antecedentes**.
- **Pago de tasa judicial** (~0,5 UTM por escrito).
- **Notificación recíproca** al SII para que conteste.

### Procedimiento ante TTA (etapas siguientes)

#### Tras presentar el reclamo

1. **Notificación al SII**: 5 días.
2. **Contestación SII**: 20 días.
3. **Réplica del contribuyente** (si procede): 8 días.
4. **Audiencia preparatoria** (sin oralidad estricta): puntos de prueba.
5. **Período de prueba**: documental + pericial + testimonial.
6. **Audiencia de juicio** (si hay testimonio + alegatos).
7. **Sentencia**: 60 días desde término del período de prueba.

**Duración promedio**: 18-24 meses desde presentación hasta sentencia
TTA.

#### Recursos

- **Apelación** a Corte de Apelaciones: 15 días desde sentencia TTA.
- **Casación** a Corte Suprema: 15 días desde sentencia CA (limitada a
  errores de derecho + procedimiento).

**Duración total** (1ª + 2ª + casación): 3-5 años en casos complejos.

### Costos estimados

| Item | Costo aproximado |
|---|---|
| Honorarios abogado (TTA + CA) | UF 200-1.000 según complejidad |
| Peritajes | UF 100-500 |
| Documentación + tasaciones | UF 10-50 |
| Tasas judiciales | UF 1-5 |
| Auditoría contable de respaldo | UF 50-300 |
| **Total estimado** | **UF 350-1.800** (~$15M-78M) |

**Comparación con la deuda ($80M)**: el reclamo cuesta entre el **20%-
100% de la deuda**. Es viable si hay buenos argumentos. **NO conviene si
los argumentos son débiles**.

### Suspensión de la cobranza durante el reclamo

⚠️ **Importante**: la presentación del reclamo **NO suspende
automáticamente** la cobranza coactiva del SII. Para suspender:

- **Garantía** (boleta bancaria, hipoteca, prenda) por el monto en
  disputa + costas.
- O **acuerdo de no innovar** del propio tribunal con condiciones.
- O **medida cautelar** del propio TTA si demuestras irreparabilidad.

**Costo de la garantía**: ~1-3% anual del monto garantizado.

### Análisis de probabilidad de éxito (tipo de caso)

Sin haber visto los autos específicos:

| Causal | Probabilidad TTA |
|---|---|
| Gastos rechazados sin causal específica | media-alta (40-60%) |
| Ingresos no declarados (auditoría con documentación) | baja (10-25%) |
| Prescripción no observada por SII | alta si aplica (80%+) |
| Vicios procedimentales graves | media (30-50%) |
| Interpretación jurídica disputada con Circular | media-alta (50-70%) |

**Tu caso con "gastos rechazados + ingresos no declarados"**: mixto.
Análisis caso a caso.

### Posibilidad de transacción / acuerdo

#### Acuerdo de pago con facilidades (Tesorería)

- **Convenios** hasta 36 cuotas.
- **Condonación parcial** de intereses + multas según evolución.
- **Norma operativa**: Tesorería General de la República + Circulares
  SII.

#### Acuerdo extrajudicial con SII durante reclamo

- **Allanamiento parcial** del SII si argumentos son sólidos.
- **Conciliación** con descuento de multas (no del capital del
  impuesto).

### Decisión recomendada para tu caso

#### Hipótesis 1 — Si los argumentos jurídicos son sólidos

Reclamar íntegramente + solicitar suspensión cobranza vía garantía.

#### Hipótesis 2 — Si los argumentos son débiles + presupuesto limitado

- Negociar pago con facilidades + condonación parcial.
- No reclamar (la sentencia adversa puede empeorar el monto a pagar
  con intereses adicionales).

#### Hipótesis 3 — Caso mixto (más realista para tu situación)

- Reclamar parcialmente (solo los gastos rechazados con argumentos).
- Pagar la parte de ingresos no declarados (con plan de pago).
- Conciliar durante el procedimiento.

### Riesgo legal personal (gerente financiero)

Si el SII detecta **dolo** en los ingresos no declarados:

- **Delito tributario** (Art. 97 N° 4 CT): pena de presidio + multa.
- **Responsabilidad penal personal** del representante legal +
  administrador.
- **Cruce con Ley 21.595** (Delitos Económicos): tributarios en catálogo
  ampliado.

⚠️ **Recomendación**: si hay elementos de dolo, **NO reclamar sin
asesoría penal-tributaria especializada** (el reclamo puede ser usado
como confesión).

## Red flags activadas (perfil tributario)

- 🚩 **Citación SII sin respuesta dentro de plazo (1 mes)**: SII queda
  facultado para liquidar sin más trámite (ya ocurrió).
- 🚩 **Plazo de reclamo ante TTA**: 90 días — quedan 30 días.
- ⚠️ **Posible delito tributario** si hay dolo en ingresos no
  declarados.
- ⚠️ **Cobranza coactiva** del SII puede iniciar sin que se suspenda
  automáticamente.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por tributarista +
  abogado tributarista habilitado.
- **Patrocinio obligatorio** ante TTA — abogado habilitado.
- **Cada caso es único**: análisis detallado de la liquidación + auditoría
  es indispensable.
- **TTA** + **Cortes**: jurisprudencia abundante + criterios pueden
  cambiar.
- **Coordinación** entre auditor contable + abogado tributarista +
  eventualmente abogado penal-tributarista.

## Normas + skills invocados

- [`codigo-tributario`](../normativa/codigos/codigo-tributario.md) —
  Art. 123, 124, 200 (prescripción), 97 N° 4 (delito).
- [`dl-824-renta`](../normativa/leyes/dl-824-renta.md) — LIR (régimen
  sustantivo de gastos + ingresos).
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  delitos tributarios en catálogo ampliado.
- [`perfil-tributario`](../perfiles/tributario.md) — orquestador.
- [`skill plazos`](../skills/plazos.md) — cómputo del Art. 124 (90 días).
- [`skill citas-verificables`](../skills/citas-verificables.md).
