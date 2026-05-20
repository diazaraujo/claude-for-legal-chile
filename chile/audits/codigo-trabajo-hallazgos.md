---
archivo_revisado: codigo-trabajo
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#12"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Código del Trabajo (DFL N° 1/2002)

> Revisión técnica (consistencia, gaps), NO legal. El validador es el
> que decide sobre interpretación sustantiva.

## Resumen ejecutivo

El perfil es compacto + bien estructurado (Libros, conceptos clave,
artículos relevantes, procedimientos). Hallazgos:

- **3 críticos**.
- **2 técnicos**.
- **6 preguntas abiertas**.
- BCN no respondió.

## Hallazgos críticos — decisión del validador

### H1 — Jornada ordinaria actual: ¿42h o 44h?

El perfil declara:
> Jornada ordinaria | Tiempo durante el cual el trabajador debe
> efectivamente prestar servicios; actualmente 42h semanales en
> transición a 40h

**Observación**: Según la Ley 21.561 (cuya auto-revisión propia ya
generamos), el calendario es:
- 45h hasta 2024-04-25
- **44h desde 2024-04-26**
- 42h desde 2026-04-26
- 40h desde 2028-04-26

A fecha de hoy (2026-05-19), la jornada vigente debería ser **42h**
(ya entró en vigor el 26-abril-2026). Pero el perfil debe **declarar
explícitamente** la fecha de redacción + cuál es la jornada vigente en
ese momento, para evitar desactualización.

**Acción sugerida**:
- Confirmar fecha de transición 44h → 42h (¿efectivamente 2026-04-26?).
- Documentar la jornada vigente con **fecha de validación**.
- Considerar un sistema que actualice automáticamente esta cifra.

### H2 — Indemnización por años de servicio: tope 90 UF vs general

El perfil declara:
> Indemnización por años de servicio (IAS): 1 mes de la última
> remuneración mensual por cada año servido, con tope (Art. 163)

**Observación**: El perfil dice "con tope" pero **no especifica el
tope**. Los topes son:
- **Tope mensual**: 90 UF (sobre el promedio mensual usado en cálculo).
- **Tope años**: 11 años máximo (a no ser que la fuente legal específica
  lo amplíe).

**Acción sugerida**:
- Documentar ambos topes (UF mensual + años máx).
- Excepciones (algunos casos no tienen tope de años).

### H3 — Prescripción: "2 años derechos, 6 meses contratos extinguidos"

El perfil declara:
> 510 | Prescripción (2 años derechos, 6 meses contratos extinguidos)

**Observación**: El Art. 510 CT establece:
- Acción derivada del contrato vigente: 2 años desde que se hicieron
  exigibles.
- Acción derivada del contrato terminado: **6 meses desde la
  terminación**.

Pero hay un cruce con prescripción del **fuero del Art. 168** (60 días
hábiles para reclamo despido).

**Acción sugerida**:
- Aclarar la diferencia entre:
  - Acción por despido injustificado: 60 días hábiles (Art. 168).
  - Acción por derechos pendientes contrato terminado: 6 meses
    (Art. 510).
  - Acción por derechos contrato vigente: 2 años (Art. 510).

## Hallazgos técnicos

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

Cambiar a `relacionada_per`.

### T2 — Faltan referencias a perfiles capa 3 ya escritos

`relacionada_con` declara 9 leyes pero falta `ley-21155-fueros` (que
mencioné en perfil laboral) y otros aún no escritos pero referenciados
en el corpus.

**Acción**: revisar coherencia con `chile/normativa/leyes/00-indice.md`.

## Preguntas abiertas para el validador

1. **¿El "deber de seguridad" del Art. 184** se interpreta con estándar
   objetivo (toda diligencia necesaria) o subjetivo (medidas
   razonables)? Cruce con Ley 16.744.

2. **¿La "presunción del Art. 8"** se aplica también cuando el
   "contratante" es el Estado a través de honorarios (cruce con
   reconducción a Estatuto vs CT)?

3. **¿Las gratificaciones del Art. 47 vs 50** se pueden combinar o son
   excluyentes para una misma empresa?

4. **¿La "semana corrida" del Art. 45** aplica solo a sueldos por día o
   también a comisiones / variables?

5. **¿Hay régimen específico para trabajadores agrícolas / forestales
   temporeros** que se mantenga vigente?

6. **¿La "Ley Bustos"** (cotizaciones al día Art. 162) tiene
   modificaciones recientes que el perfil no refleja?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=207436 | ⚠️ BCN no respondió |
| DFL 1/2002 | ⚠️ no verificada |
| Art. 7, 8, 9, 22, 28, 32, 41, 47, 50, 67, 159, 160, 161, 162, 163, 168, 171, 184, 489, 510 | ⚠️ números mencionados sin verificar texto |

## Sugerencias estructurales

- **Tabla de jornada vigente** con calendario completo 21.561 (ya está
  en el perfil de 21.561 — link cruzado).
- **Tabla de causales de término** Art. 159, 160, 161 con efectos
  indemnizatorios.
- **Calculadora de IAS** como anexo: cómo calcular con tope 90 UF +
  11 años máx.
- **Ejemplo** de **tutela laboral** con cuantificación de daño moral.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #12 (laboral completo).
- **Respuesta del validador**: pendiente.
