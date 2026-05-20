---
archivo_revisado: ley-14908-alimentos
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#13"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 14.908 (Alimentos + RNDPA + GAM)

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil es muy operativo (apremios, RNDPA, GAM). Hallazgos:

- **4 críticos** para validador de familia.
- **1 técnico**.
- **6 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — Pensión mínima: 40% del ingreso mínimo por hijo

El perfil declara:
> Pensión mínima: 40% del ingreso mínimo remuneracional por hijo (Art. 3).

**Observación**: El **40% por hijo** parece elevado. La regla típica es
**30% del IMR por hijo**, con piso del 40% del IMR para múltiples hijos
o circunstancias específicas. Verificar contra texto vigente.

**Acción sugerida**:
- Confirmar % exacto en Art. 3 Ley 14.908 vigente.
- Distinguir piso por hijo individual vs piso total familiar.

### H2 — Arraigo nacional como apremio

El perfil lista:
> - **Arraigo nacional**.
> - **Suspensión de licencia de conducir**.
> - **Suspensión de pasaporte**.
> - **Arresto nocturno** hasta 15 días renovables.

**Observación**: El **arresto nocturno** chileno funciona como **prisión
desde 22:00 a 06:00**. **Verificar plazo máximo** (15 días + renovable
indefinida vs cap absoluto + condiciones).

**Acción sugerida**:
- Confirmar plazos exactos + condiciones de renovación.
- Documentar la orden de gravedad efectiva en la práctica de TF.

### H3 — Conviviente civil (AUC) tiene derecho a alimentos

El perfil declara:
> | Conviviente civil (AUC) | Sí |

**Observación**: Esto es relevante. La Ley 20.830 reformada por
21.400 establece el régimen de AUC. Confirmar:
- ¿Aplica durante el AUC vigente, o también al terminar el AUC
  (compensación económica)?
- ¿Equiparable al cónyuge en obligación alimenticia?

**Acción sugerida**:
- Detallar régimen alimenticio del conviviente civil vs cónyuge.
- Documentar consecuencias al término del AUC.

### H4 — Restricciones del RNDPA: "comprar propiedades"

El perfil declara:
> No pueden comprar propiedades sin acreditar pago previo.

**Observación**: Esta restricción es **importante operativamente** y
afecta operaciones inmobiliarias. **Verificar**:
- ¿Aplica a TODA compraventa de inmueble o solo a las financiadas?
- ¿Aplica si paga al contado o solo cuando media crédito hipotecario?
- ¿Notarios + CBR tienen obligación de verificar?

**Acción sugerida**:
- Detallar alcance exacto.
- Cruce con `ley-21484-compraventa-inmuebles` y obligaciones del
  Conservador.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿La Ley 21.484** (compraventa inmuebles con financiamiento) tiene
   cláusula específica sobre vendedor con deuda RNDPA?

2. **¿La acción de cesación / aumento de alimentos** prescribe? ¿Plazos?

3. **¿La pensión alimenticia post-divorcio entre cónyuges** (Art.
   19 bis ss.) requiere acreditar dependencia económica o se concede
   por mero parentesco?

4. **¿Convenios internacionales** sobre cobro de alimentos en el
   extranjero: convenio La Haya 2007 ratificado? ¿Convenios
   bilaterales operativos?

5. **¿GAM**: el empleador que no cumple es solidariamente responsable
   o tiene multa específica?

6. **¿Hay régimen específico para alimentos a estudios universitarios**
   (Art. 332 CC menciona "hasta los 28 años si estudia profesión")?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=172986 | ⚠️ BCN no respondió |
| CC Arts. 321-337 | ⚠️ no verificadas contra texto |
| Art. 3 Ley 14.908 (40%) | ⚠️ ver H1 |
| Ley 21.389 (RNDPA 2021) | ⚠️ asumida |
| Ley 21.515 (GAM 2023) | ⚠️ asumida |
| Ley 21.484 (cruce inmueble) | ⚠️ asumida |

## Sugerencias estructurales

- **Tabla de plazos de apremios** con orden secuencial.
- **Tabla de % de IMR** para distintos números de hijos.
- **Ejemplo** de cálculo de pensión con padre dependiente + casado +
  2 hijos.
- **Procedimiento de salida del RNDPA**: pasos + tiempos.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #13.
- **Respuesta del validador**: pendiente.
