# Auto-revisiones técnicas pre-validación

> Notas de revisión **técnica** (NO legal) realizadas sobre los perfiles
> antes de mandarlos al validador legal. El objetivo es reducir el costo
> de tiempo del validador: el validador entra al archivo con los
> hallazgos técnicos ya identificados y se enfoca en la dimensión
> sustantiva.

## Qué es y qué NO es una auto-revisión

### Sí incluye

- Verificación de **consistencia interna** del archivo (frontmatter
  contra `MARCADORES.md`, formato canónico, links).
- Detección de **gaps obvios** (afirmaciones sin sustento; modificaciones
  posteriores conocidas no reflejadas).
- **Cross-checks** contra otros archivos del corpus (cruces, citas a
  artículos de leyes que existen en el corpus).
- **Preguntas específicas** para el validador legal — concretas, no
  abiertas.
- **Verificación de URLs** y referencias a fuentes oficiales.

### NO incluye

- **Validación legal**: solo abogado habilitado puede hacerla.
- **Verificación del texto contra BCN**: cuando es factible, se intenta;
  cuando BCN no responde, se flaglea.
- **Interpretación jurisprudencial**: queda para el validador.

## Quién hace las auto-revisiones

Antonio o Claude trabajando en el repo, sin perfil legal. Por eso TODOS
los hallazgos se presentan como **preguntas para el validador**, no como
correcciones definitivas.

## Cómo se usa

1. Antes de mandar un archivo al validador (issues `needs-legal-review`),
   se genera la nota en `chile/audits/<slug>-hallazgos.md`.
2. La nota se linka desde el issue de validación para que el validador
   la lea primero.
3. El validador puede aceptar, rechazar o ampliar cada hallazgo.
4. Tras la validación, la nota queda como **historial** (no se borra).

## Estructura canónica de una nota

```
---
archivo_revisado: <slug>
fecha_revision: YYYY-MM-DD
revisor_tecnico: <quién, no abogado>
issue_validacion: #N
estado: pendiente-de-validador | validador-revisó | descartada
---

# Auto-revisión: <título>

## Hallazgos críticos (decisión del validador)

(items que SIN duda requieren acción legal)

## Hallazgos técnicos (verificables sin abogado)

(items de formato, consistencia, links rotos)

## Preguntas abiertas para el validador

(zonas grises donde el revisor técnico no tiene base)

## Referencias verificadas / no verificadas

(citas que pude verificar contra BCN vs las que no)
```

## Notas actuales

| Archivo | Issue | Estado |
|---|---|---|
| `ley-21643-acoso-laboral` | [#8](https://github.com/diazaraujo/claude-for-legal-chile/issues/8) | pendiente-de-validador |
| `ley-21719-modificacion-lpd` | [#9](https://github.com/diazaraujo/claude-for-legal-chile/issues/9) | pendiente-de-validador |
| `ley-21713-reforma-tributaria-2024` | [#10](https://github.com/diazaraujo/claude-for-legal-chile/issues/10) | pendiente-de-validador |
| `ley-20393-rppj` | [#11](https://github.com/diazaraujo/claude-for-legal-chile/issues/11) | pendiente-de-validador |
| `ley-21595-delitos-economicos` | [#11](https://github.com/diazaraujo/claude-for-legal-chile/issues/11) | pendiente-de-validador |
| `codigo-trabajo` | [#12](https://github.com/diazaraujo/claude-for-legal-chile/issues/12) | pendiente-de-validador |
| `ley-21561-reduccion-jornada` | [#12](https://github.com/diazaraujo/claude-for-legal-chile/issues/12) | pendiente-de-validador |
