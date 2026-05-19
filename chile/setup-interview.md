# Setup interview — configuración inicial

Entrevista de configuración inicial del sistema **claude-for-legal-chile**. Genera
un `CLAUDE.md` personalizado para tu firma o práctica individual a partir de 15
preguntas en 6 bloques. Tiempo estimado: **10 minutos**.

Para invocarla, escribe en tu Project de Claude.ai o sesión de Claude Code:

> **"Corre la entrevista de configuración"** (o `/chile:setup`).

El sistema te hace las preguntas **una por una**, esperando tu respuesta antes de
continuar. Al final, genera tu `CLAUDE.md` personalizado en un bloque de código que
copias y pegas como reemplazo del `CLAUDE.md` base.

---

## Bloque 1 — Identidad profesional

### Pregunta 1.1
**¿Eres abogado/a habilitado/a en Chile, estudiante de derecho, equipo legal in-house
o builder/desarrollador?**

(Esto define el tono y el nivel de disclaimers operativos del sistema.)

### Pregunta 1.2
**¿Cuál es tu firma o institución?**

(Para personalizar la referencia. Ejemplo: "Estudio Pérez & Asociados", "Banco
ABC — Gerencia Legal", "Estudiante UC Derecho", "Builder independiente".)

### Pregunta 1.3
**¿Cuál es tu número de patente o ICA, si corresponde?**

(Solo si eres abogado. Si no aplica, responde "n/a".)

---

## Bloque 2 — Jurisdicción operativa

### Pregunta 2.1
**¿En qué ciudades o regiones operas principalmente?**

Ejemplo: "Santiago Centro y RM", "Valparaíso + Viña del Mar", "Concepción y
Biobío", "Antofagasta y Atacama".

### Pregunta 2.2
**¿Qué tribunales sueles intervenir?**

Marca los que apliquen:

- [ ] Juzgados civiles (1°, 2°, etc.)
- [ ] Juzgados del trabajo
- [ ] Tribunales de familia
- [ ] Juzgados de garantía / TOP
- [ ] Cortes de Apelaciones (¿cuáles?)
- [ ] Corte Suprema
- [ ] Tribunal Constitucional
- [ ] TDLC
- [ ] Tribunales Tributarios y Aduaneros
- [ ] Tribunales Ambientales
- [ ] Otros (especifica)

---

## Bloque 3 — Áreas de práctica

### Pregunta 3.1
**¿Qué áreas del derecho son tu volumen principal de trabajo? Ordénalas de mayor
a menor.**

Ejemplo: "1. Laboral, 2. Civil contractual, 3. Societario, 4. Privacidad."

### Pregunta 3.2
**¿Hay alguna sub-especialidad que te diferencia? (ej. tutela laboral, OPAs,
litigios de consumidor masivo)**

### Pregunta 3.3
**¿Hay áreas que el sistema NO debe abordar contigo? (ej. derecho penal si no es
tu fuero, derecho militar)**

---

## Bloque 4 — Modo de trabajo

### Pregunta 4.1
**¿Prefieres respuestas breves o exhaustivas?**

- "Breves": el sistema responde en 3-5 frases por defecto, expande solo si pides
- "Exhaustivas": el sistema entrega análisis completo desde el inicio
- "Adaptativo": depende de la complejidad de la consulta

### Pregunta 4.2
**¿Quieres que el sistema te pregunte antes de citar precedentes específicos, o
los cita directamente?**

- "Pregunta": pide rol o ministro antes de citar
- "Cita directamente": usa el corpus o conocimiento general; tú validas

### Pregunta 4.3
**¿Tu firma o equipo tiene plantillas internas de escritos que quieres que el
sistema respete?**

- Si sí: indica dónde están (ej. "carpeta DropBox: Plantillas/Templates")
- Si no: el sistema usa estructuras estándar

### Pregunta 4.4
**¿Trabajas en español, español + inglés (clientes corporativos), o español
chileno formal exclusivamente?**

---

## Bloque 5 — Datos sensibles y privacidad

### Pregunta 5.1
**¿Vas a cargar al sistema documentos con datos de clientes (RUT, expedientes,
contratos firmados)?**

- Si sí: el sistema aplica modo reserva — no exporta esos datos a terceros, los
  trata como confidenciales por defecto
- Si no: modo abierto, solo doctrina pública

### Pregunta 5.2
**¿Necesitas que el sistema asuma deber de secreto profesional (Art. 360 N° 1
CPC) en el análisis?**

(Si trabajas con clientes reales, sí. El sistema te recordará no compartir datos
identificables fuera de tu entorno.)

---

## Bloque 6 — Preferencias finales

### Pregunta 6.1
**¿Quieres que el sistema te avise cuando una norma esté próxima a entrar en
vigencia (ej. Ley 21.719 el 1-dic-2026)?**

### Pregunta 6.2
**¿Hay convenios colectivos, reglamentos internos de clientes habituales, o
políticas de tu firma que el sistema debe conocer?**

(Si sí, cárgalos en el Project como archivos adicionales.)

### Pregunta 6.3
**¿Cómo te diriges al sistema? (tuteo, usted, neutral)**

---

## Generación del `CLAUDE.md` personalizado

Al terminar el bloque 6, el sistema integra todas tus respuestas en un `CLAUDE.md`
que reemplaza el genérico. Estructura del archivo generado:

```markdown
# Perfil de práctica · <Tu nombre o firma>

## Identidad
- Profesional: <tipo>
- Firma: <nombre>
- Número de patente / ICA: <número>

## Jurisdicción operativa
- Ciudades/regiones: <lista>
- Tribunales: <lista>

## Áreas de práctica (en orden de prioridad)
1. <Área 1>
2. <Área 2>
...

## Modo de trabajo
- Respuestas: <breves / exhaustivas / adaptativo>
- Citas: <preguntar / directo>
- Plantillas: <ubicación o n/a>
- Idioma: <español / bilingüe>

## Reserva y privacidad
- Documentos del cliente: <sí / no>
- Secreto profesional: <activo / inactivo>

## Preferencias adicionales
- Avisos de vigencia: <sí / no>
- Trato: <tuteo / usted / neutral>
- Documentos cargados: <lista>

## Reglas operativas heredadas del sistema base
[contenido de chile/CLAUDE.md general]
```

---

## Actualizar el perfil

Cuando quieras cambiar algún campo, escribe:

> **"Corre la entrevista de actualización"** (o `/chile:setup --update`).

El sistema te muestra los valores actuales y pregunta solo los campos que quieres
cambiar.

## Plantilla del output

Ver `chile/setup-output-TEMPLATE.md` para el formato exacto del `CLAUDE.md`
generado.
