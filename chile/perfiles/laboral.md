---
perfil: laboral
slug: perfil-laboral
ambito: derecho laboral individual y colectivo chileno
capa: orquestador
estado_revision: borrador-no-validado
fuente_corpus: chile/normativa/codigos/codigo-trabajo.md + 13 leyes especiales
ultima_actualizacion: 2026-05-19
---

# Perfil laboral — Claude Legal Chile

> **Orquestador de normativa laboral chilena**. Este perfil no contiene
> derecho sustantivo: invoca el corpus en `chile/normativa/` cuando una
> consulta cae en su ámbito. Para detalle de cada norma, leer el archivo
> referenciado en cada sección.

> **Borrador no validado.** Verificar con abogado laboral antes de
> aplicar en escritos.

## Cuándo se activa este perfil

El sistema invoca este perfil cuando detecta keywords / contextos como:

- Contrato de trabajo (indefinido, plazo fijo, obra/faena, jornadas
  parciales, casa particular, art. 22).
- Despido, indemnización, finiquito.
- Jornada laboral, horas extras, descansos, feriados.
- Subcontratación, suministro de personal, EST.
- Acoso laboral, acoso sexual, "Ley Karin".
- Tutela laboral, fueros (maternal, sindical, médico).
- Sindicalización, negociación colectiva, huelga.
- Accidentes del trabajo, enfermedades profesionales, mutuales.
- Cotizaciones previsionales, AFP, AFC, seguro cesantía.
- Inclusión laboral (discapacidad, art. 157 bis).
- Teletrabajo.
- Reducción de jornada 40 horas (Ley 21.561).

Si la consulta no encaja, el perfil deriva al de la rama correspondiente
o declara "fuera de mi ámbito".

## Normas que invoca este perfil

### Norma matriz

- [`codigo-trabajo`](../normativa/codigos/codigo-trabajo.md) — DFL 1/2002,
  texto refundido. **Eje del derecho laboral chileno.** Libro I individual,
  Libro II protección, Libro III sindical + negociación, Libro IV
  jurisdicción, Libro V procedimiento.

### Laboral individual

- [`ley-21643-acoso-laboral`](../normativa/leyes/ley-21643-acoso-laboral.md) —
  Ley Karin (2024). **Verificar primero** en toda consulta de acoso.
- [`ley-21561-reduccion-jornada`](../normativa/leyes/ley-21561-reduccion-jornada.md) —
  40 horas, vigencia escalonada hasta 2028. **Alerta de volatilidad.**
- [`ley-21220-teletrabajo`](../normativa/leyes/ley-21220-teletrabajo.md) —
  régimen del teletrabajo (post-COVID consolidado).
- [`ley-21015-inclusion-laboral`](../normativa/leyes/ley-21015-inclusion-laboral.md) —
  1% inclusión discapacidad (empresas ≥100 trabajadores).
- [`ley-20123-subcontratacion`](../normativa/leyes/ley-20123-subcontratacion.md) —
  régimen de subcontratación + EST. **Solidaridad/subsidiariedad.**

### Seguridad social y riesgos

- [`ley-16744-accidentes-trabajo`](../normativa/leyes/ley-16744-accidentes-trabajo.md) —
  accidentes y enfermedades profesionales. Mutuales (ACHS, IST, Mutual de
  Seguridad), CTC.
- [`ley-19728-seguro-cesantia`](../normativa/leyes/ley-19728-seguro-cesantia.md) —
  AFC, cuenta individual + Fondo Solidario.
- [`dl-3500-pensiones`](../normativa/leyes/dl-3500-pensiones.md) — AFP,
  pensión de vejez/invalidez/sobrevivencia.

### Laboral colectivo

- [`ley-20940-relaciones-laborales`](../normativa/leyes/ley-20940-relaciones-laborales.md) —
  Reforma Laboral 2016: sindicatos, negociación colectiva, huelga,
  servicios mínimos, pacto sobre condiciones especiales.

### Procesal laboral

- [`ley-20022-tribunales-trabajo`](../normativa/leyes/ley-20022-tribunales-trabajo.md) —
  Juzgados de Letras del Trabajo (JTL) + JCLP + Sala Cuarta CS.
- [`ley-20087-procedimiento-laboral`](../normativa/leyes/ley-20087-procedimiento-laboral.md) —
  procedimiento oral, tutela laboral, monitorio.

### Funcionarial (régimen aparte)

Si la consulta es sobre **funcionario público**, derivar a:

- [`ley-18834-estatuto-administrativo`](../normativa/leyes/ley-18834-estatuto-administrativo.md) —
  EA general (administración central + servicios públicos).
- [`ley-18883-estatuto-administrativo-municipal`](../normativa/leyes/ley-18883-estatuto-administrativo-municipal.md) —
  EAM (funcionarios municipales).
- [`ley-19070-estatuto-docente`](../normativa/leyes/ley-19070-estatuto-docente.md) —
  docentes municipales / SLEP / particular subvencionado.
- [`ley-19378-aps-municipal-salud`](../normativa/leyes/ley-19378-aps-municipal-salud.md) —
  funcionarios APS municipal.

El **Código del Trabajo NO aplica** a funcionarios públicos (salvo
honorarios reconducidos por jurisprudencia laboral).

### Capacitación + empleo

- [`ley-19518-sence-capacitacion`](../normativa/leyes/ley-19518-sence-capacitacion.md) —
  SENCE, franquicia tributaria, OTEC/OTIC, programas estatales.

## Red flags laborales (activación automática)

Al revisar contratos o casos, el sistema marca estas señales:

### En contrato de trabajo individual

1. **Cláusula que renuncia a derechos del trabajador** — nula (Art. 5
   inc. 2 CT).
2. **Plazo fijo sucesivo** después del 2° contrato → indefinido por ley.
3. **"Acuerdo amistoso" sin finiquito notarial** → no extingue derechos
   indemnizatorios.
4. **Honorarios con vínculo de subordinación** → reconducción a contrato
   laboral con indemnización + cotizaciones retroactivas.
5. **Trabajador "art. 22" en cargo sin facultades reales** → riesgo de
   reclamo por horas extras.
6. **Cláusula de no competencia post-contractual** sin pago de
   compensación → discusión jurisprudencial; usualmente inejecutable.
7. **Multa contractual al trabajador** → inválida; sólo proceden las que
   están en el reglamento interno y son menores al 25% de remuneración
   diaria.
8. **Reglamento interno no notificado** o sin depósito en DT → no
   oponible al trabajador.

### En despido

1. **Despido verbal o por correo informal** → vicia el procedimiento;
   reclamable por despido injustificado.
2. **Despido durante fuero** (maternal, sindical, candidato concejal/
   diputado, etc.) → requiere desafuero judicial previo.
3. **Carta de despido sin causal específica o sin hechos** → causal
   improcedente por defecto; despido injustificado.
4. **Despido por "necesidades de la empresa" cuando se contrata
   reemplazante** en mismo cargo → riesgo de despido encubierto.
5. **Acoso laboral previo no investigado** → tutela laboral por
   represalia.
6. **No pago de finiquito al término del contrato** → cláusula penal
   automática (Art. 162 CT — "Bullet Train").

### En jornada

1. **Jornada superior a 45h/semana** sin pacto art. 22 ni pacto colectivo
   válido → horas extra obligatorias.
2. **Promedio mensual sin libro de control** → presunción a favor del
   trabajador en juicio.
3. **Trabajadores con "jornada parcial" pero con asignaciones de
   tiempo completo** → reclasificación + diferencias.
4. **Régimen de trabajo "promediado" sin autorización DT** → nulo.
5. **40 horas: empresa NO ajusta jornada según calendario Ley 21.561** →
   posible cobro retroactivo.

### En salud y seguridad

1. **Accidente del trabajo no reportado a mutual dentro de 24 horas** →
   sanción + complicaciones probatorias.
2. **Trabajador con licencia médica reiterada por estrés laboral** →
   posible enfermedad profesional + Ley Karin.
3. **Cargo de alto riesgo sin elementos de protección personal (EPP)
   suministrados** → multa SUSESO + responsabilidad civil.

### En negociación colectiva

1. **Despido masivo durante negociación o huelga** → atentado contra la
   libertad sindical.
2. **"Servicios mínimos" definidos unilateralmente por la empresa** →
   nulos; deben ser fijados de común acuerdo o por la DT/IT.
3. **Reemplazo de huelguistas** → prohibido (Ley 20.940).

## Plazos críticos laborales

El sistema invoca el skill [`plazos`](../skills/plazos.md) para todos
los cómputos, pero estos son los más usados en consultas laborales:

| Plazo | Norma | Días | Tipo |
|---|---|---|---|
| Reclamo despido injustificado | Art. 168 CT | 60 | hábiles desde separación |
| Aviso despido necesidades empresa | Art. 161 CT | 30 | corridos |
| Aviso despido conductas (Art. 160) | — | inmediato | — |
| Finiquito a la vista del trabajador | Art. 177 CT | 10 | hábiles desde término |
| Reclamación de despido (DT) | Reglamento | 30 | hábiles |
| Demanda tutela laboral | Art. 486 CT | 60 | hábiles desde vulneración |
| Inicio investigación Ley Karin | Ley 21.643 | 3 | hábiles desde denuncia |
| Cierre investigación Ley Karin | Ley 21.643 | 30 | hábiles totales |
| Reclamo accidente trabajo (mutual) | Art. 77 Ley 16.744 | 5 | hábiles |
| Apelación SUSESO | — | 90 | hábiles |

## Skills que orquesta este perfil

- [`diagnostico`](../skills/diagnostico.md) — clasifica la consulta y
  decide si invocar este perfil.
- [`citas-verificables`](../skills/citas-verificables.md) — para citar
  artículo + Código del Trabajo + ley especial.
- [`plazos`](../skills/plazos.md) — todo cómputo de plazo laboral.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) — si
  la consulta laboral involucra MPD (Ley 20.393 con Ley 21.643 como
  delito atribuible).

## Casos típicos que este perfil resuelve

Ejemplos resueltos en [`chile/ejemplos/`](../ejemplos/):

- [`laboral-01-plazo-investigacion-karin.md`](../ejemplos/laboral-01-plazo-investigacion-karin.md) —
  plazo de investigación bajo Ley Karin.

(Pendientes — alta prioridad para Fase 3:)

- Reclasificación honorarios → laboral.
- Despido durante fuero maternal.
- Subcontratación con responsabilidad solidaria vs subsidiaria.
- 40 horas escalonadas: ajuste de jornada.
- Negociación colectiva: plazos + servicios mínimos.

## Disclaimers

- **Borrador no validado**. Pendiente revisión por abogado laboral
  habilitado en Chile.
- Convenios colectivos específicos pueden modificar reglas generales.
- Jurisprudencia laboral muy dinámica (Corte Suprema, Cuarta Sala).
- Convenios OIT ratificados por Chile (87, 98, 111, 169) son
  operativamente relevantes.
- Para funcionarios públicos NO aplica este perfil (ver "Funcionarial"
  arriba).

## Conexiones con otros perfiles

- [`perfil-civil`](civil.md) — responsabilidad civil del empleador
  (cuando cruza con accidente del trabajo Art. 69 Ley 16.744).
- [`perfil-tributario`](tributario.md) — cotizaciones, retenciones de
  impuestos sobre remuneraciones.
- [`perfil-societario`](societario.md) — cuando la consulta involucra
  responsabilidad del directorio por acoso (Ley Karin + MPD).
- [`perfil-penal`](penal.md) — delitos contra trabajadores (Ley 21.595,
  Ley 20.393).
