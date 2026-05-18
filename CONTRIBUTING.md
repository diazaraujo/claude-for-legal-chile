# Cómo contribuir

Gracias por interesarte. Este es un proyecto open source mantenido por
[Unholster](https://unholster.com) cuyo objetivo es ofrecer un **corpus normativo
chileno estructurado** para uso con Claude. Toda contribución que ayude a hacer el
sistema más útil, más preciso o más completo es bienvenida.

> **Antes de empezar:** este proyecto trabaja con contenido legal. Las reglas
> editoriales y de revisión están diseñadas para que el corpus sea **citable** —
> consultable por abogados sin que tengamos que dar disclaimers de "esto puede estar
> mal". Por eso los PRs que tocan normativa pasan por revisión legal explícita.

Para contribuciones a los **plugins del upstream Anthropic** (no a `chile/`),
referirse adicionalmente a las
[design principles del upstream](https://github.com/anthropics/claude-for-legal/blob/main/CONTRIBUTING.md).

---

## Tipos de contribución

### 1. Redactar un archivo de norma nuevo

Las normas chilenas pendientes están listadas en
[`chile/normativa/leyes/00-indice.md`](chile/normativa/leyes/00-indice.md),
[`chile/normativa/codigos/00-indice.md`](chile/normativa/codigos/00-indice.md) y
[`chile/normativa/decretos/00-indice.md`](chile/normativa/decretos/00-indice.md).

**Schema canónico** del archivo: [`chile/normativa/README.md`](chile/normativa/README.md).

**Reglas:**

- **NO copies texto literal** completo de la norma. El texto íntegro vive en
  BCN/LeyChile. Este corpus es metadata + síntesis útil para el LLM.
- Frontmatter obligatorio con `estado_revision: borrador-no-validado` al crear.
- Declarar `fuente_oficial` con URL de BCN.
- Declarar `relacionada_con:` con slugs de otras normas conectadas — eso permite al
  LLM razonar sistémicamente, no sobre piezas aisladas.
- Mantener tono operativo: el documento se dirige a un LLM que va a invocarlo, no a
  un lector humano académico.

### 2. Validación legal de un archivo en `borrador-no-validado`

Si eres **abogado habilitado en Chile** y quieres revisar archivos:

1. Abre un issue presentándote (firma, materias de especialidad, motivación).
2. En el issue comentamos qué archivos quieres revisar primero.
3. Tu PR de validación cambia `estado_revision` a `validada`, llena `validador` con
   tu nombre, `fecha_validacion` con fecha ISO, y agrega correcciones inline.
4. Mergeamos como Unholster maintainer.

Tu nombre queda registrado en el archivo y en el `CHANGELOG.md` correspondiente como
crédito permanente.

### 3. Reportar un error de cita o aplicación

Si Claude (usando este corpus) responde mal una pregunta legal, ese es un bug que
queremos cerrar. Abre un issue con:

- La pregunta que hiciste.
- La respuesta que dio el sistema.
- Cuál es la respuesta correcta y la cita normativa que la sustenta.
- Tu hipótesis sobre qué archivo del corpus está mal o falta.

### 4. Agregar un caso de uso / ejemplo

En [`chile/ejemplos/`](chile/ejemplos/) viven consultas canónicas que muestran el
sistema en acción. Cada ejemplo es un archivo markdown con:

- Pregunta inicial del usuario.
- Respuesta del sistema (real o sintética, identificar cuál).
- Notas sobre qué archivos del corpus se invocaron.
- Por qué este caso es relevante.

### 5. Mejorar la arquitectura o los skills transversales

Si tienes ideas para los skills (`chile/skills/diagnostico.md`,
`chile/skills/citas-verificables.md`, `chile/skills/plazos.md`) o para la arquitectura
general, abre un issue con la etiqueta `needs-discussion`. Conversamos antes de
codificar.

---

## Flujo de PR

1. Forkea el repositorio.
2. Crea una rama: `git checkout -b mi-contribucion`.
3. Haz los cambios. Si tocas contenido normativo, marca `needs-legal-review` en el PR.
4. Commit con mensaje descriptivo (idealmente en español).
5. Push y abre el PR contra `main`.
6. Etiqueta el PR con la rama del derecho correspondiente (`rama:civil`, etc.) si
   aplica.

**Plazo de revisión**: PRs sin `needs-legal-review` se revisan en 3-7 días hábiles.
Los que requieren validación legal pueden tardar más — depende de la disponibilidad
de los validadores asociados.

---

## Convenciones

- **Idioma**: español de Chile (tuteo: "puedes", "haz", no "podés").
- **Citas normativas**: formato chileno: `Art. 41 CT`, `Art. 1545 CC`, `Ley 19.628`,
  `DS 40 (Mintrab, 1969)`.
- **Citas jurisprudenciales**: `CS Rol N° 12.345-2022`, `CA Santiago Rol N° 6.789-2023`.
- **Plazos**: especificar siempre si son **hábiles** o **corridos**. En Chile, sábado
  no es día hábil para tribunales (Art. 66 CPC).
- **Unidades**: UF, UTM, UTA, IPC, sueldo mínimo. No confundir UF con USD ni con peso
  argentino.
- **Frontmatter YAML**: comillas dobles para strings que contienen `:`, `'`, etc.
- **Markdown**: tablas para datos estructurados; bullets para listas heterogéneas.

---

## Código de conducta

Ver [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) (heredado del upstream).

En resumen: sé profesional. Esto es un proyecto orientado a práctica legal real;
mantenemos un tono colegiado. Reportes de conducta inadecuada van a
antonio@unholster.com.

---

## Licencia de las contribuciones

Toda contribución se licencia bajo [Apache-2.0](LICENSE), misma licencia del proyecto
y del upstream. Al abrir un PR confirmas que tienes derecho a contribuir el material
bajo esta licencia.

Si vas a contribuir material que es trabajo de un tercero (ej. análisis legal de un
estudio jurídico), necesitamos confirmación expresa de quien tiene los derechos. En
general preferimos que **redactes nuevo**, basándote en fuentes oficiales (BCN), en
lugar de copiar análisis de terceros.

---

## Contacto

- Issues: [github.com/diazaraujo/claude-for-legal-chile/issues](https://github.com/diazaraujo/claude-for-legal-chile/issues)
- Mantenedor: [@diazaraujo](https://github.com/diazaraujo) · antonio@unholster.com
- Unholster: [unholster.com](https://unholster.com)

Gracias por contribuir.
