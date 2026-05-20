---
archivo_revisado: codigo-tributario
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#14"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Código Tributario (DL 830 / 1974)

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil cubre estructura, conceptos, fiscalización + procedimiento.
Hallazgos:

- **3 críticos** para tributarista.
- **1 técnico**.
- **5 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — Cuerpo normativo: DL 830 + Ley 21.713 reforma estructural

El perfil declara:
> cuerpo_normativo: DL 830 de 1974
> ultima_modificacion: actualización continua (...; reforma estructural
> Ley 21.713 de 2024)

**Observación**: La Ley 21.713 (2024) **modifica estructuralmente** el
CT en NGA, sanciones, plataformas digitales. **Verificar** que el
perfil refleje:
- NGA reforzada (Arts. 4 bis y ss.) en el detalle.
- Plazos de respuesta a citación (Art. 63) post-reforma.
- Régimen sancionatorio modernizado.

**Acción sugerida**:
- Tabla de cambios estructurales pre-21.713 vs post.
- Vinculación operativa con `ley-21713-reforma-tributaria-2024.md`.

### H2 — Estructura: solo 3 Libros mencionados

El perfil declara estructura en 3 Libros. **Verificar** si tras 21.713
hay disposiciones nuevas en libros separados o en un libro IV
adicional.

**Acción sugerida**:
- Confirmar estructura actual.
- Documentar artículos nuevos (Arts. 4 bis-quáter NGA, etc.).

### H3 — Procedimientos jurisdiccionales: TTA + CA + CS

El perfil declara:
> procedimientos jurisdiccionales (ante los Tribunales Tributarios y
> Aduaneros — TTA — y vía Corte de Apelaciones / Corte Suprema).

**Observación**: Bien identificada la jurisdicción. **Verificar**:
- Plazos exactos post-reforma (90 días reclamación al TTA — Art. 124).
- Procedimientos especiales (general, sumario, infraccionario,
  sancionatorio).
- RAV (Reposición Administrativa Voluntaria) — Art. 123 bis.

**Acción sugerida**:
- Tabla de procedimientos + plazos por tipo de impuesto / sanción.
- Distinguir vía administrativa (RAV) vs judicial (TTA).

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿La presunción de validez del acto tributario** (Art. 24) tiene
   matices jurisprudenciales tras 21.713?

2. **¿La doctrina de "secreto tributario"** (Art. 35) se mantiene o se
   ha flexibilizado con cruces con UAF, FNE, etc.?

3. **¿La prescripción del Art. 200** tiene excepciones recientes
   (operaciones internacionales, BEPS, fideicomisos)?

4. **¿La cobranza coactiva tributaria** sigue siendo competencia de
   Tesorería con embargos administrativos, o se ha judicializado?

5. **¿El procedimiento de gestión de cobro** ante TTA tiene plazos
   prescriptivos específicos?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=6374 | ⚠️ BCN no respondió |
| DL 830 (1974) | ⚠️ no verificada |
| Estructura 3 Libros | ⚠️ no verificada (ver H2) |

## Sugerencias estructurales

- **Tabla de procedimientos tributarios** con plazos + recursos.
- **Diagrama** vía administrativa vs judicial.
- **Ejemplo** de RAV exitosa (caso real anonimizado).

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #14 (códigos base).
- **Respuesta del validador**: pendiente.
