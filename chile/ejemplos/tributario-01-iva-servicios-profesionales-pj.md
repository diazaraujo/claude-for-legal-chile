---
ejemplo: tributario-01-iva-servicios-profesionales-pj
rama: tributario
nivel: intermedio
archivos_invocados:
  - chile/normativa/leyes/ley-21420-reduccion-exenciones.md
  - chile/normativa/leyes/dl-825-iva.md
  - chile/normativa/codigos/codigo-tributario.md
estado_revision: borrador-no-validado
---

# Ejemplo · Servicios profesionales prestados por SpA — IVA desde 2023

## Escenario

> Tengo una sociedad por acciones (SpA) unipersonal que presta servicios
> de consultoría en ingeniería. Antes de 2023 facturaba sin IVA (servicio
> profesional exento). Mi contador me dice que ahora debo cobrar IVA 19%.
> Mis clientes —principalmente empresas— protestan. ¿Es obligatorio?
> ¿Hay alguna estructura que me permita evitarlo?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Verificar con
> tributarista habilitado antes de cambiar estructura societaria.

> **Invoca**: [`perfil-tributario`](../perfiles/tributario.md).

### Régimen aplicable

La **Ley 21.420 (2022)** —Reducción de Exenciones Tributarias— modificó
el **DL 825** (IVA) para incluir los **servicios profesionales prestados
por personas jurídicas** dentro del hecho gravado, con vigencia desde el
**1 de enero de 2023**.

> **[VERIFICAR]** Cambio operativo: Art. 8 letra G del DL 825 incluye
> ahora los servicios prestados por PJ que antes estaban exentos
> (consultoría profesional, asesoría técnica, ingeniería, arquitectura,
> abogacía corporativa, contabilidad, etc.).

### Régimen actual (desde 2023)

| Modalidad | IVA | Justificación |
|---|---|---|
| **Persona Natural** con boleta de honorarios | **Exento** | Servicio personal del profesional |
| **SpA / SA / SRL / EIRL** con factura | **Gravado 19%** | Servicio prestado por persona jurídica |

**Tu caso (SpA unipersonal)**: **gravado con IVA**. No hay forma directa
de evitarlo manteniendo la estructura SpA.

### Por qué se eliminó la exención

El SII argumentó:

1. **Equidad horizontal**: dos profesionales prestando el mismo servicio
   tributaban distinto según su forma jurídica.
2. **Recaudación**: la exención generaba pérdida fiscal significativa.
3. **Simplicidad regulatoria**: armonizar el tratamiento con el régimen
   general del IVA.

### ¿Hay forma de evitarlo?

**Opciones legales** (analizar cada una con tributarista):

#### Opción A — Disolver la SpA + facturar como PN

- **Cómo**: disolución de la SpA + entrega de bienes al socio + emisión
  de boletas de honorarios a futuro.
- **Pros**: vuelves a exención de IVA.
- **Contras**:
  - Pierdes ventajas de la PJ (limitación responsabilidad, sucesión).
  - Tu tributación pasa a Global Complementario (probable mayor tasa
    marginal).
  - Disolución tiene costos + plazos.
  - Liquidación de activos podría tener efecto tributario.
- **Cuándo conviene**: profesional independiente con clientes
  individuales que NO usan crédito fiscal.

#### Opción B — Mantener SpA y trasladar IVA al cliente

- **Cómo**: continuar facturando con IVA 19%.
- **Pros**:
  - Mantienes la estructura PJ.
  - Puedes **descontar crédito fiscal** del IVA de tus compras
    (insumos, software, viajes, etc.).
  - Tus clientes empresariales usan ese IVA como crédito fiscal en su
    propio F29.
- **Contras**: clientes **no contribuyentes IVA** (PN finales, ONGs)
  sienten el costo neto del 19%.
- **Cuándo conviene**: clientes principalmente empresariales (tu caso).

#### Opción C — Estructura mixta

- **Cómo**: mantener SpA para algunos servicios + emitir boletas de
  honorarios personales para servicios "personalísimos" donde haya
  base legal para diferenciar.
- **Pros**: optimización parcial.
- **Contras**:
  - Riesgo de cuestionamiento SII por simulación.
  - Requiere documentación rigurosa del rol PN vs PJ.
  - Solo viable si efectivamente prestas servicios de naturaleza
    diferenciada.
- **Cuándo conviene**: casos específicos, asesorado por tributarista.

#### Opción D — Esperar (no recomendado)

No actuar = facturas no afectas + sanción del SII en fiscalización +
intereses + reajustes + posible delito tributario (Art. 97 N° 4 CT —
declaración maliciosa).

### Tu caso específico (SpA unipersonal de consultoría a empresas)

**Recomendación: Opción B (mantener SpA + trasladar IVA).**

Razones:

1. **Clientes empresariales** usan el IVA como crédito fiscal → costo
   neto = $0 para ellos.
2. **Mantienes limitación de responsabilidad** de la SpA.
3. **Crédito fiscal** por compras (PC, software, viajes, oficina) →
   recuperación efectiva de IVA pagado.
4. **Estructura simple** sin reorganización.

**Comunicación a tus clientes**:

> "Estimado cliente:
>
> A partir del 1° de enero de 2023, conforme a la Ley 21.420 que
> modifica el DL 825 (IVA), los servicios profesionales prestados por
> personas jurídicas pasan a estar afectos a IVA. En consecuencia,
> nuestras facturas a partir de esa fecha incluirán el 19% de IVA.
>
> Cabe destacar que **este IVA constituye crédito fiscal** que vuestra
> empresa puede descontar de su propio IVA débito en el Formulario 29
> mensual, por lo que el **costo efectivo del servicio se mantiene
> inalterado**.
>
> Atentamente,
> [TU SpA]"

### Pasos operativos para cumplir

#### Paso 1 — Inscripción como contribuyente de IVA

Si aún no estás inscrito (probable que sí porque tienes RUT como PJ):

- Aviso al SII vía **Inicio de Actividades** modificación.
- **Caracterización** del giro como afecto a IVA.

#### Paso 2 — Emisión de facturas afectas

- **Factura electrónica** con tasa 19%.
- **Detalle del servicio** + monto neto + IVA + total.

#### Paso 3 — Declaración + pago mensual (Form. 29)

- **Plazo**: hasta el día 12 del mes siguiente (con extensión hasta 20
  si se cumple buena fe).
- **Cálculo**: IVA débito (de facturas emitidas) - IVA crédito (de
  facturas recibidas).

#### Paso 4 — Crédito fiscal por compras

- **Facturas de compra** con IVA: descontable en F29.
- **Documentar** uso (relación con el giro).
- **Casos típicos descontables**:
  - Computadores + software.
  - Servicios profesionales recibidos (legal, contable).
  - Telecomunicaciones (afectas a IVA).
  - Combustible para viajes de trabajo.
  - Arriendo de oficina (si está afecto).

#### Paso 5 — Operación Renta + IVA armonizada

- **Declaración Renta anual (F22)**: refleja ingresos + IVA débito y
  crédito.
- **Conciliación** con F29 mensuales.

### Riesgo si no aplicas IVA

| Plazo | Sanción | Norma |
|---|---|---|
| Hasta 60 días | Intereses moratorios + reajuste UTM | CT |
| Tras citación SII | Multa 50%-300% del IVA omitido | Art. 97 CT |
| Si hay maliciosidad | Delito tributario | Art. 97 N° 4 CT + Ley 21.595 |
| Reincidencia | Cierre temporal del establecimiento | Art. 97 N° 10 CT |
| Cobranza coactiva | Embargo + apremio | CT |

### Beneficios compensatorios

Aunque cobres IVA, hay ventajas:

1. **Crédito fiscal** por insumos → recuperas IVA pagado.
2. **No pierdes la exención de Primera Categoría** (tu SpA sigue
   tributando renta sobre utilidades, no sobre todo el ingreso).
3. **Eligibilidad para licitaciones públicas** que requieren
   contribuyente IVA.

## Red flags activadas (perfil tributario)

- 🚩 **Servicio profesional prestado por PJ después de 2023** sin emisión
  de factura afecta a IVA (Ley 21.420): infracción + multa.
- ⚠️ **Reorganización societaria** (Opción A) requiere análisis previo
  de implicancias tributarias completas.
- ⚠️ **Estructura mixta** (Opción C): riesgo simulación si no hay
  diferenciación efectiva.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por tributarista.
- **Circulares + Oficios Ordinarios SII** sobre Ley 21.420 son
  operativamente centrales — verificar versiones vigentes.
- **Régimen Pyme** (Art. 14 D LIR) puede modificar el análisis para
  empresas pequeñas.
- **Exenciones específicas** subsisten para casos especiales (ej.
  algunos servicios prestados por SpA unipersonal con estructura
  análoga a profesional independiente — sujeto a análisis caso a
  caso por el SII).
- **Convenios para evitar doble tributación** pueden modificar régimen
  si el cliente es extranjero.

## Normas + skills invocados

- [`ley-21420-reduccion-exenciones`](../normativa/leyes/ley-21420-reduccion-exenciones.md) —
  Reducción de exenciones tributarias.
- [`dl-825-iva`](../normativa/leyes/dl-825-iva.md) — IVA (Art. 8 letra G
  modificado).
- [`codigo-tributario`](../normativa/codigos/codigo-tributario.md) —
  Art. 97 (sanciones), procedimiento.
- [`dl-824-renta`](../normativa/leyes/dl-824-renta.md) — Primera Categoría
  (cruce).
- [`perfil-tributario`](../perfiles/tributario.md) — orquestador.
- [`skill citas-verificables`](../skills/citas-verificables.md).
