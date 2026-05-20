---
ejemplo: civil-01-vicios-ocultos-inmueble
rama: civil
nivel: intermedio
archivos_invocados:
  - chile/normativa/codigos/codigo-civil.md
  - chile/normativa/leyes/ley-21484-compraventa-inmuebles.md
  - chile/normativa/leyes/ley-19496-consumidor.md
  - chile/perfiles/civil.md
estado_revision: borrador-no-validado
---

# Ejemplo · Vicios ocultos en compraventa de inmueble con financiamiento

## Escenario

> Mi clienta compró un departamento hace 8 meses por UF 3.500 con
> crédito hipotecario. Tras instalarse descubrió: humedad estructural en
> 3 muros, sistema eléctrico deficiente, filtración en techo. Ninguno
> era visible en visita. La inmobiliaria + corredora aseguraron que el
> departamento "estaba en perfectas condiciones". ¿Qué acciones tiene?
> ¿Sirve la Ley 21.484?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Pendiente revisión
> por abogado civil-inmobiliario.

> **Invoca**: [`perfil-civil`](../perfiles/civil.md).

### Régimen aplicable — análisis dual

#### Vía 1: Régimen general del Código Civil (acción redhibitoria)

**Art. 1857+ CC** regula los **vicios redhibitorios**:

- **Definición**: vicio existente al tiempo de la venta, **oculto** + de
  cierta **gravedad** + **no conocido** por el comprador.
- **Acciones**:
  - **Acción redhibitoria** (Art. 1858 CC): resolución del contrato +
    restitución del precio.
  - **Acción quanti minoris** (Art. 1858 CC): reducción del precio
    proporcional.
- **Plazo de prescripción**:
  - Acción redhibitoria: **6 meses** desde entrega real (Art. 1866 CC).
  - Acción quanti minoris: **1 año** desde entrega real.

**Problema para tu caso**: ya pasaron 8 meses → **acción redhibitoria
prescrita**. Solo queda **acción quanti minoris** (con 4 meses por
delante).

#### Vía 2: Ley 21.484 (2022) — responsabilidad solidaria vendedor + intervinientes

**Cuando hay financiamiento bancario**, la Ley 21.484 introduce
responsabilidad solidaria por **información falsa** del vendedor y los
intervinientes (corredor, tasador, asesor financiero).

- **Sujeto protegido**: comprador persona natural con financiamiento
  hipotecario.
- **Hecho gatillante**: **información falsa o engañosa** sobre estado
  del inmueble.
- **Responsables solidarios**: vendedor + intervinientes que hayan
  participado.
- **Acciones**:
  - **Indemnización** por daño material + moral.
  - **Resolución del contrato** + restitución.
- **Plazo de prescripción**: **5 años** desde el descubrimiento.

**Ventaja**: tu cliente tiene tiempo + responsabilidad ampliada.

#### Vía 3: Ley 19.496 (Protección Consumidor)

Si la vendedora es **profesional** (inmobiliaria), aplica el régimen de
consumidor:

- **Garantía legal** (Art. 21 LPC): productos deben servir para uso al
  que están destinados.
- **Información veraz** (Art. 28 LPC): publicidad y representaciones no
  pueden ser engañosas.
- **Plazo**: 6 meses desde recepción.
- **Acción SERNAC** previa o **demanda en JPL**.

**Problema para tu caso**: plazo de 6 meses ya vencido para algunas
acciones. Pero la **información engañosa** mantiene plazos más amplios
por dolo civil.

### Cruce + estrategia

Tu cliente tiene **3 vías paralelas**:

| Vía | Estado | Acción |
|---|---|---|
| CC redhibitoria | Prescrita | — |
| CC quanti minoris | Vigente 4 meses | Posible |
| **Ley 21.484** | **Vigente 4 años, 4 meses** | **Principal** |
| LPC | Algunas prescritas | Subsidiaria por dolo |

**Recomendación**: **Ley 21.484 como acción principal** + Art. 1858 CC
quanti minoris + Art. 19.496 por dolo como subsidiarias.

### Acción operativa

#### Etapa 1 — Recopilación de evidencia (próximas 4 semanas)

1. **Peritaje técnico** independiente:
   - Constructora o ingeniero civil.
   - Acreditación de vicios + su antigüedad (pre o post compraventa).
   - Costo de reparación estimado.
   - **Vicio existente al tiempo de la compra** (clave para Art. 1858
     CC + Ley 21.484).
2. **Documentación de las representaciones falsas**:
   - Folleto publicitario del inmueble.
   - Correos + mensajes WhatsApp con la corredora.
   - Tasación bancaria (si quedó como respaldo).
   - Cláusula de "estado del inmueble" del contrato.
3. **Cronología** del descubrimiento:
   - Fecha de recepción.
   - Fecha del primer indicio.
   - Acciones intentadas para reparar (si hubo).
4. **Costos** asumidos por la clienta:
   - Reparaciones que ya realizó.
   - Tratamiento humedad / consulta médica si afectó salud.
   - Costos de mudanza temporal (si aplica).
5. **Tasación actual** del inmueble vs valor pagado.

#### Etapa 2 — Carta extrajudicial (10 días antes de demanda)

A la vendedora + intervinientes (corredora + tasadora + asesor
financiero del banco) en cobertura solidaria:

> "Estimados:
>
> En relación con la compraventa del inmueble [DIRECCIÓN] de
> [FECHA] entre [VENDEDORA] y [COMPRADORA], y con cargo a las
> responsabilidades solidarias del Art. 2 de la Ley 21.484, manifiesto
> lo siguiente:
>
> El inmueble presenta vicios ocultos no informados al momento de la
> compraventa, consistentes en [LISTAR + adjuntar peritaje]. El costo
> de reparación es de $[X] según informe pericial adjunto.
>
> Conforme a la Ley 21.484, los suscritos solicitan la indemnización
> de los daños materiales y morales por el monto de $[X], en los
> términos del Art. 1 ibídem.
>
> Plazo para respuesta: 15 días hábiles. En caso de negativa,
> procederemos vía judicial.
>
> Atentamente."

#### Etapa 3 — Demanda

**Tribunal competente**: Juzgado de Letras Civil del lugar del
inmueble (Art. 134 COT — competencia inmueble).

**Procedimiento**: ordinario o sumario según cuantía.

**Pretensiones**:

1. **Principal**: indemnización Ley 21.484 por daño material + moral.
2. **Subsidiaria 1**: quanti minoris Art. 1858 CC.
3. **Subsidiaria 2**: indemnización LPC por dolo.

**Demandados solidarios**:

- Vendedora (persona o inmobiliaria).
- Corredora de propiedades.
- Tasadora (si fue independiente).
- Banco (si su tasador interno fue determinante).

### Cálculo de exposición

#### Daño material

- Reparaciones: $15M (según peritaje).
- Costos asumidos por temporal: $2M.
- Diferencia de tasación actualizada: $5-10M.
- Intereses + reajustes: 5%-10%.

#### Daño moral

- Frustración del proyecto de vida (vivienda principal): $3-10M.

#### Total estimado

**$25M - $40M**. La inmobiliaria + intervinientes prefieren transar al
70-80% de este monto típicamente.

### Riesgos para la cliente

#### Si pierde la demanda

- Costas judiciales (~5%-10% del monto demandado).
- Costos de peritajes propios (~$2-3M).
- Tiempo + estrés.

#### Si gana parcialmente

- Recuperación proporcional + posible mediación favorable.

#### Recomendación realista

Probabilidad de éxito **alta** dado:

1. Vicios objetivos + acreditables.
2. Información falsa documentable.
3. Ley 21.484 reciente con doctrina pro-comprador.
4. Solidaridad amplía cobertura financiera.

### Tiempos estimados

- Acumulación de evidencia: 1 mes.
- Mediación extrajudicial: 1-2 meses.
- Procedimiento ordinario civil: 18-36 meses (1ª instancia + apelación).
- Sentencia firme + cobro: hasta 4 años.

**Si hay buena fe + voluntad de transar**: 3-6 meses con acuerdo
extrajudicial.

### Alternativa: arbitraje (si el contrato lo contempla)

Si el contrato de compraventa tiene **cláusula arbitral**: ir a
arbitraje en lugar de Tribunales Civiles.

- **Más rápido** (6-18 meses).
- **Costoso** en honorarios árbitro + actuaciones.
- **Sentencia final** sin apelación (salvo casos excepcionales).

## Red flags activadas (perfil civil)

- 🚩 **Compraventa de inmueble con vicios ocultos** + financiamiento
  hipotecario: cruce con Ley 21.484 (responsabilidad solidaria).
- 🚩 **Información de la corredora** "perfectas condiciones" = vicio
  informativo: ampliación responsables solidarios.
- ⚠️ **Acción redhibitoria CC prescrita** (6 meses); priorizar Ley 21.484
  con 5 años desde descubrimiento.
- ⚠️ **Cláusula arbitral** del contrato puede cambiar el foro.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado civil-
  inmobiliario.
- **Peritaje técnico independiente** es el eje de la prueba —
  invertir en uno de calidad.
- **Cláusulas exoneratorias** ("vendido tal como se ve") son
  generalmente **inoponibles** contra dolo o vicios ocultos del
  vendedor.
- **Banco no responde** si su tasación fue meramente referencial; sí
  responde si actuó como tasador definitivo.
- **Régimen sucesoral**: si vendedora fallece durante el proceso,
  acción continúa contra herederos hasta el monto de la herencia.

## Normas + skills invocados

- [`codigo-civil`](../normativa/codigos/codigo-civil.md) — Art. 1857-1869
  (vicios redhibitorios) + Art. 1546 (buena fe contractual).
- [`ley-21484-compraventa-inmuebles`](../normativa/leyes/ley-21484-compraventa-inmuebles.md) —
  responsabilidad solidaria por información falsa.
- [`ley-19496-consumidor`](../normativa/leyes/ley-19496-consumidor.md) —
  garantía legal + información veraz.
- [`codigo-procedimiento-civil`](../normativa/codigos/codigo-procedimiento-civil.md) —
  procedimiento.
- [`perfil-civil`](../perfiles/civil.md) — orquestador.
- [`skill plazos`](../skills/plazos.md) — prescripciones de cada vía.
