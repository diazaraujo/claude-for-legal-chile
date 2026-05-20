# Protocolo de validación legal

> Documento canónico que define **quién**, **cómo** y **bajo qué
> responsabilidad** se valida cada archivo del corpus. Sin validación
> formal, todo archivo opera en estado `borrador-no-validado` y el
> sistema antepone disclaimer al citarlo.

## Por qué importa

Este corpus es la **base normativa** sobre la cual operará Claude (y
otros agentes) cuando un abogado consulte sobre derecho chileno. Una
norma mal explicada, una cita errónea, un plazo equivocado: todo eso
se propaga al **escrito final del cliente**.

La validación formal **NO es opcional**: es lo que distingue un corpus
de referencia operativa de un brainstorm asistido por LLM.

## Quién puede validar

### Requisito mínimo

- **Abogado habilitado** en Chile con **patente al día**.
- **5+ años de experiencia** en la rama del derecho que valida (o
  equivalente — académico, fiscal, dictaminador).
- **Sin conflicto de interés** con clientes / casos vigentes del
  validador en la materia del archivo (ver §Conflictos).

### Quién NO debería validar

- Abogado sin habilitación vigente.
- Estudiantes / egresados sin patente.
- Profesional de otra disciplina (contador, ingeniero, etc.), incluso
  con conocimiento técnico — su rol es **revisión técnica**, no
  validación legal.
- Asistentes IA (incluyendo Claude que escribió el borrador): el
  sistema **NO** puede auto-validar; necesita ojos humanos habilitados.

## Qué se valida

Cada archivo del corpus tiene un campo `estado_revision` en frontmatter
con valores controlados (ver [`MARCADORES.md`](MARCADORES.md)).

### Para perfiles capa 3 (normas individuales)

El validador revisa **6 dimensiones**:

#### 1. Vigencia + texto

- ¿La norma está vigente al día de la validación?
- ¿El texto citado corresponde al texto consolidado en BCN/LeyChile?
- ¿Los artículos citados existen + están en el rango correcto?
- ¿Las modificaciones recientes están reflejadas (con fecha y ley
  modificatoria)?

#### 2. Correctitud sustantiva

- ¿La interpretación del régimen es **correcta**?
- ¿Los efectos atribuidos a la norma son los efectivos?
- ¿Las excepciones señaladas son las que la doctrina + jurisprudencia
  reconocen?

#### 3. Cobertura

- ¿Faltan elementos importantes de la norma?
- ¿Hay aspectos relevantes para la práctica que el perfil no toca?

#### 4. Cruces normativos

- ¿Las normas relacionadas (`relacionada_per`) son las correctas?
- ¿Faltan cruces evidentes con otras normas?

#### 5. Disclaimers + tono

- ¿El archivo identifica adecuadamente las áreas de incertidumbre?
- ¿No promete certeza donde no la hay?
- ¿No asume conocimiento que el usuario del sistema no tiene?

#### 6. Operatividad

- ¿La sección "Cuándo invocar esta norma" lista casos reales?
- ¿Los pasos operativos son correctos?
- ¿Los plazos están bien?

### Para perfiles por rama (orquestadores)

Adicionalmente:

- ¿Las "Red flags" son **realmente** señales de problema?
- ¿Cubre los casos más comunes que un abogado de la rama enfrenta?
- ¿Los cross-links con otros perfiles son acertados?

### Para skills

- ¿Las instrucciones que el skill da al sistema son **operativamente
  ejecutables**?
- ¿No inducen comportamientos riesgosos (alucinación, sobre-promesa)?

### Para ejemplos

- ¿El escenario es **realista**?
- ¿La respuesta del sistema es **defendible** ante un par profesional?
- ¿Los cálculos / cifras / plazos están correctos?

## Cómo se valida — flujo formal

### Etapa 1 — Manifestación

Validador abre **issue** con el template
[`02-validacion-legal.md`](../.github/ISSUE_TEMPLATE/02-validacion-legal.md):

- Identificación profesional.
- Lista de slugs a revisar.
- Confirmación de no conflicto de interés.

### Etapa 2 — Asignación

El maintainer (Unholster) confirma:

- Acepta la oferta de validación.
- Asigna los archivos al validador.
- Le entrega checklist específico de la rama si aplica.

### Etapa 3 — Revisión

Validador revisa cada archivo asignado:

- Edita inline con propuestas.
- Marca con `**[VALIDADOR: <comentario>]**` cualquier inquietud.
- Levanta issues separados para cambios estructurales.

### Etapa 4 — Pull Request

Validador (o maintainer en su nombre) abre PR con:

- **Cambios al texto** si corresponde.
- **Cambio del frontmatter** `estado_revision` a `validada`.
- **Firma del validador**: nombre + patente + fecha en el frontmatter.
- **CHANGELOG** actualizado con la validación.

### Etapa 5 — Merge

Maintainer revisa:

- Que el validador esté habilitado (verificación de patente).
- Que los cambios estén bien estructurados.
- Que el frontmatter quede consistente.

Tras el merge, el archivo opera **sin disclaimer adicional** y puede
citarse directamente.

## Responsabilidad del validador

El validador NO se hace responsable de:

- Casos concretos en los que el archivo se aplique.
- Cambios normativos posteriores a la fecha de validación.
- Interpretaciones que el sistema haga al combinar la norma con otros
  archivos.

El validador SÍ se hace responsable de:

- Que el contenido validado refleje **el estado del derecho a la fecha
  de validación**.
- Que la cita normativa exista + sea correcta.
- Que las afirmaciones no excedan lo que la doctrina + jurisprudencia
  sostienen razonablemente.

### Reconocimiento

El nombre + patente del validador queda registrado:

- En el frontmatter del archivo (`validador:` + `fecha_validacion:`).
- En el [CHANGELOG.md](CHANGELOG.md) del proyecto.
- En la página de créditos (cuando se publique).

## Conflictos de interés

### Caso a declarar

El validador debe declarar y abstenerse si:

- Tiene **caso vigente o reciente** (≤2 años) sobre la materia del
  archivo, donde el contenido podría afectar su posición.
- Es **asesor de gremio / lobby** con posición sobre la materia.
- Es **socio capital** de empresa cuya defensa podría beneficiarse.

### Caso aceptable

- Especialización académica + ejercicio general en la rama.
- Casos pasados (>2 años) sin posición vigente.
- Asesor de comunidad / ONG sin agenda partidaria.

## Vigencia de la validación

Una validación NO es perpetua:

- **Por defecto**: 2 años desde la fecha.
- **Excepciones**:
  - Norma con vigencia escalonada → revalidar tras cada fase.
  - Reforma posterior → revalidar.
  - Jurisprudencia que cambia criterio → revalidar.

El frontmatter incluye `fecha_validacion`; el sistema marca como
`requiere-revalidacion` si supera los 2 años.

## Prioridades de validación

### Tier 1 — Alta vigencia + alto uso (urgente)

| Archivo | Razón |
|---|---|
| [`ley-21643-acoso-laboral`](normativa/leyes/ley-21643-acoso-laboral.md) | Ley Karin (2024), aplicación masiva en empresas |
| [`ley-21561-reduccion-jornada`](normativa/leyes/ley-21561-reduccion-jornada.md) | 40h en vigencia escalonada hasta 2028 |
| [`ley-21719-modificacion-lpd`](normativa/leyes/ley-21719-modificacion-lpd.md) | Vigencia 2026-12-01; preparación urgente |
| [`ley-21595-delitos-economicos`](normativa/leyes/ley-21595-delitos-economicos.md) | Reforma penal corporativa de 2023 |
| [`ley-21713-reforma-tributaria-2024`](normativa/leyes/ley-21713-reforma-tributaria-2024.md) | Reforma Tributaria activa |
| [`ley-20393-rppj`](normativa/leyes/ley-20393-rppj.md) | RPPJ con catálogo ampliado por 21.595 |
| [`codigo-trabajo`](normativa/codigos/codigo-trabajo.md) | Base laboral universal |
| [`codigo-tributario`](normativa/codigos/codigo-tributario.md) | Base procesal tributaria |

### Tier 2 — Alta vigencia + uso especializado

Códigos básicos + leyes orgánicas + recursos naturales + privacidad.

### Tier 3 — Histórico + DDHH

Reparación dictadura + LOC históricas + jurisprudencia consolidada.

### Tier 4 — Sectorial nicho

Pesca, minería, aeronáutico, etc. — esperan a validadores especializados.

## Métricas del programa

Tracked en `CHANGELOG.md` del proyecto:

- N° de archivos en `borrador-no-validado` → meta: <50% para v1.0.
- N° de archivos en `validada` → meta: 50%+ del Tier 1 para v1.0.
- N° de validadores activos.
- Tiempo promedio de validación (issue → merge).

## Compensación + reconocimiento

El programa de validación es **honorario** por default (no remunerado).

Casos donde Unholster puede ofrecer compensación:

- Validación de Tier 1 prioritario por especialistas con costo de
  oportunidad alto.
- Validación masiva (≥10 archivos del corpus).

Negociar caso a caso vía issue + comunicación privada.

### Reconocimiento no monetario

- Nombre + estudio en página de créditos del proyecto.
- Mención en post de comunicación al lanzar v1.0.
- Acceso anticipado a productos Unholster relacionados.
- Carta de reconocimiento formal.

## Cómo empezar — para validadores

1. Lee este documento + [`MARCADORES.md`](MARCADORES.md) + el
   [`README` del proyecto](../README.md).
2. Identifica 3-5 archivos del corpus en tu especialidad.
3. Lee el contenido de esos archivos.
4. Si el modelo te parece bueno y querés validar, abre el
   [issue de oferta](../.github/ISSUE_TEMPLATE/02-validacion-legal.md).
5. Esperarás respuesta del maintainer en <72 horas hábiles.

## Cómo empezar — para maintainer

1. Ver issues con label `needs-legal-review`.
2. Priorizar Tier 1.
3. Difundir oferta en:
   - Redes profesionales (LinkedIn).
   - Colegios de abogados (gremiales).
   - Estudios jurídicos del ecosistema legaltech chileno.
   - Universidades (Derecho + clínicas jurídicas).
4. Coordinar con validadores que se ofrezcan.
5. Acompañar el proceso hasta merge.

## Cambios al protocolo

Este documento se actualiza por PR. Cambios estructurales requieren:

- Discusión previa en issue.
- Aprobación del maintainer (Antonio Díaz-Araujo / Unholster).
- Notificación a validadores actuales.

## Versión

- **v0.1.0** (2026-05-19) — Versión inicial.
