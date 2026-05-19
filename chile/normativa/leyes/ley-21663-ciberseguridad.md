---
norma: Ley 21.663
slug: ley-21663-ciberseguridad
titulo_oficial: Ley Marco sobre Ciberseguridad e Infraestructura Crítica de la Información
publicacion: 2024-04-08
fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma=1204018
ultima_modificacion: 2024-04-08
vigencia: vigente con escalonamiento (régimen pleno desde 2025)
materia:
  - ciberseguridad
  - infraestructura crítica de información (ICI)
  - operadores de importancia vital (OIV)
  - notificación de incidentes
  - ANCI (Agencia Nacional de Ciberseguridad)
capa: 3
relacionada_con:
  - ley-19628-proteccion-datos
  - ley-21719-modificacion-lpd
  - ley-18168-telecomunicaciones
estado_revision: borrador-no-validado
validador: null
fecha_validacion: null
---

# Ley 21.663 — Marco sobre Ciberseguridad e Infraestructura Crítica

> **Borrador no validado.** Pendiente de revisión por abogado regulatorio o de
> ciberseguridad.

## Resumen

La Ley 21.663 (2024) es el **marco general de ciberseguridad** en Chile. Crea
la **Agencia Nacional de Ciberseguridad (ANCI)**, define **Operadores de
Importancia Vital (OIV)** e **Infraestructura Crítica de la Información (ICI)**,
establece **deberes de ciberseguridad**, **obligaciones de notificación** de
incidentes y un régimen sancionatorio.

Aplica a:

- **Órganos del Estado** que operan ICI.
- **OIV** privados: bancos, AFP, isapres, energía, telecomunicaciones,
  transporte, agua, salud, educación, alimentos, sistemas financieros.

## Estructura

| Título | Materia |
|---|---|
| I | Disposiciones generales |
| II | Servicios e infraestructura crítica |
| III | De la ANCI |
| IV | Deberes generales |
| V | Notificación de incidentes |
| VI | CSIRT (Computer Security Incident Response Teams) |
| VII | Sanciones |
| VIII | Disposiciones varias |

## Conceptos clave

| Concepto | Definición operativa |
|---|---|
| Ciberseguridad | Preservación de confidencialidad, integridad y disponibilidad de información |
| Servicio esencial | Servicio cuyo no funcionamiento causaría grave afectación a vida, salud, economía, seguridad |
| Infraestructura Crítica de la Información (ICI) | Sistemas que soportan servicios esenciales |
| Operador de Importancia Vital (OIV) | Entidad que opera ICI (calificada por ANCI) |
| Incidente de ciberseguridad | Evento que afecta confidencialidad, integridad, disponibilidad |
| CSIRT | Equipo de respuesta ante incidentes (nacional y sectoriales) |
| ANCI | Agencia Nacional de Ciberseguridad (autoridad fiscalizadora) |

## Operadores de Importancia Vital (OIV)

Calificación por la ANCI. Sectores típicos:

- **Energía** (generación, transmisión, distribución eléctrica;
  combustibles).
- **Servicios financieros** (bancos, AFP, isapres, valores).
- **Telecomunicaciones**.
- **Transporte** (aeronáutico, marítimo, terrestre).
- **Agua potable y saneamiento**.
- **Salud** (hospitales, redes).
- **Servicios estatales esenciales** (impuestos, registros, identidad).
- **Educación** (universidades grandes en algunos casos).
- **Alimentos** (producción y distribución masiva).

## Deberes del OIV (Título IV)

1. **Implementar plan de ciberseguridad** conforme estándares ANCI.
2. **Designar Encargado de Ciberseguridad** con autonomía y reporte directo
   al directorio o máxima autoridad.
3. **Gestión de riesgos** continua.
4. **Continuidad operacional** y planes de contingencia.
5. **Auditoría** periódica.
6. **Notificación de incidentes** (ver Título V).
7. **Cooperación** con CSIRT nacional y sectorial.
8. **Cumplimiento de estándares técnicos** publicados por ANCI.

## Notificación de incidentes (Título V)

### Plazos

- **Alerta temprana**: **3 horas** desde toma de conocimiento de un incidente
  significativo.
- **Reporte completo**: **72 horas** desde alerta temprana.
- **Reporte final**: cuando termina la gestión.

### Información a notificar

- Naturaleza del incidente.
- Sistemas afectados.
- Impacto estimado.
- Medidas adoptadas.
- Vector de ataque (cuando se conozca).

### Mecanismo

- A través del **CSIRT nacional** vía plataforma electrónica de la ANCI.
- Coordinación con CSIRTs sectoriales (financiero, energía, gobierno).

## Sanciones

| Infracción | Multa |
|---|---|
| Leves | Hasta 5.000 UTM |
| Graves | 5.001 - 20.000 UTM |
| Gravísimas | Hasta 40.000 UTM + suspensión actividad |

Procedimiento: sumario ANCI. Recurso de reposición + reclamación ante Corte
de Apelaciones.

## Régimen institucional

### ANCI (Agencia Nacional de Ciberseguridad)

- Servicio público descentralizado.
- Funciones: política nacional, fiscalización, sanciones, coordinación CSIRT
  nacional, cooperación internacional.

### CSIRT Nacional

- Recepción de notificaciones.
- Respuesta y coordinación ante incidentes.
- Inteligencia de amenazas.
- Cooperación con CSIRTs sectoriales y de otros países.

## Interacción con protección de datos

Si el incidente involucra **datos personales**, además de Ley 21.663 aplican:

- **Ley 19.628** (vigente) y **Ley 21.719** (desde 2026-12-01).
- **Notificación dual**: a ANCI (Ley 21.663) y a la APDP (Ley 21.719).
- **Notificación a titulares afectados** según LPDP.

## Conexiones con otras normas

- [`ley-19628-proteccion-datos`](ley-19628-proteccion-datos.md) +
  [`ley-21719-modificacion-lpd`](ley-21719-modificacion-lpd.md) — notificación
  de brechas en paralelo.
- [`ley-18168-telecomunicaciones`](ley-18168-telecomunicaciones.md) —
  operadores telecom como OIV.
- **Ley 20.285** — Transparencia: información de ciberseguridad puede ser
  reservada.
- **Código Penal** + **Ley 19.223** (delitos informáticos modificada por Ley
  21.459 / 2022) — tipos penales.
- **Convención de Budapest** sobre Ciberdelito (Chile parte).

## Cuándo invocar esta norma

- Diagnóstico de obligaciones de OIV.
- Diseño de plan de ciberseguridad corporativo.
- Notificación de incidente significativo.
- Coordinación con CSIRT.
- Defensa frente a procedimiento sancionatorio ANCI.
- Cruce con LPDP en brechas de datos personales.
- Auditoría de cumplimiento Ley 21.663.

## Disclaimers

- Borrador no validado.
- Vigencia escalonada; algunas obligaciones plenas desde 2025.
- Estándares técnicos publicados por la ANCI son centrales en la operación.
- Sector privado en proceso de adecuación; consultar publicaciones ANCI más
  recientes.
