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
| `ley-19628-proteccion-datos` | [#9](https://github.com/diazaraujo/claude-for-legal-chile/issues/9) | pendiente-de-validador |
| `ley-21400-matrimonio-igualitario` | [#13](https://github.com/diazaraujo/claude-for-legal-chile/issues/13) | pendiente-de-validador |
| `ley-14908-alimentos` | [#13](https://github.com/diazaraujo/claude-for-legal-chile/issues/13) | pendiente-de-validador |
| `ley-19880-procedimiento-administrativo` | [#15](https://github.com/diazaraujo/claude-for-legal-chile/issues/15) | pendiente-de-validador |
| `ley-10336-cgr` | [#15](https://github.com/diazaraujo/claude-for-legal-chile/issues/15) | pendiente-de-validador |
| `codigo-civil` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-tributario` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-penal` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-procesal-penal` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-comercio` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-procedimiento-civil` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `codigo-organico-tribunales` | [#14](https://github.com/diazaraujo/claude-for-legal-chile/issues/14) | pendiente-de-validador |
| `ley-21000-cmf` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-18840-loc-banco-central` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-18010-operaciones-credito-dinero` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-18092-letras-pagares` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-21234-fraude-tarjetas` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-21521-fintec` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `ley-18045-mercado-valores` | [#21](https://github.com/diazaraujo/claude-for-legal-chile/issues/21) | pendiente-de-validador |
| `dfl-725-codigo-sanitario` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-19966-auge-ges` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-21030-aborto-tres-causales` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-20584-derechos-deberes-paciente` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-21331-salud-mental` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-19378-aps-municipal-salud` | [#17](https://github.com/diazaraujo/claude-for-legal-chile/issues/17) | pendiente-de-validador |
| `ley-20720-concursal` | [#19](https://github.com/diazaraujo/claude-for-legal-chile/issues/19) | pendiente-de-validador |
| `ley-19123-reparacion-rettig` | [#18](https://github.com/diazaraujo/claude-for-legal-chile/issues/18) | pendiente-de-validador |
| `ley-19992-reparacion-valech` | [#18](https://github.com/diazaraujo/claude-for-legal-chile/issues/18) | pendiente-de-validador |
| `ley-20405-indh` | [#18](https://github.com/diazaraujo/claude-for-legal-chile/issues/18) | pendiente-de-validador |
| `ley-21067-defensoria-ninez` | [#18](https://github.com/diazaraujo/claude-for-legal-chile/issues/18) | pendiente-de-validador |
| `dfl-458-urbanismo-construcciones` | [#20](https://github.com/diazaraujo/claude-for-legal-chile/issues/20) | pendiente-de-validador |
| `ley-19537-copropiedad-inmobiliaria` | [#20](https://github.com/diazaraujo/claude-for-legal-chile/issues/20) | pendiente-de-validador |
| `ley-21484-compraventa-inmuebles` | [#20](https://github.com/diazaraujo/claude-for-legal-chile/issues/20) | pendiente-de-validador |
| `dfl-1122-codigo-aguas` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-18248-codigo-mineria` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-18097-concesiones-mineras` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-21591-royalty-minero` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-18892-pesca-acuicultura` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-19300-medio-ambiente` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-21455-cambio-climatico` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `dl-1939-bienes-estado` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
| `ley-17288-monumentos-nacionales` | [#16](https://github.com/diazaraujo/claude-for-legal-chile/issues/16) | pendiente-de-validador |
