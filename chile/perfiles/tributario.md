---
perfil: tributario
slug: perfil-tributario
ambito: derecho tributario chileno · impuestos federales, regionales y municipales
capa: orquestador
estado_revision: borrador-no-validado
fuente_corpus: chile/normativa/codigos/codigo-tributario.md + 8 leyes especiales
ultima_actualizacion: 2026-05-19
---

# Perfil tributario — Claude Legal Chile

> **Orquestador del derecho tributario chileno.** Para detalle sustantivo
> ver Código Tributario + leyes específicas en `chile/normativa/`.

> **Borrador no validado.** Verificar con tributarista habilitado antes
> de aplicar en escritos.

## Cuándo se activa este perfil

- Impuesto a la Renta (LIR), IVA, impuestos específicos.
- Patentes municipales, contribuciones de bienes raíces, permisos
  circulación.
- Royalty minero (Ley 21.591).
- Reorganizaciones, ganancias de capital, donaciones, herencias.
- Fiscalización SII, citaciones, liquidaciones, giros, reclamos.
- Tribunales Tributarios y Aduaneros (TTA).
- Convenios para evitar la doble tributación (CDI).
- Norma General Antielusiva (NGA) Ley 21.713.
- Imposición de plataformas digitales, BEPS.
- Operaciones cambiarias, capítulo XIV BCCh.
- Compliance fiscal de empresas (Ley 21.713, Art. 100 CT).
- Beneficios + franquicias: SENCE (19.518), Ricarte Soto, donaciones.

## Normas que invoca este perfil

### Norma matriz

- [`codigo-tributario`](../normativa/codigos/codigo-tributario.md) — DL 830:
  procedimiento administrativo + sancionatorio tributario, prescripción,
  notificaciones, plazos, recursos. **Eje del sistema tributario chileno.**

### Impuestos principales

- [`dl-824-renta`](../normativa/leyes/dl-824-renta.md) — Ley de Impuesto a
  la Renta (LIR). Primera Categoría, Global Complementario, Adicional,
  Único de Segunda, ganancias de capital.
- [`dl-825-iva`](../normativa/leyes/dl-825-iva.md) — Impuesto al Valor
  Agregado y otros impuestos al consumo.

### Reformas estructurales

- [`ley-21420-reduccion-exenciones`](../normativa/leyes/ley-21420-reduccion-exenciones.md) —
  reducción de exenciones tributarias (IVA a servicios profesionales PJ).
- [`ley-21713-reforma-tributaria-2024`](../normativa/leyes/ley-21713-reforma-tributaria-2024.md) —
  NGA reforzada, plataformas digitales, BEPS. **Alerta de volatilidad —
  reglamentos SII en publicación.**

### Tributos territoriales + locales

- [`ley-17235-impuesto-territorial`](../normativa/leyes/ley-17235-impuesto-territorial.md) —
  contribuciones de bienes raíces, avalúo fiscal, sobretasa altos avalúos.
- [`dl-3063-rentas-municipales`](../normativa/leyes/dl-3063-rentas-municipales.md) —
  patentes municipales, permisos circulación, derechos, FCM.

### Sectorial — minería

- [`ley-21591-royalty-minero`](../normativa/leyes/ley-21591-royalty-minero.md) —
  Royalty 2023, componente ad valorem + margen, distribución regional.

### Cruce regulatorio

- [`ley-21000-cmf`](../normativa/leyes/ley-21000-cmf.md) — CMF
  (operaciones bancarias + valores con efectos tributarios).
- [`ley-18840-loc-banco-central`](../normativa/leyes/ley-18840-loc-banco-central.md) —
  BCCh (capítulo XIV CNF, operaciones cambiarias).
- [`ley-19913-lavado-activos`](../normativa/leyes/ley-19913-lavado-activos.md) —
  cruce con planificación tributaria agresiva.
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  delito tributario en catálogo ampliado.

### Beneficios + franquicias

- [`ley-19518-sence-capacitacion`](../normativa/leyes/ley-19518-sence-capacitacion.md) —
  franquicia tributaria de capacitación (1% remuneraciones).
- Ley 19.247 — donaciones educacionales.
- Ley 19.885 — donaciones sociales.
- Ley 20.850 — Ricarte Soto (cobertura adicional alto costo).

## Red flags tributarios (activación automática)

### En primera categoría / Renta

1. **Gastos no rechazados sin documentación**: factura electrónica o
   boleta de honorarios obligatorias.
2. **Pago a relacionados sin precio de mercado**: ajuste SII vía precios
   de transferencia (Art. 41 E LIR).
3. **Reinversión de utilidades sin acreditación**: pierde beneficio.
4. **Retiro presuntivo**: cuando socio usa bienes sociales para fin
   personal sin pagar arriendo de mercado.
5. **Préstamo a accionista no documentado**: SII puede recalificar como
   retiro encubierto.
6. **Cambio de régimen tributario** (Pyme vs general) sin cumplir
   requisitos: rechazo en fiscalización.

### En IVA

1. **Servicio profesional prestado por PJ después de 2023** sin emisión
   de factura afecta a IVA (Ley 21.420): infracción + multa.
2. **Crédito fiscal por compras de uso personal**: rechazo + sanción.
3. **Emisión de factura sin documento de respaldo**: delito tributario.
4. **Exportación sin documentación SNA**: pierde devolución IVA
   exportador.
5. **Compraventa de inmueble usado** entre habituales sin pago IVA al
   valor agregado (Ley 21.210 modificada): contingencia.

### En reorganizaciones

1. **División, fusión o conversión sin valor tributario continuo**:
   pérdida del costo histórico de los bienes.
2. **Reorganización con pérdida tributaria absorbida por sociedad
   distinta**: limitación (Art. 31 N° 3 + Ley 21.713).
3. **Aporte societario sin formalidad escritura pública + escritura SII**:
   no oponible al SII como reorganización.

### En patrimonio + sucesión

1. **Donación entre vivos sin pago de impuesto**: presunción de operación
   onerosa.
2. **Asignación testamentaria sin inventario**: imposibilidad de
   determinar impuesto a la herencia.
3. **Bienes en el extranjero no declarados**: cruce con FATCA, CRS,
   intercambio automático.

### En procedimiento

1. **Citación SII sin respuesta dentro de plazo (1 mes)**: SII queda
   facultado para liquidar sin más trámite.
2. **Liquidación sin reclamo dentro de 90 días**: queda firme.
3. **Reclamo sin patrocinio de abogado** ante TTA: inadmisible (salvo
   procedimiento general de reclamación administrativa).
4. **Notificación por correo electrónico no autorizado en RIE**: nula.

### En NGA + planificación agresiva

1. **Operaciones sin sustancia económica** dirigidas únicamente a
   reducir impuesto: Norma General Antielusiva (Art. 4 bis + ter CT).
2. **Cadena de empresas en paraísos fiscales** sin operación real:
   recalificación + multa + delito si hay dolo.
3. **Precios de transferencia no documentados**: ajuste + sanción.
4. **Aprovechamiento de exención derogada antes de cancelación**:
   limitación temporal.

### En cobranzas + acción ejecutiva del SII

1. **Embargo sobre bienes esenciales** del giro: suspendible vía amparo
   tributario.
2. **Apremio personal** del representante legal: limitado, solo en casos
   específicos.
3. **Bloqueo de cuentas bancarias** sin notificación previa: revisable.

## Plazos críticos tributarios

| Plazo | Norma | Tipo |
|---|---|---|
| Prescripción ordinaria liquidación | Art. 200 CT | 3 años desde vencimiento |
| Prescripción extraordinaria (declaración maliciosa) | Art. 200 CT | 6 años |
| Respuesta a citación SII | Art. 63 CT | 1 mes (prorrogable) |
| Reclamo de liquidación ante TTA | Art. 124 CT | 90 días desde notificación |
| Reclamo de giro | Art. 124 CT | 90 días |
| Recurso de Reposición Administrativa Voluntaria (RAV) | Art. 123 bis CT | 30 días |
| Apelación de sentencia TTA ante CA | Art. 139 CT | 15 días |
| Casación ante CS | Art. 145 CT | 15 días |
| Declaración Renta (Form. 22) | calendario SII | abril año siguiente |
| Declaración IVA (Form. 29) | calendario SII | día 12 mes siguiente |
| Pago contribuciones bienes raíces | calendario SII | 4 cuotas (abril/junio/sept/nov) |
| Pago patente municipal | calendario municipal | enero o julio |

## Skills que orquesta este perfil

- [`diagnostico`](../skills/diagnostico.md) — clasifica + activa.
- [`citas-verificables`](../skills/citas-verificables.md) — citas a CT +
  LIR + IVA + Circulares + Oficios SII.
- [`plazos`](../skills/plazos.md) — prescripción, reclamo, RAV, etc.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) —
  cuando empresa con MPD se enfrenta a delito tributario.

## Casos típicos

(Pendientes — Fase 3:)

- Régimen Pyme vs régimen general: criterios + transición.
- Servicios profesionales: PN (boleta honorarios) vs PJ (factura + IVA).
- Reorganización societaria: división vs fusión vs conversión.
- Citación SII: estrategia de respuesta + plazos.
- Reclamo de liquidación ante TTA: requisitos + cuantía.
- Pago internacional a relacionados: precios de transferencia.
- Donación con beneficio tributario: requisitos por ley específica.
- Royalty minero: cálculo + componente margen.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por tributarista.
- **Circulares + Oficios Ordinarios SII** son operativamente centrales —
  pueden cambiar criterio sin previo aviso.
- **Reforma Tributaria 2024 (Ley 21.713)** tiene escalonamiento +
  reglamentos pendientes. **Alerta de volatilidad activa.**
- **Convenios para evitar doble tributación (CDI)** Chile-país pueden
  alterar régimen general.
- **Precios de transferencia + BEPS**: análisis técnico + asesoría
  multinacional.
- **TTA + Cortes**: jurisprudencia abundante, revisar criterios
  recientes.

## Conexiones con otros perfiles

- [`perfil-societario`](societario.md) — toda reorganización + tributación
  societaria.
- [`perfil-civil`](civil.md) — impuesto a herencia + ganancias de capital
  inmueble personal.
- [`perfil-laboral`](laboral.md) — cotizaciones + impuesto sobre
  remuneraciones.
- [`perfil-penal`](penal.md) — delitos tributarios (Art. 97 CT, Art. 100
  CT, Ley 21.595).
- [`perfil-administrativo`](administrativo.md) — fiscalización + sanciones
  + recursos.
