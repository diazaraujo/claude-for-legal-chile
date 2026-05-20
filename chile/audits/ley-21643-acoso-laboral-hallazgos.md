---
archivo_revisado: ley-21643-acoso-laboral
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#8"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.643 (Ley Karin)

> **Nota**: esta revisión es técnica (consistencia, formato, gaps),
> NO legal. Las decisiones sustantivas quedan en el validador habilitado.

## Resumen ejecutivo

El perfil cubre los conceptos centrales (definiciones, plazo de 3 días
hábiles, protocolo, sanciones), pero hay:

- **5 hallazgos críticos** que requieren decisión del validador.
- **3 hallazgos técnicos** ya identificados (consistencia, formato).
- **6 preguntas abiertas** para zonas grises.
- **BCN no respondió** durante la revisión técnica — las citas no
  fueron contrastadas con texto oficial.

## Hallazgos críticos — decisión del validador

### H1 — Fecha de entrada en vigencia vs fecha de publicación

El frontmatter declara:
```yaml
publicacion: 2024-01-15
ultima_modificacion: 2024-01-15
vigencia: vigente
```

**Observación**: La Ley 21.643 fue **publicada en DO el 5 de enero de
2024**, no el 15. Pero su **entrada en vigencia es el 1° de agosto de
2024** (transcurridos 6 meses desde publicación, según art. transitorio).

**Acción sugerida al validador**:
- Confirmar fecha de publicación DO (creo es 2024-01-05, no 2024-01-15).
- Considerar agregar campo `vigencia_desde: 2024-08-01` al frontmatter
  para distinguir publicación de vigencia efectiva.

### H2 — Plazo de investigación: "30 días razonables" vs plazo legal

El perfil declara:
> | Investigación | Plazo razonable, en general 30 días | Investigador designado |

**Observación**: El plazo NO es "razonable, en general 30 días". La
ley establece un plazo específico (creo es **30 días desde inicio de la
investigación**) y la DT ha publicado dictámenes operativos.

**Acción sugerida al validador**:
- Confirmar plazo de cierre de investigación según texto de la ley +
  dictámenes DT.
- Corregir la tabla para que indique plazo fijo, no "razonable".

### H3 — Comunicación a la DT: plazo no especificado

El perfil declara:
> | Comunicación a DT | Conforme texto vigente | Empleador |

**Observación**: "Conforme texto vigente" es vago. La ley establece un
plazo específico para comunicación a la DT (creo es **dentro de 5 días
hábiles** desde la conclusión de la investigación).

**Acción sugerida al validador**:
- Confirmar plazo específico + a quién va el reporte (DT central /
  IT regional).
- Confirmar si el reporte va siempre o solo en casos calificados.

### H4 — Ausencia de mención a Ley 21.595 (Delitos Económicos)

El perfil no menciona que el acoso laboral, bajo ciertas configuraciones,
puede activar **RPPJ** vía **Ley 20.393** modificada por **Ley 21.595
(Delitos Económicos, 2023)** que **amplió el catálogo de delitos
atribuibles**.

**Acción sugerida al validador**:
- Confirmar si el acoso laboral está en el catálogo expandido de la
  Ley 21.595 como delito atribuible a la persona jurídica.
- Si sí, agregar sección "Cruce con RPPJ + MPD" + link al perfil
  societario.

### H5 — Ausencia de mención a Ley 20.005 como antecedente

La Ley 20.005 (2005) introdujo el acoso sexual al CT. La Ley Karin la
**deroga + amplía**.

**Acción sugerida al validador**:
- Agregar nota breve sobre el régimen previo (Ley 20.005) y qué cambia
  con Karin.
- Útil para asesoría a casos previos a 2024-08-01 (fecha de vigencia).

## Hallazgos técnicos (no requieren abogado)

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

El frontmatter usa:
```yaml
relacionada_con:
  - codigo-trabajo
  - ley-16744-accidentes-trabajo
```

Pero `chile/MARCADORES.md` establece como canónico **`relacionada_per`**
(perfiles relacionados).

**Acción**: cambiar a `relacionada_per` para consistencia con el
glosario.

### T2 — Reglamento posterior no referenciado

El perfil dice:
> Reglamentos de la Dirección del Trabajo sobre el procedimiento

Pero no nombra ni linka al reglamento específico. La DT publicó
**reglamentos** + **circulares** + **dictámenes** post-promulgación.

**Acción**: investigar los reglamentos publicados por DT desde 2024-08
y agregarlos como links. Si el validador conoce el reglamento operativo
específico, mencionarlo.

### T3 — Sección "Cuándo invocar esta norma" incompleta

Lista 4 casos. Faltan al menos 2 frecuentes:
- Asesoría a víctima sobre denuncia directa a DT (vía alternativa a
  interna).
- Asesoría a empresa sobre defensa frente a demanda de despido
  indirecto (Art. 171 CT) por acoso.

**Acción**: ampliar lista.

## Preguntas abiertas para el validador

1. **¿La perspectiva de género en la investigación es obligatoria con
   estándar específico**, o queda como principio orientador? ¿Hay
   protocolo MTPS?

2. **¿La licencia preventiva durante la investigación** tiene plazo
   máximo? ¿Se paga normal o con régimen especial?

3. **¿El despido por acoso confirmado activa automáticamente el
   Art. 160 N° 1**, o el empleador puede usar 160 N° 7 (incumplimiento
   grave) según el caso? ¿Cuál es más sólido procesalmente?

4. **¿La empresa con MPD certificado** queda eximida o atenuada de la
   RPPJ por acoso laboral? ¿Hay caso jurisprudencial al respecto?

5. **¿La violencia ejercida por terceros (clientes, proveedores)** que
   afecte al trabajador genera obligaciones del empleador con el mismo
   alcance que el acoso interno?

6. **¿Hay régimen específico para acoso laboral en sector público**
   (Estatuto Administrativo / Municipal) o aplica el régimen general
   del CT vía remisión?

## Referencias verificadas / no verificadas

### Citas mencionadas en el perfil

| Cita | Verificada |
|---|---|
| Art. 160 N° 1 CT (causales despido) | ⚠️ no verificada contra texto |
| Art. 171 CT (despido indirecto) | ⚠️ no verificada contra texto |
| Art. 485-495 CT (tutela laboral) | ⚠️ no verificada contra texto |
| Ley 16.744 (Mutuales) | ⚠️ no verificada contra texto |
| URL BCN id=1199895 | ⚠️ BCN no respondió al momento de revisión |

**Nota técnica**: el endpoint BCN devolvió "Error" durante esta
revisión (2026-05-19). El validador debe consultar texto oficial
directamente en https://www.bcn.cl/leychile/navegar?idNorma=1199895.

## Sugerencias estructurales (opcional para validador)

- **Agregar tabla** de comparación pre-Karin vs post-Karin para
  abogados que tienen casos arrastrados.
- **Agregar ejemplo** específico de **acoso por tercero** (cliente)
  para distinguir del acoso jerárquico — un ejemplo extra en
  `chile/ejemplos/`.
- **Agregar checklist operativo** del protocolo (qué debe contener,
  como anexo o link).

## Vigencia de esta auto-revisión

Esta auto-revisión es **técnica**, no legal. NO modifica el estado
`borrador-no-validado` del archivo.

Una vez que el validador legal responda:

- Si acepta los hallazgos: se aplican y el `estado_revision` cambia a
  `validada`.
- Si rechaza algunos: se documenta el rechazo en el PR.
- Si requiere más investigación: nuevos hallazgos se agregan.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #8.
- **Respuesta del validador**: pendiente.
