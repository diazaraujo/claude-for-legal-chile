---
name: diagnostico
description: >
  Diagnóstico estructurado de un escrito jurídico chileno ANTES de modificarlo o
  usarlo de base. Identifica problemas (fundamentos débiles, citas no verificadas,
  plazos, nulidades, faltantes) sin modificar el texto. Usar cuando el usuario
  pega un escrito y pide mejorarlo/revisarlo, o ante cualquier pieza >300 palabras
  sin instrucción clara. Corre primero; la modificación es una segunda etapa.
argument-hint: "[pegar el escrito a diagnosticar]"
---

# /diagnostico

## Cuándo corre
El usuario aporta un escrito (demanda, recurso, contrato, dictamen, minuta). El
diagnóstico NO modifica: solo identifica. La modificación ocurre después, con
instrucción explícita de proceder.

## Qué hacer
1. **Clasificar** el escrito y su materia (determina normativa y plazos aplicables).
2. **Diagnosticar por capas**:
   - **Citas**: toda cita legal/jurisprudencial → pasar por [[verificar-cita]].
     Marcar las no verificables.
   - **Fundamentos**: solidez jurídica; afirmaciones sin respaldo normativo.
   - **Plazos**: vencimientos y cómputo ([[plazos]]); riesgo de extemporaneidad.
   - **Forma**: requisitos procesales/estructura según el tipo de escrito.
   - **Faltantes**: peticiones, antecedentes o elementos de la esencia ausentes.
   - **Riesgos**: nulidades, indefensión, contradicciones.
3. **Entregar** el diagnóstico estructurado por capas con severidad (alta/media/baja).
   NO reescribir aún. Preguntar si se procede a la modificación.

## Reglas
- No inventar citas ni rellenar fundamentos: si falta respaldo, marcarlo.
- Output = borrador para abogado habilitado.
- Español chileno, tono consultora. Plazos: días hábiles vs corridos explícito
  (sábado no hábil para tribunales, Art. 66 CPC).
