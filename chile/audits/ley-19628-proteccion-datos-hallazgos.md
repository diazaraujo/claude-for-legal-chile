---
archivo_revisado: ley-19628-proteccion-datos
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#9"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 19.628 (LPDP original)

> Revisión técnica (consistencia, gaps), NO legal. Validar junto a
> Ley 21.719 (auto-revisión ya generada).

## Resumen ejecutivo

Es la LPDP original vigente hasta 2026-12-01. Hallazgos:

- **2 críticos**.
- **1 técnico**.
- **3 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — "Hasta la entrada en vigencia plena": régimen transitorio

El perfil declara correctamente la convivencia con 21.719:
> Hasta la entrada en vigencia plena de la Ley 21.719 (vigente desde
> el 1 de diciembre de 2026), la 19.628 rige con sus modificaciones
> acumuladas previas.

**Observación**: Esto está bien planteado. Pero falta detallar **qué
disposiciones de la 21.719 entran en vigor antes del 2026-12-01** (si
es que las hay) y cuáles esperan.

**Acción sugerida**:
- Confirmar si hay disposiciones de la 21.719 con vigencia inmediata o
  todo se difiere al 2026-12-01.
- Documentar régimen transitorio explícito.

### H2 — ARCO básicos vs ARCO ampliado

El perfil declara que la 19.628 establece **ARCO** (acceso,
rectificación, cancelación, oposición).

**Observación**: La 21.719 introduce derechos adicionales
(portabilidad, decisiones automatizadas, intervención humana,
bloqueo). El perfil de 19.628 debe declarar **qué derechos NO existen
todavía** (operativos solo desde 2026-12-01).

**Acción sugerida**:
- Tabla comparativa: derechos en 19.628 vs 21.719.
- Marcar inequívocamente qué se puede invocar HOY (2026-05-19) vs
  desde 2026-12-01.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix mecánico del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿Qué bancos de datos siguen requiriendo registro** ante el
   Servicio de Registro Civil bajo el régimen actual (19.628)?

2. **¿El régimen de datos económicos** del Título IV
   (DICOM/Equifax/EDIBOX) tiene modificaciones recientes que afecten
   la asesoría a empresas?

3. **¿La acción de habeas data** ante el Juzgado de Letras Civil
   sigue siendo la vía principal hasta que APDP entre en operación?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=141599 | ⚠️ BCN no respondió |
| Estructura Títulos I-V | ⚠️ no verificada |

## Sugerencias estructurales

- **Banner visual** en el archivo: "Régimen vigente hasta 2026-12-01"
  para evitar que el sistema cite normas como si fueran post-21.719.
- **Tabla comparativa** consolidada con la 21.719.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #9 (junto a 21.719).
- **Respuesta del validador**: pendiente.
