---
name: plazos
description: >
  Calcula y explica plazos en derecho chileno distinguiendo días hábiles vs
  corridos, feriados nacionales y judiciales, y la regla del sábado no hábil para
  tribunales (Art. 66 CPC). Usar cuando el usuario pregunta "hasta cuándo tengo
  para X", "cuándo vence el plazo de Y", o cuando un análisis depende de un cómputo
  de plazo.
argument-hint: "[plazo/actuación y fecha de inicio]"
---

# /plazos

## Cuándo corre
Cualquier cálculo o advertencia de plazo procesal o sustantivo chileno.

## Qué hacer
1. **Identificar** la actuación y su norma de plazo (recuperar el artículo vigente
   del corpus vía [[verificar-cita]] — no asumir el número).
2. **Determinar el tipo de día**:
   - **Días hábiles** = regla general procesal. En materia judicial, el **sábado
     NO es hábil** para tribunales (Art. 66 CPC), además de domingos y feriados.
   - **Días corridos** = regla excepcional (cuando la ley lo dice expresamente);
     incluye sábados, domingos y feriados.
3. **Considerar feriados** nacionales y judiciales (feriado judicial de febrero
   cuando aplique al cómputo).
4. **Calcular** el vencimiento y declarar el supuesto (hábil/corrido) usado.
   Si hay duda sobre el tipo de día, mostrarlo y advertir.

## Reglas
- Explicitar SIEMPRE si el plazo es hábil o corrido; no asumir.
- Reportar fechas en horario de Chile.
- Si el plazo es fatal/improrrogable, advertirlo.
- Output = borrador para abogado habilitado; el cómputo final debe confirmarse.
