---
perfil: civil
slug: perfil-civil
ambito: derecho civil chileno · obligaciones, contratos, responsabilidad, familia patrimonial
capa: orquestador
estado_revision: borrador-no-validado
fuente_corpus: chile/normativa/codigos/codigo-civil.md + leyes complementarias
ultima_actualizacion: 2026-05-19
---

# Perfil civil — Claude Legal Chile

> **Orquestador del derecho civil chileno.** Para el detalle sustantivo,
> ver Código Civil + leyes complementarias en `chile/normativa/`.

> **Borrador no validado.** Verificar con abogado civil antes de aplicar
> en escritos.

## Cuándo se activa este perfil

- Contratos: validez, vicios del consentimiento, ejecución, terminación.
- Obligaciones: novación, prescripción, mora, daños.
- Responsabilidad civil contractual y extracontractual.
- Compraventa, arrendamiento, mandato, comodato, depósito, mutuo.
- Familia patrimonial: sociedad conyugal, separación de bienes,
  participación gananciales, AUC, matrimonio igualitario.
- Sucesión: testamento, herencia, asignaciones forzosas.
- Posesión, dominio, servidumbres, prescripción adquisitiva.
- Copropiedad, condominios.
- Crédito personal, fianza, prenda, hipoteca.

## Normas que invoca este perfil

### Norma matriz

- [`codigo-civil`](../normativa/codigos/codigo-civil.md) — CC Andrés Bello
  (1857) + reformas. **Eje del derecho civil chileno.** Libro I personas,
  Libro II bienes, Libro III sucesión por causa de muerte, Libro IV
  obligaciones y contratos.

### Familia patrimonial

- [`ley-19947-matrimonio-civil`](../normativa/leyes/ley-19947-matrimonio-civil.md) —
  régimen del matrimonio.
- [`ley-21400-matrimonio-igualitario`](../normativa/leyes/ley-21400-matrimonio-igualitario.md) —
  modifica CC, 19.947, 19.620, 20.830, 21.120 (2021/2022).
- [`ley-20830-acuerdo-union-civil`](../normativa/leyes/ley-20830-acuerdo-union-civil.md) —
  AUC: convivencia jurídicamente reconocida.
- [`ley-19968-tribunales-familia`](../normativa/leyes/ley-19968-tribunales-familia.md) —
  Tribunales de Familia (cruce procesal).
- [`ley-19620-adopciones`](../normativa/leyes/ley-19620-adopciones.md) —
  régimen de adopciones.
- [`ley-14908-alimentos`](../normativa/leyes/ley-14908-alimentos.md) —
  pensiones alimenticias + RNDPA + GAM.
- [`ley-20066-vif`](../normativa/leyes/ley-20066-vif.md) — Violencia
  Intrafamiliar (cruce penal + protección).

### Contratos especiales

- [`ley-19496-consumidor`](../normativa/leyes/ley-19496-consumidor.md) —
  LPC (régimen consumidor — para contratos B2C).
- [`ley-18092-letras-pagares`](../normativa/leyes/ley-18092-letras-pagares.md) —
  pagarés (cuando contrato civil incluye documento de crédito).
- [`ley-18010-operaciones-credito-dinero`](../normativa/leyes/ley-18010-operaciones-credito-dinero.md) —
  OCD: UF, intereses, TMC (operaciones de crédito civiles).
- [`ley-19537-copropiedad-inmobiliaria`](../normativa/leyes/ley-19537-copropiedad-inmobiliaria.md) —
  condominios.
- [`ley-21484-compraventa-inmuebles`](../normativa/leyes/ley-21484-compraventa-inmuebles.md) —
  responsabilidad por información falsa en compraventas con financiamiento.

### Inmuebles

- [`dfl-458-urbanismo-construcciones`](../normativa/leyes/dfl-458-urbanismo-construcciones.md) —
  LGUC (cruce con permisos).
- [`dfl-1122-codigo-aguas`](../normativa/leyes/dfl-1122-codigo-aguas.md) —
  Código de Aguas (cuando inmueble incluye DAA).
- [`dl-1939-bienes-estado`](../normativa/leyes/dl-1939-bienes-estado.md) —
  cuando se trata de inmueble fiscal.

### Persona

- [`ley-19628-proteccion-datos`](../normativa/leyes/ley-19628-proteccion-datos.md) —
  LPDP + Ley 21.719 (datos personales).
- [`ley-20584-derechos-deberes-paciente`](../normativa/leyes/ley-20584-derechos-deberes-paciente.md) —
  derechos del paciente (consentimiento, intimidad).
- [`ley-21120-identidad-genero`](../normativa/leyes/ley-21120-identidad-genero.md) —
  cambio de nombre + sexo registral.

### Responsabilidad civil extracontractual

- [`codigo-civil`](../normativa/codigos/codigo-civil.md) — Art. 2.314+ (régimen
  general).
- Cruce con [`ley-19733-libertades-opinion-informacion`](../normativa/leyes/ley-19733-libertades-opinion-informacion.md) —
  daño moral por medios.
- Cruce con [`ley-21484-compraventa-inmuebles`](../normativa/leyes/ley-21484-compraventa-inmuebles.md) —
  responsabilidad solidaria vendedor + intervinientes.

### Cruce con otras ramas

- **Comercial**: [`codigo-comercio`](../normativa/codigos/codigo-comercio.md)
  y [`perfil-societario`](societario.md).
- **Procesal**: [`codigo-procedimiento-civil`](../normativa/codigos/codigo-procedimiento-civil.md) —
  procedimiento ordinario, ejecutivo, sumario.

## Red flags civiles (activación automática)

### En contrato

1. **Cláusula contraria a la moral, el orden público o las buenas
   costumbres** → nula (Art. 1.461 CC).
2. **Objeto ilícito** (cosa fuera del comercio, hecho contrario a la ley)
   → nulidad absoluta.
3. **Vicio del consentimiento** (error, fuerza, dolo) → acción de
   rescisión.
4. **Lesión enorme** en compraventa de bienes raíces (Art. 1.888 CC) →
   rescisión.
5. **Cláusula abusiva** en contrato adhesivo B2C → revisión bajo Ley
   19.496 + cruce con derecho civil.
6. **Plazo de prescripción** vencido → excepción para ejercer.

### En obligaciones

1. **Constitución en mora sin requerimiento** → solo válido si plazo
   cierto (regla del CC, modificada en OCD por Ley 18.010).
2. **Cláusula penal manifiestamente desproporcionada** → reducción
   judicial (Art. 1.544 CC).
3. **Confesión judicial sin contrainterrogatorio** → válida pero
   impugnable según contexto.
4. **Documento privado sin reconocimiento** → no es título ejecutivo.

### En familia patrimonial

1. **Sociedad conyugal con bienes del marido sin participación de la
   mujer** → revisión bajo reforma 2021 + matrimonio igualitario.
2. **Capitulaciones matrimoniales sin escritura pública** → nulas.
3. **AUC sin pacto de comunidad** → cada conviviente conserva su patrimonio
   (separación total por defecto).
4. **Pensión de alimentos no inscrita en RNDPA** → no genera retención
   automática.
5. **Cambio de régimen patrimonial** sin escritura pública + inscripción
   → no oponible.

### En sucesión

1. **Testamento sin formalidades** (cerrado / abierto / privilegiado) →
   nulo.
2. **Asignación que afecta legítima** sin justificación legal → reducible
   por acción de partición.
3. **Indignidad sucesoria** invocada → causales tasadas (Art. 968 CC).
4. **Herencia con deudas no inventariadas** → herederos pueden aceptar
   bajo beneficio de inventario.

### En inmuebles

1. **Compraventa de inmueble por instrumento privado** → no transfiere
   dominio; requiere escritura + inscripción CBR.
2. **Servidumbre no inscrita** → no oponible a terceros adquirentes.
3. **Posesión sin justo título** durante 10 años → posible prescripción
   adquisitiva extraordinaria.
4. **Compraventa con financiamiento hipotecario y vicios ocultos** → cruce
   con Ley 21.484 (responsabilidad solidaria vendedor + intervinientes).
5. **Condominio sin reglamento inscrito** → bienes comunes sin régimen
   aplicable.

### En crédito + garantías

1. **Pagaré sin protesto** → pierde acción ejecutiva pero conserva acción
   ordinaria.
2. **Hipoteca sin inscripción** → no oponible a terceros.
3. **Prenda sin formalidades específicas** según el tipo (común vs sin
   desplazamiento) → ineficaz.
4. **Tasa de interés superior a TMC** → cobro reducible + sanción
   (Ley 18.010).

## Plazos críticos civiles

| Plazo | Norma | Tipo |
|---|---|---|
| Prescripción acción ordinaria | Art. 2.515 CC | 5 años |
| Prescripción acción ejecutiva | Art. 2.515 CC | 3 años |
| Prescripción acción rescisoria por lesión enorme | Art. 1.896 CC | 4 años |
| Prescripción adquisitiva ordinaria de inmueble | Art. 2.508 CC | 5 años con título |
| Prescripción adquisitiva extraordinaria | Art. 2.510 CC | 10 años |
| Prescripción responsabilidad extracontractual | Art. 2.332 CC | 4 años desde acto |
| Prescripción acción de simulación | jurisprudencia | 5 años |
| Aceptación o repudiación herencia | Art. 1.225 CC | sin plazo, pero juez puede fijarlo |
| Inventario solemne | Art. 1.253 CC | dentro del año |
| Acción para demandar legítima | Art. 1.211 CC | 4 años desde apertura |
| Cumplimiento por equivalencia (daños) | Art. 1.489 CC | sin plazo perentorio |

## Skills que orquesta este perfil

- [`diagnostico`](../skills/diagnostico.md) — clasifica el caso.
- [`citas-verificables`](../skills/citas-verificables.md) — citas precisas
  al CC + leyes complementarias.
- [`plazos`](../skills/plazos.md) — prescripción, aceptación herencia,
  rescisión.

## Casos típicos

(Pendientes — Fase 3:)

- Contrato de arrendamiento: cláusulas + protección locatario.
- Compraventa de inmueble: vicios ocultos vs Ley 21.484.
- Sucesión: legítima rigurosa + cuarta de mejoras + libre disposición.
- Rescisión por lesión enorme.
- Sociedad conyugal vs separación: cuándo conviene cambiar.
- Pensión de alimentos: cómputo + retención + GAM + RNDPA.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado civil.
- El CC tiene 2.500+ artículos; el sistema NO los cita todos, sino los
  más invocados. Verificar siempre en BCN.
- Sucesión por causa de muerte tiene reformas históricas (matrimonio
  igualitario, AUC) — revisar fecha de fallecimiento para determinar
  régimen aplicable.
- Para inmuebles, CBR (Conservador de Bienes Raíces) competente determina
  publicidad oponible.

## Conexiones con otros perfiles

- [`perfil-societario`](societario.md) — contratos comerciales,
  responsabilidad del directorio.
- [`perfil-laboral`](laboral.md) — responsabilidad civil del empleador.
- [`perfil-familia`](familia.md) — Tribunales de Familia + procesos
  especiales.
- [`perfil-tributario`](tributario.md) — impuesto a la herencia,
  ganancias de capital.
- [`perfil-penal`](penal.md) — responsabilidad penal con efectos civiles.
