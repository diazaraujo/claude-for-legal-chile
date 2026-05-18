# Índice de leyes

Leyes especiales chilenas con identidad propia que el corpus debe reconocer.
**Estado de revisión** en cada fila refleja si el archivo está validado por abogado
habilitado en Chile.

| Slug | Número | Título corto | Materia principal | Vigencia | Estado |
|---|---|---|---|---|---|
| [`ley-19628-proteccion-datos`](ley-19628-proteccion-datos.md) | 19.628 | Protección de la vida privada / datos personales | Privacidad | Vigente (modif. por 21.719) | borrador-no-validado |
| [`ley-21719-modificacion-lpd`](ley-21719-modificacion-lpd.md) | 21.719 | Modificación a la LPDP + creación APDP | Privacidad | Vigencia diferida: 2026-12-01 | borrador-no-validado |
| [`ley-16744-accidentes-trabajo`](ley-16744-accidentes-trabajo.md) | 16.744 | Accidentes del trabajo y enfermedades profesionales | Laboral / Seguridad social | Vigente | borrador-no-validado |
| [`ley-20123-subcontratacion`](ley-20123-subcontratacion.md) | 20.123 | Subcontratación y suministro de trabajadores | Laboral | Vigente | borrador-no-validado |
| [`ley-21561-reduccion-jornada`](ley-21561-reduccion-jornada.md) | 21.561 | Reducción gradual de la jornada laboral | Laboral | Vigente (escalonada hasta 2028) | borrador-no-validado |
| [`ley-21643-acoso-laboral`](ley-21643-acoso-laboral.md) | 21.643 | Ley Karin — prevención de acoso y violencia laboral | Laboral | Vigente | borrador-no-validado |
| `ley-21015-inclusion-laboral` | 21.015 | Inclusión laboral de personas con discapacidad | Laboral | Vigente | pendiente |
| `ley-21220-teletrabajo` | 21.220 | Teletrabajo y trabajo a distancia | Laboral | Vigente | pendiente |
| `ley-18046-sociedades-anonimas` | 18.046 | Sociedades Anónimas | Societario | Vigente | pendiente |
| `ley-19886-compras-publicas` | 19.886 | Bases sobre contratos administrativos | Compras públicas | Vigente | pendiente |
| `ley-19496-consumidor` | 19.496 | Protección de los derechos de los consumidores | Consumidor | Vigente | pendiente |
| `ley-20720-concursal` | 20.720 | Reorganización y liquidación de empresas y personas | Concursal | Vigente | pendiente |
| `ley-19880-procedimiento-administrativo` | 19.880 | Bases del procedimiento administrativo | Administrativo | Vigente | pendiente |
| `ley-19728-seguro-cesantia` | 19.728 | Seguro de cesantía | Laboral / Previsional | Vigente | pendiente |
| `ley-20940-relaciones-laborales` | 20.940 | Modernización del sistema de relaciones laborales | Laboral | Vigente | pendiente |
| `ley-21327-modernizacion-dt` | 21.327 | Modernización de la Dirección del Trabajo | Laboral / Administrativo | Vigente | pendiente |
| `ley-19947-matrimonio-civil` | 19.947 | Matrimonio Civil | Familia | Vigente | pendiente |
| `ley-19968-tribunales-familia` | 19.968 | Tribunales de Familia | Familia / Procesal | Vigente | pendiente |
| `ley-19253-indigenas` | 19.253 | Pueblos indígenas (CONADI) | Indígena | Vigente (fuera de alcance v1) | fuera-de-alcance |

## Cómo agregar una ley nueva

1. Crear archivo `ley-<numero>-<slug-corto>.md` siguiendo el schema en `../README.md`.
2. Marcar `estado_revision: borrador-no-validado` hasta que un abogado habilitado revise.
3. Agregar fila a esta tabla.
4. Si la ley tiene reglamentos asociados, agregarlos en `../decretos/`.
5. Crear o actualizar perfil(es) que la invocan en `../../perfiles/`.
