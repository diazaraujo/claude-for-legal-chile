---
archivo_revisado: ley-18010-operaciones-credito-dinero
fecha_revision: 2026-05-20
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#21"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 18.010 (OCD)

## Hallazgos críticos

### H1 — TMC (Tasa Máxima Convencional)

El perfil declara TMC = tasa corriente + porcentaje variable. **Verificar**:
- ¿Cálculo exacto: 1,5x (corto plazo / chicas) y 50% (grandes / largo
  plazo)?
- ¿Cómo se segmenta exactamente (monto + plazo + reajustable / no)?
- Cifras post-Ley 21.398 (2021) si hubo cambios.

### H2 — Mora automática vs requerimiento

El perfil declara mora automática para OCD (sin requerimiento). **Verificar**
si esta regla se mantiene en su forma original, o si hay excepciones
para consumidor (Ley 19.496 modificada).

### H3 — Anatocismo en operaciones bancarias

El perfil declara que anatocismo permitido en bancos con autorización CMF.
**Verificar**:
- Frecuencia de capitalización (mensual estándar).
- ¿Aplica a tarjetas de crédito o tiene régimen distinto?

## Hallazgos técnicos

T1: Frontmatter usa `relacionada_per` ✅.
T2: Cruces a complementar: `ley-21000-cmf` (TMC + circulares),
`ley-21234-fraude-tarjetas`, `ley-21521-fintec`.

## Preguntas abiertas

1. ¿La **TMC para fintech** (Ley 21.521) tiene segmentos propios o
   aplica la TMC general?
2. ¿La **acción de usura penal** (Art. 472 CP) se ejerce de oficio por
   MP o solo a querella?
3. ¿La **devolución por exceso de TMC** opera de pleno derecho o
   requiere acción judicial?
4. ¿Hay régimen específico para **microcrédito** (organismos no
   bancarios)?

## Referencias

| Cita | Verificada |
|---|---|
| URL BCN id=29438 | ⚠️ BCN no respondió |
| Ley 21.398 (2021) | ⚠️ asumida |

## Estado: pendiente-de-validador.
