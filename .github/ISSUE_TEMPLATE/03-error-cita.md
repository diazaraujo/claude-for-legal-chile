---
name: Error de cita o aplicación
about: Claude respondió mal una pregunta legal chilena usando este corpus
title: "[bug] <descripción corta>"
labels: ["bug"]
assignees: []
---

## La pregunta que hice

```
(pega el prompt completo aquí, sin datos personales)
```

## La respuesta del sistema

```
(pega la respuesta de Claude aquí)
```

## La respuesta correcta

¿Qué debería haber dicho? ¿Cuál es la cita normativa que lo sustenta?

## Hipótesis sobre el origen del error

- [ ] Falta el archivo de norma correspondiente en `chile/normativa/`
- [ ] El archivo existe pero el contenido es incorrecto/desactualizado
- [ ] El perfil que orquestó la respuesta no invocó la norma correcta
- [ ] El skill transversal (diagnóstico, plazos, citas) falló
- [ ] Otra (especifica)

Archivo(s) sospechoso(s) del corpus:

- ...

## Entorno de prueba

- ¿Qué cliente usaste? (Claude Code / Claude.ai Projects / API)
- ¿Modelo? (ej. Sonnet 4.6, Opus 4.7)
- ¿Cargaste el corpus completo o solo algunos archivos?
