---
archivo_revisado: ley-21561-reduccion-jornada
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#12"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.561 (Reducción jornada a 40h)

> Revisión técnica (consistencia, gaps), NO legal. Alerta de
> volatilidad: vigencia escalonada hasta 2028.

## Resumen ejecutivo

El perfil es **breve y bien estructurado** (calendario claro,
cambios al CT, impacto operativo). Hallazgos:

- **3 críticos**.
- **2 técnicos**.
- **5 preguntas abiertas**.
- BCN no respondió.

## Hallazgos críticos — decisión del validador

### H1 — Calendario de reducción: ¿44h desde 2024-04-26 o desde otra fecha?

El perfil declara:
> | Desde 2024-04-26 | **44 horas** (1 año desde publicación) |

**Observación**: Si la ley fue publicada el 2023-04-26, "1 año
después" sería 2024-04-26. **Verificar** que efectivamente 44h
empezó en esa fecha precisa (vs algún día específico distinto).

El art. transitorio probablemente especifique días exactos.

**Acción sugerida**:
- Confirmar fechas exactas vía art. transitorio.
- Reflejar si hay diferencias entre régimen general y sectores
  específicos.

### H2 — Bandas horarias: "hasta una hora" — corregir si el plazo es distinto

El perfil declara:
> Trabajadores con responsabilidades de cuidado... pueden solicitar
> adelantar o postergar **hasta una hora** la entrada con compensación
> equivalente en la salida.

**Observación**: La Ley 21.561 introduce bandas horarias para
cuidadores. **Verificar** que el rango exacto es 1 hora vs otro valor.

**Acción sugerida**:
- Confirmar rango + condiciones del beneficio.
- Verificar si aplica solo durante crianza activa (menor de 12 años) o
  extendido.

### H3 — Promedio semanal: máximo diario 10 horas

El perfil declara:
> la jornada puede calcularse como **promedio en un período de hasta 4
> semanas**, con un máximo absoluto diario de 10 horas.

**Observación**: El **máximo diario** general del CT es 10 horas
(Art. 28). Para el sistema de promedio semanal de la Ley 21.561,
**verificar** si:
- El máximo absoluto sigue siendo 10 horas, o
- La ley permite jornadas más largas algunos días siempre que se
  compense en otros.

**Acción sugerida**:
- Detallar el régimen del Art. 22 bis CT incorporado por 21.561.
- Especificar plazos para la "compensación dentro del período".

## Hallazgos técnicos

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

Cambiar a `relacionada_per`.

### T2 — Cruces faltantes

`relacionada_con` declara solo `codigo-trabajo`. Faltan:
- `ley-20940-relaciones-laborales` — negociación colectiva +
  adaptabilidad sindical.
- `ley-21220-teletrabajo` — cruce con jornada en teletrabajo.
- `ley-16744-accidentes-trabajo` — cómputo de jornada para
  contingencias.
- `ley-21643-acoso-laboral` — sobrecarga horaria como factor de
  riesgo psicosocial.

## Preguntas abiertas para el validador

1. **¿Hay reglamentos / circulares DT** sobre aplicación de la 21.561
   en sectores específicos (salud 24/7, transporte, retail con
   feriados, agroindustria temporal)?

2. **¿Los pactos colectivos pre-21.561** sobre jornada de 45h siguen
   vigentes** hasta su renegociación, o se ajustan automáticamente al
   nuevo techo?

3. **¿La compensación de horas extras con descanso** (vs pago en
   dinero) requiere acuerdo individual o puede ser unilateral del
   empleador?

4. **¿La jornada 4x3** requiere autorización DT o solo acuerdo
   contractual?

5. **¿Hay régimen específico para trabajadores con discapacidad** que
   pueda interactuar con las bandas horarias para cuidadores?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1191702 | ⚠️ BCN no respondió |
| Fecha publicación 2023-04-26 | ⚠️ asumida |
| Fechas calendario reducción | ⚠️ ver H1 |
| Art. 22, 22 bis, 28, 32, 33, 38 CT | ⚠️ no verificadas |

## Sugerencias estructurales

- **Calendario visual** (timeline) en SVG mostrando 45 → 44 → 42 → 40
  con fechas exactas.
- **Tabla del divisor para cálculo hora**: 45h → /195h; 44h → /190h;
  42h → /182h; 40h → /173h.
- **Ejemplo** específico de **liquidación con jornada 44h** vigente
  hoy.
- **Cruce con teletrabajo**: cómo se cuentan horas en teletrabajo bajo
  la 21.561.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #12 (laboral completo).
- **Respuesta del validador**: pendiente.
