---
name: red-flags-contrato
description: >
  Revisa un contrato chileno y marca red flags (cláusulas riesgosas, nulidades,
  faltantes, abusivas) contrastando contra normativa vigente recuperada del
  corpus — no contra memoria del modelo. Usar cuando el usuario pega un contrato
  o pide "revisa este contrato", "qué riesgos tiene", "cláusulas abusivas",
  "qué le falta a este contrato".
argument-hint: "[pegar el contrato o indicar tipo]"
---

# /red-flags-contrato

## Cuándo corre
El usuario aporta un contrato chileno (o un tipo) para revisión de riesgos.

## Qué hacer
1. **Clasificar** el contrato (compraventa, arriendo, trabajo, prestación de
   servicios, mutuo, sociedad, consumo, etc.) → determina la normativa aplicable
   (CC, Código del Trabajo, Ley 19.496 LPC, Ley 18.046, etc.).
2. **Recuperar** la normativa vigente relevante con `corpus_search_articulos`
   (`vigentes_only=true`) y dictámenes/jurisprudencia con [[buscar-dictamen]] /
   [[buscar-jurisprudencia]] sobre las cláusulas dudosas.
3. **Marcar red flags** por categoría:
   - **Nulidad / ilegalidad**: cláusula contra norma imperativa (citar el artículo
     recuperado). Ej.: renuncia anticipada de derechos irrenunciables.
   - **Abusiva** (consumo): contrastar con Art. 16 Ley 19.496 si aplica.
   - **Faltante**: elementos de la esencia/naturaleza ausentes.
   - **Riesgo**: ambigüedad, indefensión, desequilibrio.
4. **Reportar** cada flag con: cláusula → norma/criterio recuperado (con cita
   verificada) → riesgo → sugerencia. Severidad alta/media/baja.

## Reglas
- Cada afirmación de ilegalidad/abusividad DEBE apoyarse en una cita recuperada y
  verificada ([[verificar-cita]]). Sin respaldo → marcar como "punto a revisar",
  no como nulidad afirmada.
- Output es **borrador para abogado habilitado**, no asesoría directa.
- Tuteo chileno, tono consultora; no chilenismos.
- Plazos en días hábiles vs corridos según corresponda ([[plazos]]).
