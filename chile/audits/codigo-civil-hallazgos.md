---
archivo_revisado: codigo-civil
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#14"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Código Civil

> Revisión técnica (consistencia, gaps), NO legal. Base universal del
> derecho privado chileno.

## Resumen ejecutivo

El perfil cubre estructura, conceptos clave, artículos centrales.
Hallazgos:

- **3 críticos** para validador civilista.
- **1 técnico**.
- **6 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — URL BCN: id=172986 (ambigüedad de DFL refundidor)

El perfil declara:
> fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma=172986

**Observación**: El id=172986 **se comparte** entre Código Civil + Ley
14.908 (Alimentos) + Ley 19.620 (Adopciones) porque corresponde al
**DFL Nº 1 del Ministerio de Justicia (2000)** que fija el texto
refundido, coordinado y sistematizado del Código Civil y otras leyes
de familia.

Esto es **técnicamente correcto** pero **operativamente ambiguo**: un
usuario que entra al URL verá contenido refundido de múltiples leyes.

**Acción sugerida**:
- Documentar en el perfil que la URL apunta al DFL refundidor.
- Si BCN tiene anchor específico para el CC dentro del DFL, usarlo.
- Considerar agregar campo `dfl_refundidor: DFL Nº 1 / 2000 Justicia`
  al frontmatter.
- Esta ambigüedad afecta también a Ley 14.908 y Ley 19.620 — revisar
  consistencia entre los 3 perfiles.

### Hallazgo análogo: id=1118991

Buscando duplicados detecté que el id=1118991 está compartido entre
`ley-21091-educacion-superior.md` y `ley-21094-universidades-estatales.md`.

**Acción sugerida**:
- Verificar si ambas leyes están en un DFL refundidor o si una de las
  URLs es error.
- Si es DFL refundidor: documentar.
- Si es error: corregir.

### H2 — Reformas estructurales recientes no destacadas

El perfil cubre el CC histórico (1855) + actualización continua. Pero
no destaca:
- **Ley 21.400 (2021)** que reformó régimen patrimonial matrimonio para
  matrimonio igualitario.
- **Reforma filiación (2015)** Ley 20.830 + posteriores.
- **Reforma adopción (2014)**.

**Acción sugerida**:
- Tabla de reformas estructurales recientes con impacto en el CC.
- Vinculación con perfiles capa 3 que cubren cada reforma.

### H3 — Norma supletoria: alcance exacto

El perfil declara:
> Es **norma supletoria** del derecho privado: lo no regulado por
> leyes especiales (laboral, comercial, consumidor, etc.) se rige
> por el CC.

**Observación**: La supletoriedad del CC es la regla, pero el orden de
aplicación es más complejo:
1. Ley especial específica.
2. Ley general del sector (ej. Código Comercio si es comercial).
3. CC como supletorio último.

Hay materias donde el CC no aplica supletoriamente (ej. concursal post
Ley 20.720 tiene régimen propio integral).

**Acción sugerida**:
- Detallar jerarquía de aplicación.
- Documentar materias donde el CC NO opera supletoriamente.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix mecánico del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿El Título Preliminar (Arts. 1-53)** sigue vigente sin
   modificaciones estructurales? ¿O la interpretación legal (Arts. 19-24)
   tiene reformas relevantes?

2. **¿La regla del Art. 1462 sobre nulidad por objeto ilícito** tiene
   jurisprudencia consolidada sobre alcance?

3. **¿La regla del Art. 1546 sobre buena fe contractual** se interpreta
   con estándar objetivo, subjetivo o mixto?

4. **¿La interpretación de Art. 1564 sobre cláusulas oscuras** sigue
   siendo "en sentido más favorable al deudor"?

5. **¿La acción reivindicatoria** (Arts. 889+) tiene jurisprudencia
   reciente sobre títulos perfectos vs imperfectos?

6. **¿La prescripción adquisitiva** (Arts. 2492+) tiene cómputos
   especiales para inmuebles fiscales?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=172986 | ⚠️ ambigua (DFL refundidor compartido — ver H1) |
| Estructura Libros I-IV | ⚠️ no verificada |
| Arts. 55, 545, etc. | ⚠️ no verificadas |

## Sugerencias estructurales

- **CORREGIR URL** crítico.
- **Tabla de reformas estructurales** del CC (1855-presente) con link
  a perfiles capa 3 que cubren cada una.
- **Mapa de aplicación**: cuándo CC aplica directamente vs
  supletoriamente vs no aplica.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #14 (códigos base).
- **Respuesta del validador**: pendiente.
