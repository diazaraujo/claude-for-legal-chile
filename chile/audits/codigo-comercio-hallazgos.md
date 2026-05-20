---
archivo_revisado: codigo-comercio
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#14"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Código de Comercio

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil reconoce el rol histórico del CCom + su erosión por leyes
especiales modernas. Hallazgos:

- **2 críticos** para comercialista.
- **1 técnico**.
- **5 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — "Libro IV (Quiebras) derogado por Ley 20.720"

El perfil declara correctamente que la Ley 20.720 (2014) reemplazó el
**Libro IV** del CCom (quiebras).

**Observación**: Verificar:
- ¿El Libro IV fue **íntegramente derogado** o solo en parte?
- ¿Algún concepto del antiguo Libro IV (preferencias, acción
  revocatoria) sigue vigente en el CCom?

**Acción sugerida**:
- Confirmar alcance de la derogación.
- Cruce con `ley-20720-concursal` para evitar contradicciones.

### H2 — Comercio marítimo: vigente pero antigüedad estructural

El perfil declara que el CCom mantiene relevancia en **comercio
marítimo**.

**Observación**: El **Libro III del CCom** sobre comercio marítimo fue
**modernizado por la Ley 18.680 (1988)** que incorporó normas
internacionales (Bruselas, La Haya-Visby).

**Acción sugerida**:
- Mencionar Ley 18.680 como reforma estructural del comercio marítimo.
- Identificar tratados internacionales aplicables (Convenios de
  Bruselas, La Haya-Visby, Hamburgo, Rotterdam).

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix.)

## Preguntas abiertas para el validador

1. **¿La definición de "actos de comercio" (Art. 3)** sigue siendo
   relevante operativamente, o ha sido superada por el principio de
   "comerciante" funcional?

2. **¿La cuenta corriente mercantil** (Arts. 602+) sigue siendo
   utilizada en práctica, o ha sido desplazada por cuenta corriente
   bancaria (DFL 707)?

3. **¿El contrato de transporte por carretera (Arts. 166+)** se
   aplica supletoriamente con la Ley 18.290 (transporte) y normas
   sectoriales?

4. **¿La comisión mercantil (Arts. 235+)** tiene jurisprudencia
   reciente sobre su distinción del mandato civil?

5. **¿Existe régimen específico para comercio electrónico** dentro
   del CCom, o todo se rige por Ley 19.799 + 19.496 + leyes
   especiales?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1974 | ⚠️ BCN no respondió |
| Ley 1865-11-23 | ⚠️ no verificada |
| Estructura libros | ⚠️ no verificada |
| Ley 20.720 derogación Libro IV | ⚠️ confirmar alcance |
| Ley 18.680 modernización marítimo | ⚠️ ver H2 |

## Sugerencias estructurales

- **Tabla de "qué sigue vigente"** vs "qué fue desplazado por ley
  especial" en cada Libro del CCom.
- **Mapa de cruces** CCom + leyes especiales (18.045, 18.046, 20.720,
  18.092, 18.010, 19.913, etc.).

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #14 (códigos base).
- **Respuesta del validador**: pendiente.
