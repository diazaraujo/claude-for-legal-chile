---
ejemplo: privacidad-01-brecha-datos
rama: privacidad
nivel: intermedio
archivos_invocados:
  - chile/normativa/leyes/ley-19628-proteccion-datos.md
  - chile/normativa/leyes/ley-21719-modificacion-lpd.md
  - chile/normativa/leyes/ley-21663-ciberseguridad.md
  - chile/perfiles/privacidad.md
estado_revision: borrador-no-validado
---

# Ejemplo · Brecha de seguridad con datos personales

## Escenario

> Soy CISO de un retailer mediano chileno. Hace 6 horas detectamos
> intrusión a nuestra base de datos de clientes (~250.000 personas). Se
> filtraron: RUT, nombre, email, teléfono, historial de compras. Tarjetas
> de crédito están tokenizadas (no se filtraron). ¿Qué obligaciones
> tenemos? ¿Debemos notificar a alguien hoy?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Verificar con abogado
> de privacidad antes de tomar decisión final.

> **Invoca**: [`perfil-privacidad`](../perfiles/privacidad.md).

> **⚠️ Alerta de volatilidad**: hoy es **2026-05-19**. La **Ley 21.719**
> entra en plena vigencia el **2026-12-01**. Por ahora rige el régimen
> de la **Ley 19.628** original. Pero la práctica recomendada es operar
> bajo el régimen 21.719 desde ya (los reglamentos están en formación
> y los criterios serán retroactivos en ciertos aspectos).

### Régimen aplicable HOY

#### Bajo Ley 19.628 (régimen actual)

**Sin obligación legal expresa** de notificar la brecha a una autoridad
(no hay APDP aún). Pero existen obligaciones derivadas de:

1. **Buena fe del responsable del tratamiento** (Art. 4 Ley 19.628).
2. **Deber de cuidado** del Art. 11 Ley 19.628 (medidas de seguridad).
3. **Derecho del titular** a saber del tratamiento ilegal (Art. 12 ARCO
   básicos).

#### Bajo Ley 21.719 (régimen desde 2026-12-01)

Si la brecha ocurre **después del 1° de diciembre 2026**:

- **Notificación obligatoria a APDP** dentro de **72 horas**.
- **Notificación a los titulares** afectados sin demora indebida.
- **Multas** por incumplimiento de notificación: hasta **UF 20.000**
  (~USD 700.000).

#### Bajo Ley 21.663 (Marco Ciberseguridad)

Si tu empresa es **OIV (Operador de Importancia Vital)** —retailer
mediano probablemente NO lo es, pero verificar listado ANCI—:

- **Notificación inmediata** a CSIRT (ANCI).
- **Reportes posteriores** según evolución.

### Plan de acción inmediato (próximas 24-72 horas)

#### Hora 0-2 — Contención

1. **Aislar el sistema comprometido** sin destruir evidencia.
2. **Resetear credenciales** comprometidas.
3. **Activar el CSIRT interno** (si existe).
4. **Snapshot forense** de los sistemas afectados.
5. **Bitácora detallada** desde el momento de detección.

#### Hora 2-6 — Evaluación

1. **Magnitud confirmada** de la brecha:
   - Cantidad de registros afectados: **250.000**.
   - Tipo de datos: identificadores (RUT, nombre), contacto (email,
     teléfono), conductuales (historial compras).
   - **Datos sensibles** afectados: ⏸ verificar (¿hay datos de salud,
     ideología, etc.?).
   - Datos no afectados: tarjetas (tokenizadas).
2. **Vector de ataque**: identificar cómo entraron (phishing,
   vulnerabilidad explotada, insider, supply chain).
3. **Persistencia**: ¿siguen dentro? ¿hay backdoors?

#### Hora 6-12 — Decisión estratégica

Convocar **comité de crisis** con:

- CEO.
- Gerente Legal.
- CISO (tú).
- Gerente Comunicaciones.
- DPO (si lo hay).
- Asesores externos (legal + forense).

Decisiones clave:

1. ¿Notificar a titulares? **SÍ, fuertemente recomendado** aunque la
   ley actual no obligue.
2. ¿Notificar a autoridades? **Sí, recomendable** (preparar para
   régimen 21.719 + buena fe + reputacional).
3. ¿Notificar a CMF? **Sí si la empresa es supervisada** (no parece tu
   caso retailer, salvo que tenga producto financiero asociado).
4. ¿Comunicación pública? **Sí, transparente** — anticipar al medio.
5. ¿Investigación penal? **Querella** ante MP (delito informático Art.
   2+ Ley 21.663, modifica delitos cómputo Ley 19.223).

#### Hora 12-24 — Notificación a titulares

Email + SMS + publicación en sitio web:

> "Estimado(a) [NOMBRE],
>
> El [FECHA] detectamos un acceso no autorizado a nuestra base de datos
> de clientes que afectó a aproximadamente 250.000 personas, incluyendo
> sus datos de identificación, contacto e historial de compras.
>
> **No se vio comprometida** información de tarjetas de crédito (que
> se almacenan tokenizadas en sistemas separados) ni contraseñas.
>
> Recomendamos las siguientes precauciones:
> - Estar atento a phishing usando tu nombre + email.
> - No abrir links sospechosos que digan venir de nuestra empresa.
> - Verificar movimientos bancarios inusuales.
>
> Hemos: (a) contenido el incidente, (b) notificado a las autoridades,
> (c) iniciado investigación forense, (d) reforzado controles.
>
> Estamos a disposición vía privacidad@[empresa].cl o [800-XXXX].
>
> Atentamente,
> [Empresa]"

#### Hora 24-72 — Notificación a autoridades

##### Ministerio Público (querella por delito informático)

- Querella criminal por Art. 5 Ley 21.663 (acceso indebido a sistemas
  informáticos), Art. 6 (sabotaje informático) según el caso.
- Presentar al Ministerio Público con todos los antecedentes forenses.

##### CPLT (cruce con transparencia, no aplica directamente al sector
privado)

- No procede salvo que sean datos de origen público.

##### CMF (si aplica)

- Verificar si tu empresa es sujeto regulado.

##### Preparación para APDP (futuro 2026-12-01)

- Documentar el incidente con el estándar 21.719.
- Tener el reporte listo si la APDP entra en vigor mientras se procesa.

### Investigación forense (próximas 1-4 semanas)

Contratar firma forense (Deloitte, KPMG, EY, PwC, o especializada):

- **Cadena de eventos**: cuándo entró, qué hizo, cómo salió.
- **Datos efectivamente exfiltrados** (no asumido, sino confirmado).
- **Persistencia**: artefactos malware, backdoors.
- **Vector**: phishing / vulnerabilidad / insider / supply chain.
- **Atribución** (si posible).
- **Reporte forense** que sirva para:
  - Querella penal.
  - Defensa frente a reclamos.
  - Auditoría futura.

### Comunicación con tarjeta financiera

Aunque las tarjetas estaban tokenizadas:

- **Notificar a la red** (Transbank, Webpay).
- **Coordinar con bancos** emisores para monitoreo reforzado.
- **Cruce con Ley 21.234** (fraude tarjetas): si hubo intentos
  posteriores, los clientes tienen protección legal reforzada.

### Reclamaciones de los titulares + exposición legal

#### Acción individual (cada cliente)

- **Recurso de protección** (CPR Art. 20) por vulneración derecho
  privacidad: 30 días desde conocimiento.
- **Habeas data** (Art. 16 Ley 19.628): acción ante Juzgado de Letras
  Civil.
- **Indemnización por daño moral**: vía civil ordinaria.

#### Acción colectiva (Ley 19.496 modificada)

Cruce con **Ley 19.496 (Protección Consumidor)**:

- **SERNAC** puede iniciar **procedimiento colectivo** si afecta a
  consumidores.
- **Acción de clase** posible.
- **Indemnización tasada** por la afectación.

#### Exposición estimada

- **Indemnización individual**: $200.000 - $2.000.000 promedio (varía
  por sensibilidad del dato + impacto efectivo).
- **Multiplicado por 250.000 afectados** (no todos demandarán; típico
  10-20% de los grandes incidentes en Chile).
- **Multa CMF** (si aplica): hasta UF 1M en sectores regulados.
- **Multa SERNAC + cosa juzgada en acción colectiva**: 750 UTM por
  infracción.
- **Reputacional**: difícil cuantificar pero significativo.

**Exposición potencial total**: **$1.000-5.000 millones de pesos** en
casos grandes (ej. Walmart 2014, Cencosud 2019).

### Pasos preventivos post-incidente

- **Auditoría completa** de seguridad informática.
- **Programa de DPO** (Data Protection Officer) si aún no lo tienen.
- **Plan de respuesta a incidentes** documentado.
- **Capacitación** a empleados (phishing es el vector #1).
- **Cifrado** + **tokenización** de TODO dato personal sensible.
- **Penetration testing** anual.
- **Seguro cibernético** (cobertura $1-10M en pólizas estándar
  chilenas).
- **Implementación pre-21.719** del nuevo régimen.

## Red flags activadas (perfil privacidad)

- 🚩 **Brecha de datos no reportada** a APDP (post-2026-12-01): multa
  mayor — preparar régimen ya.
- 🚩 **Acceso a base de datos sin auditoría** rigurosa de logs +
  alertas: vulnera responsabilidad demostrada.
- 🚩 **Recolección de RUT + datos contacto sin política clara de
  retención** + minimización.
- ⚠️ **Reporte forense incompleto** → defensa débil en eventual
  litigio.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado de
  privacidad + ciberseguridad.
- **Hoy (pre-21.719)**: no hay obligación legal de notificación
  estructurada — operar bajo buena fe.
- **Post-2026-12-01**: cumplir 72h notificación a APDP.
- **Coordinación inmediata**: legal + IT + comunicaciones + ejecutivo.
- **Seguros cibernéticos**: revisar póliza para activación inmediata.
- **No destruir evidencia**: aunque sea tentador "limpiar" el sistema,
  podría destruir vector de prueba + investigación + cadena de
  custodia.

## Normas + skills invocados

- [`ley-19628-proteccion-datos`](../normativa/leyes/ley-19628-proteccion-datos.md) —
  régimen vigente hasta 2026-12-01.
- [`ley-21719-modificacion-lpd`](../normativa/leyes/ley-21719-modificacion-lpd.md) —
  régimen futuro + APDP + 72h notificación.
- [`ley-21663-ciberseguridad`](../normativa/leyes/ley-21663-ciberseguridad.md) —
  ANCI + delitos informáticos.
- [`ley-21234-fraude-tarjetas`](../normativa/leyes/ley-21234-fraude-tarjetas.md) —
  cruce.
- [`ley-19496-consumidor`](../normativa/leyes/ley-19496-consumidor.md) —
  acción colectiva.
- [`perfil-privacidad`](../perfiles/privacidad.md) — orquestador.
- [`skill plazos`](../skills/plazos.md) — 72 horas, 30 días recurso
  protección.
- [`skill citas-verificables`](../skills/citas-verificables.md).
