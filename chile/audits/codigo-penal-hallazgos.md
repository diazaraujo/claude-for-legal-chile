---
archivo_revisado: codigo-penal
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#14"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Código Penal

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil cubre estructura básica + reforma Ley 21.595. Hallazgos:

- **2 críticos** para penalista.
- **1 técnico**.
- **5 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — "Modelo del Código Penal español de 1848"

El perfil declara:
> El Código Penal chileno data de 1874 (modelo del Código Penal español
> de 1848).

**Observación**: Es **dato histórico correcto**, pero hoy el CP chileno
es muy distinto por las múltiples reformas. La mención del "modelo
español" es de interés académico — verificar si tiene relevancia
operativa o si confunde al usuario.

**Acción sugerida**:
- Mantener como contexto histórico si es útil.
- O moverlo a "antecedentes" + enfocar el cuerpo en CP vigente.

### H2 — Reformas estructurales no enumeradas

El perfil menciona Ley 21.595 (2023) pero NO lista otras reformas
estructurales del último ciclo:

- **Ley 20.480 (2010)** — femicidio.
- **Ley 21.013 (2017)** — maltrato relevante a NNA y adulto mayor.
- **Ley 21.057 (2019)** — entrevista videograbada.
- **Ley 21.563 (2023)** — comunicación a distancia padre-hijo.
- **Ley 21.601 (2023)** — crimen organizado (asociación + organización).
- **Ley 21.663 (2024)** — ciberseguridad (modifica Ley 19.223 delitos
  informáticos).
- **Ley 21.671 (2024)** — reforma régimen de indultos.

**Acción sugerida**:
- Tabla de reformas estructurales recientes del último ciclo.
- Vinculación con perfiles capa 3 que cubren cada una.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

(Tras fix mecánico.)

## Preguntas abiertas para el validador

1. **¿La distinción crimen/simple delito/falta (Art. 3, 21)** sigue
   siendo determinante para penas y procedimientos, o se ha
   flexibilizado?

2. **¿El Art. 11 (atenuantes)** tiene jurisprudencia que amplíe el
   "comportamiento posterior" para abuso sexual / DDHH?

3. **¿El Art. 12 (agravantes)** sobre alevosía, premeditación, etc.
   se aplica también a delitos económicos post-21.595?

4. **¿La pena alternativa de prestación de servicios en beneficio de
   la comunidad** (Ley 18.216 reforma) tiene cobertura ampliada?

5. **¿La extinción por prescripción de la acción penal** (Arts. 94-95)
   se computa desde la consumación del delito o desde el conocimiento?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1984 | ⚠️ BCN no respondió |
| Estructura 3 Libros | ⚠️ no verificada |
| Reformas listadas en H2 | ⚠️ no verificadas |

## Sugerencias estructurales

- **Tabla de reformas estructurales** del último cuarto de siglo.
- **Mapa de cruces** con leyes penales especiales (drogas, RPA, lavado).

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #14 (códigos base).
- **Respuesta del validador**: pendiente.
