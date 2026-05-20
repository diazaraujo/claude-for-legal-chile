---
archivo_revisado: ley-19880-procedimiento-administrativo
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#15"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 19.880 (Procedimiento administrativo)

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil cubre los conceptos fundamentales (acto, plazos, recursos,
silencio, principios). Hallazgos:

- **2 críticos**.
- **1 técnico**.
- **5 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — Recurso de revisión: "1 año desde firmeza"

El perfil declara:
> | Recurso de revisión | 1 año desde firmeza del acto |

**Observación**: El recurso extraordinario de revisión (Art. 60) tiene
**causales tasadas** muy estrictas (vicios formales graves, hechos
nuevos, etc.) y un plazo que probablemente sea desde el conocimiento
del nuevo hecho, no desde la firmeza. **Verificar**.

**Acción sugerida**:
- Confirmar plazo exacto del Art. 60.
- Documentar las causales tasadas.

### H2 — Silencio positivo: ámbito de aplicación

El perfil declara:
> Aplicable a:
> - Procedimientos sin trámites complementarios.
> - Cuando la ley específica no diga lo contrario.

**Observación**: El silencio positivo es **regla general en Chile**
(Art. 64) pero tiene excepciones importantes. **Verificar**:
- ¿Aplica a TODO procedimiento iniciado a petición de parte?
- ¿Excluyente para actos administrativos sujetos a control de
  legalidad (toma de razón CGR)?
- ¿Cómo se acredita el silencio (cargo del beneficiario)?

**Acción sugerida**:
- Detallar ámbito de aplicación del silencio positivo + procedimiento
  para invocarlo.
- Cruce con dictámenes CGR sobre silencio.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix mecánico del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿La invalidación de oficio (Art. 53)** tiene plazo límite?
   ¿Genera obligación de indemnizar al titular?

2. **¿Las notificaciones electrónicas** (vía ClaveÚnica + Ley 21.180)
   sustituyen a la notificación por carta certificada o son
   complementarias?

3. **¿La suspensión del plazo del silencio (Art. 66)** es automática o
   debe ser fundamentada?

4. **¿La impugnación administrativa agota la vía**, o el interesado
   puede acudir directamente a tribunal sin recurso administrativo?

5. **¿Hay régimen específico de notificación a personas jurídicas**
   distinto al de personas naturales?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=210676 | ⚠️ BCN no respondió |
| Art. 3, 4, 24, 25, 45, 53, 59, 60, 64, 65 | ⚠️ no verificadas |

## Sugerencias estructurales

- **Diagrama de flujo** del procedimiento administrativo tipo.
- **Tabla** de plazos por tipo de procedimiento.
- **Ejemplo** de cómputo de plazo en días hábiles (excluyendo sábados +
  feriados + judiciales).

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #15.
- **Respuesta del validador**: pendiente.
