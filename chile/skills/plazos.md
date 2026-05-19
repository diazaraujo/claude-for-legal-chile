# Skill — Cálculo de plazos

Skill **obligatorio**. Errar un plazo puede ser fatal para un derecho. El sistema
debe distinguir explícitamente entre **plazos de días hábiles** y **plazos de días
corridos**, considerar los días feriados aplicables y precisar el momento de
inicio del cómputo.

## Principio rector

> **Todo plazo expresado por el sistema lleva su unidad y su regla de cómputo
> explícitas.** "60 días" sin unidad es un error.

## Reglas chilenas básicas

### Días corridos vs días hábiles

- **Día corrido**: cada día calendario, incluidos sábados, domingos y feriados.
  Es la regla general en el **Código Civil** (Art. 50: "todos los plazos de días,
  meses o años de que se haga mención en las leyes o en los decretos del Presidente
  de la República, de los tribunales o juzgados, se entenderá que han de ser
  completos").
- **Día hábil**: día en que funcionan los tribunales o el organismo competente.
  Es la regla general en **procesos judiciales y administrativos**.

### Sábado, domingo y feriados en plazos procesales

- **CPC Art. 66 inc. 1°**: "Los términos de días que establece el presente Código,
  se entenderán suspendidos durante los feriados, salvo que el tribunal, por
  motivos justificados, haya dispuesto expresamente lo contrario."
- **CPC Art. 66 inc. 2°**: "Lo anterior **no regirá con los términos de días
  fijados para la práctica de actuaciones judiciales**, en cuyo caso se
  computarán los días corridos."

**Reglas operativas**:

- **Sábado NO es día hábil** para efectos procesales (modificación legal).
- **Domingos y feriados**: no hábiles.
- **31 de diciembre, viernes y lunes santos, Año Nuevo, etc.**: feriados, no hábiles.

### Feriado judicial

El **Poder Judicial** declara feriado judicial cada año (típicamente del 1 al 31 de
febrero). Durante el feriado:

- Solo funcionan tribunales en turno.
- Los plazos procesales se **suspenden** salvo en causas urgentes.
- Los plazos administrativos siguen su curso (salvo norma especial).

### Inicio del cómputo

- **Plazo desde notificación**: se cuenta **al día siguiente** de la notificación.
- **Plazo desde publicación en DO**: se cuenta desde el **día siguiente** de la
  publicación.
- **Plazo desde un hecho**: se cuenta desde el día siguiente al hecho, salvo que
  la norma indique otra cosa.

### Plazos en meses y años

- Computados de fecha a fecha: el plazo de 1 mes desde el 15 de marzo termina el
  15 de abril.
- Si el día equivalente no existe (ej. 31 → mes con 30 días), termina el último
  día del mes (CC Art. 48).
- Si vence en día feriado, **se prorroga al día hábil siguiente** (CC Art. 49,
  regla supletoria; en plazos procesales aplica también).

### Plazos fatales y plazos no fatales

- **Plazo fatal**: vencido extingue el derecho, sin posibilidad de prórroga.
- **Plazo no fatal**: el tribunal o autoridad puede declarar transcurrido el
  plazo, pero hasta que no lo declare, la actuación es válida.
- En general, los plazos del CPC son fatales para las partes (Art. 64); los
  del tribunal no lo son.

## Plazos críticos por rama

### Laboral

| Acción | Plazo | Tipo |
|---|---|---|
| Reclamar despido injustificado | 60 días hábiles desde separación | Hábiles, suspendido por reclamo DT (máx +30) |
| Tutela laboral | 60 días hábiles desde la afectación | Hábiles |
| Demanda monitoria | Variable; en general 60 días hábiles | Hábiles |
| Comunicación de despido (Art. 162) | 30 días previos o sustitutiva en finiquito | Corridos |
| Reclamación de multa DT | 15 días hábiles desde notificación | Hábiles |
| Prescripción derechos laborales | 2 años desde exigibilidad | Corridos (CC Art. 50) |
| Prescripción acciones contratos extinguidos | 6 meses | Corridos |

### Privacidad (Ley 19.628 + 21.719)

| Acción | Plazo | Tipo |
|---|---|---|
| Respuesta a solicitud de acceso ARCOP+ | Por definir en reglamento APDP (típicamente 15-30 días) | Por definir |
| Notificación de brecha a APDP | Típicamente 72 horas desde conocimiento | Corridos |
| Reclamación a APDP por denegación | Por definir | Por definir |

### Consumidor (Ley 19.496)

| Acción | Plazo | Tipo |
|---|---|---|
| Derecho a retracto en e-commerce | 10 días desde recepción | Corridos |
| Garantía legal en productos durables | 6 meses desde entrega | Corridos |
| Garantía legal en productos no durables | 3 meses desde entrega | Corridos |
| Procedimiento sumarísimo LPC | Plazos breves del CPC para JPL | Hábiles |

### Constitucional

| Acción | Plazo | Tipo |
|---|---|---|
| Recurso de protección (Art. 20 CPR) | 30 días corridos desde el acto u omisión | Corridos |
| Recurso de amparo (Art. 21 CPR) | Sin plazo (mientras subsista la afectación) | — |
| Inaplicabilidad por inconstitucionalidad | Mientras esté pendiente el juicio | — |

### Procesal civil (CPC)

| Acción | Plazo | Tipo |
|---|---|---|
| Contestar demanda en juicio ordinario | 15 días hábiles desde notificación | Hábiles, sábado no hábil |
| Recurso de apelación | 5 días hábiles desde notificación de la sentencia | Hábiles |
| Recurso de casación en el fondo | 15 días hábiles | Hábiles |

### Acoso laboral (Ley 21.643 — Ley Karin)

| Acción | Plazo | Tipo |
|---|---|---|
| Iniciar investigación interna | 3 días hábiles desde la denuncia | Hábiles |
| Comunicar a la DT | Conforme texto vigente | _verificar reglamento_ |

## Procedimiento de cálculo del sistema

### Paso 1 — Identificar el tipo de plazo

- ¿Procesal (CPC, CPP) o sustantivo (CC, leyes especiales)?
- ¿Hábil o corrido?
- ¿Fatal o no fatal?

### Paso 2 — Establecer el momento de inicio

- ¿Desde notificación? — al día siguiente.
- ¿Desde publicación en DO? — al día siguiente.
- ¿Desde el hecho (ej. accidente)? — al día siguiente, salvo norma especial.

### Paso 3 — Aplicar exclusiones

- En plazos hábiles: excluir sábados, domingos, feriados nacionales y feriado
  judicial cuando aplique.
- En plazos corridos: contar todos los días.

### Paso 4 — Determinar fecha de vencimiento

- Calcular según los días.
- Si vence en día no hábil y aplica la regla de prórroga, mover al día hábil
  siguiente.

### Paso 5 — Verificar plazos críticos

Si el plazo es bloqueante (despido injustificado, tutela, recurso de protección,
recurso de casación), advertir explícitamente:

```
⚠ PLAZO CRÍTICO: el cómputo termina el <fecha>. Si no se presenta la acción
antes de esa fecha, se extingue el derecho.
```

## Feriados nacionales chilenos (referencia)

Plazos hábiles excluyen estos feriados (consultar oficial cada año):

- 1 de enero (Año Nuevo)
- Viernes Santo y Sábado Santo
- 1 de mayo (Día del Trabajo)
- 21 de mayo (Glorias Navales)
- 29 de junio (San Pedro y San Pablo) — móvil
- 16 de julio (Virgen del Carmen)
- 15 de agosto (Asunción de la Virgen)
- 18 y 19 de septiembre (Fiestas Patrias)
- 12 de octubre (Encuentro de Dos Mundos) — móvil
- 31 de octubre (Día de las Iglesias Evangélicas)
- 1 de noviembre (Día de Todos los Santos)
- 8 de diciembre (Inmaculada Concepción)
- 25 de diciembre (Navidad)

Más feriados regionales y plebiscitos según corresponda.

## Disclaimer

El sistema no es calendario perpetuo: cuando el plazo depende de feriados de un año
específico, advertir al abogado que **verifique el calendario oficial** del año
correspondiente.
