---
archivo_revisado: ley-21595-delitos-economicos
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#11"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.595 (Delitos Económicos + ambientales)

> Revisión técnica (consistencia, gaps), NO legal. **Hermana** de la
> [auto-revisión de la Ley 20.393](ley-20393-rppj-hallazgos.md):
> validar juntas.

## Resumen ejecutivo

El perfil es **muy completo** (categorías, penas, comiso, vigencia
escalonada, impacto en PJ). Hallazgos:

- **4 críticos** para validador.
- **2 técnicos**.
- **5 preguntas abiertas**.
- BCN no respondió.

## Hallazgos críticos — decisión del validador

### H1 — "Más de 230 figuras delictivas" vs "~250 delitos"

El perfil declara:
> Catálogo ampliado a **más de 230 figuras delictivas**.

En la auto-revisión de Ley 20.393 mencionamos "~250 delitos económicos
atribuibles" según fuentes secundarias. La cifra exacta varía.

**Acción sugerida**:
- Verificar la cifra exacta + considerar usar rango ("220-250 delitos
  según conteo").
- Idealmente: enlazar a tabla anexa con el catálogo completo
  desglosado por categoría.

### H2 — Multas: 60.000 UTM vs "doble beneficio"

El perfil declara:
> Para personas jurídicas: hasta 60.000 UTM o el doble del beneficio
> económico obtenido (el mayor).

**Observación**: Verificar si la **tabla de multas** está correctamente
escalada por categoría. Algunas fuentes secundarias mencionan también
**% de ventas anuales** como techo alternativo (similar a libre
competencia DL 211).

**Acción sugerida**:
- Confirmar las cuantías exactas + casos donde el techo es % de ventas
  en lugar de UTM.
- Documentar régimen agravado para reincidencia.

### H3 — Comiso "sin condena": condiciones

El perfil declara:
> Comiso sin condena: en algunos casos puede aplicarse aunque no haya
> sentencia condenatoria.

**Observación**: El **comiso sin condena previa** es un cambio
estructural muy potente. El régimen exacto + las salvaguardas
constitucionales (debido proceso) deberían explicitarse.

**Acción sugerida**:
- Detallar **causales específicas** del comiso sin condena.
- Especificar **órgano competente** (TR/TOP/Juzgado de Garantía).
- Vincular con **Ley 21.601** (Crimen Organizado) que también
  introduce comiso autónomo.

### H4 — Restricción de salidas alternativas en Categoría 1

El perfil declara:
> Salidas alternativas (suspensión condicional, acuerdos reparatorios)
> restringidas o prohibidas en Categoría 1.

**Observación**: "Restringidas o prohibidas" es vago. Las salidas
alternativas son herramientas centrales del CPP. Una prohibición
absoluta vs restricción condicional cambia toda la estrategia de
defensa.

**Acción sugerida**:
- Confirmar el régimen exacto para Categoría 1 (prohibición absoluta vs
  excepciones).
- Documentar para Categorías 2-4.
- Vincular con [`ley-19640-ministerio-publico`](../normativa/leyes/ley-19640-ministerio-publico.md)
  (Unidad Especializada Delitos Económicos).

## Hallazgos técnicos

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

Mismo problema sistemático. Cambiar a `relacionada_per`.

### T2 — Faltan cruces importantes

Adicionalmente a los ya listados:
- `ley-21601-crimen-organizado` — cruce con comiso autónomo + organización
  criminal.
- `ley-21663-ciberseguridad` — cruce con delitos informáticos (algunos
  en catálogo Cat 1).
- `ley-20720-concursal` — quiebra fraudulenta CP 463.
- `ley-19913-lavado-activos` — UAF.
- `ley-21643-acoso-laboral` — acoso como delito atribuible vía RPPJ.

## Preguntas abiertas para el validador

1. **¿Hay "primeros condenados"** de PJ bajo Ley 21.595 desde su entrada
   en vigencia (septiembre 2024)? ¿Casos emblemáticos?

2. **¿La "Unidad Especializada en Delitos Económicos"** del MP tiene
   instrucciones generales públicas que el sistema debería citar?

3. **¿El comiso por valor equivalente** alcanza a **bienes de terceros**
   de buena fe? ¿Cuáles son los límites constitucionales?

4. **¿La inhabilitación para administrar PJ** se aplica como pena
   accesoria automática o requiere imposición específica?

5. **¿Hay régimen específico para pymes** o aplican todas las
   restricciones del régimen general?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| Art. 1° categorías | ⚠️ no verificada |
| Art. 14 multas | ⚠️ no verificada |
| Art. 15 comiso | ⚠️ no verificada |
| CP 470 N° 11 (admón desleal modif.) | ⚠️ no verificada |
| Ley 18.045 Art. 53, 165 | ⚠️ no verificada |
| URL BCN id=1195164 | ⚠️ BCN no respondió |
| Vigencia "septiembre 2024" | ⚠️ no verificada (¿día específico?) |

## Sugerencias estructurales

- **Archivo anexo** con catálogo completo de delitos económicos por
  Categoría (matriz de riesgo para construcción de MPD).
- **Ejemplo** de cálculo de "comiso por valor equivalente" con un caso
  hipotético.
- **Tabla comparativa** régimen pre-Ley 21.595 vs post-Ley 21.595 para
  el mismo tipo de delito (ej. cohecho activo).

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #11 (junto a Ley 20.393).
- **Respuesta del validador**: pendiente.
