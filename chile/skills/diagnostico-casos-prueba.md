---
skill: diagnostico-casos-prueba
slug: diagnostico-casos-prueba
proposito: validar que el sistema activa el perfil correcto + invoca normas correctas
capa: testing
estado_revision: borrador-no-validado
relacionada_per:
  - diagnostico
  - citas-verificables
  - plazos
ultima_actualizacion: 2026-05-19
---

# Casos de prueba del diagnóstico

> Conjunto canónico de casos para validar el funcionamiento del
> diagnóstico. Cada caso declara: consulta + diagnóstico esperado
> (perfil + normas + plazo + red flags). Sirve como **test fixture**
> manual y futuro CI.

## Cómo usar este archivo

### Modo manual (humano)

1. Cargar el corpus en Claude Code / Claude.ai.
2. Para cada caso, presentar la consulta verbatim.
3. Comparar la respuesta del sistema con el diagnóstico esperado.
4. Marcar PASS / FAIL / PARTIAL.

### Modo automatizado (futuro CI)

Un script que:

1. Lea este archivo + extraiga los `<consulta>` y `<esperado>` de cada caso.
2. Llame al sistema con la consulta.
3. Verifique que la respuesta menciona el perfil + normas + plazos + red flags
   esperados.
4. Reporte cobertura + falsos negativos + falsos positivos.

## Estructura de un caso

```
### Caso N — <título corto>

**Consulta**:
> <verbatim del usuario>

**Diagnóstico esperado**:
- Perfil: <slug>
- Normas: <lista>
- Plazo crítico: <descripción>
- Red flags: <lista>
- Nivel: <básico | intermedio | avanzado>
- Notas: <observaciones, edge cases, derivaciones>
```

---

## Casos por rama (1 por rama mínimo)

### Caso 1 — Laboral: investigación Ley Karin

**Consulta**:
> Una empleada me informa que su jefe directo la ha humillado en
> reuniones durante dos meses. ¿Cuánto plazo tengo para iniciar la
> investigación interna?

**Diagnóstico esperado**:
- Perfil: `laboral`
- Normas: `ley-21643-acoso-laboral` (eje), `codigo-trabajo` (Art. 184+),
  `ley-16744-accidentes-trabajo` (cruce salud).
- Plazo crítico: **3 días hábiles** desde recepción formal de la denuncia
  para iniciar investigación (Ley 21.643).
- Red flags: investigación interna obligatoria del empleador; reporte a
  Mutual si aplica; comunicación a DT; medidas de resguardo previas.
- Nivel: básico.

---

### Caso 2 — Societario: diseñar MPD post-Ley 21.595

**Consulta**:
> Mi empresa industrial mediana (UF 800.000 ventas) ganó licitación
> MOP que exige acreditar MPD. ¿Qué incluye un MPD válido + cuánto
> demora certificarlo?

**Diagnóstico esperado**:
- Perfil: `societario`
- Normas: `ley-20393-rppj`, `ley-21595-delitos-economicos` (catálogo
  ampliado), `ley-21643-acoso-laboral` (delito atribuible),
  `ley-19913-lavado-activos` (UAF).
- Plazo crítico: ~10 meses para certificación inicial (cronograma 6
  fases).
- Red flags: EP autónomo; matriz de riesgos no copiada; canal denuncias
  con garantías; capacitación documentada; auditoría anual.
- Nivel: intermedio.

---

### Caso 3 — Civil: vicios ocultos en inmueble

**Consulta**:
> Mi clienta compró un departamento hace 8 meses con crédito hipotecario.
> Descubrió humedad estructural + sistema eléctrico deficiente. ¿Qué
> acciones tiene?

**Diagnóstico esperado**:
- Perfil: `civil`
- Normas: `codigo-civil` (Art. 1857+ vicios redhibitorios),
  `ley-21484-compraventa-inmuebles` (responsabilidad solidaria),
  `ley-19496-consumidor` (cruce LPC).
- Plazo crítico: 6 meses redhibitoria (probablemente prescrita), 1 año
  quanti minoris, 5 años Ley 21.484 desde descubrimiento.
- Red flags: acción redhibitoria CC prescrita; priorizar Ley 21.484;
  vendedor + corredora + tasador + banco solidariamente responsables.
- Nivel: intermedio.

---

### Caso 4 — Tributario: IVA servicios profesionales por SpA

**Consulta**:
> Tengo SpA de consultoría que antes facturaba sin IVA. Mi contador
> dice que ahora debo cobrar 19%. ¿Es obligatorio?

**Diagnóstico esperado**:
- Perfil: `tributario`
- Normas: `ley-21420-reduccion-exenciones` (eje), `dl-825-iva` (Art. 8
  letra G modificado), `dl-824-renta`.
- Plazo crítico: facturación afecta a IVA desde 1° enero 2023; declaración
  F29 día 12 de cada mes; F22 abril año siguiente.
- Red flags: emisión sin IVA = infracción Art. 97 CT; opción A
  (disolver), B (mantener + trasladar), C (mixta), D (no actuar = riesgo
  penal Art. 97 N° 4 CT).
- Nivel: intermedio.

---

### Caso 5 — Penal: formalización por delito tributario

**Consulta**:
> Mi cliente es gerente de empresa que será formalizada por delito
> tributario doloso. Empresa tiene MPD certificado. ¿Hay riesgo de
> prisión preventiva?

**Diagnóstico esperado**:
- Perfil: `penal`
- Normas: `codigo-procesal-penal` (Art. 140 PP), `codigo-tributario`
  (Art. 97 N° 4), `codigo-penal` (Art. 470 N° 11 modificado),
  `ley-21595-delitos-economicos`, `ley-20393-rppj` (MPD como defensa).
- Plazo crítico: 2 años investigación formalizada; 10 días acusación;
  10 días recurso nulidad; 90 días reclamo tributario paralelo.
- Red flags: prisión preventiva poco probable en delito económico con
  arraigo; activar MPD para defensa de PJ; coordinación frente
  tributario paralelo; análisis de salidas alternativas (SCP,
  abreviado).
- Nivel: avanzado.

---

### Caso 6 — Familia: divorcio matrimonio igualitario

**Consulta**:
> Mi clienta se casó con su esposa hace 4 años post-Ley 21.400. Quiere
> divorciarse. No hicieron capitulaciones. ¿Qué régimen patrimonial
> tienen?

**Diagnóstico esperado**:
- Perfil: `familia`
- Normas: `ley-21400-matrimonio-igualitario`, `ley-19947-matrimonio-civil`
  (Art. 55), `ley-19968-tribunales-familia`, `codigo-civil`.
- Plazo crítico: 1 año separación efectiva (mutuo acuerdo) o 3 años
  (unilateral); mediación prejudicial obligatoria 60 días.
- Red flags: por defecto separación total de bienes post-21.400; sin
  liquidación de sociedad; eventual copropiedad por compras conjuntas;
  bienes familiares declarados; compensación económica si aplica.
- Nivel: intermedio.

---

### Caso 7 — Administrativo: cese contrata + confianza legítima

**Consulta**:
> Funcionaria del MINSAL a contrata desde 2018 (7 años). El 28 de
> diciembre 2024 le notificaron que no renuevan su contrata. ¿Tiene
> acción?

**Diagnóstico esperado**:
- Perfil: `administrativo`
- Normas: `ley-18834-estatuto-administrativo` (Art. 10 contrata),
  `ley-19880-procedimiento-administrativo` (Art. 11 motivación, Art. 59
  reposición), `ley-10336-cgr`.
- Plazo crítico: 5 días reposición; 30 días recurso protección; 60 días
  silencio.
- Red flags: doctrina confianza legítima (CS post-2018); falta de
  motivación = vicio Art. 11 Ley 19.880; vías paralelas
  (reposición + dictamen CGR + protección + nulidad).
- Nivel: intermedio.

---

### Caso 8 — Privacidad: brecha de seguridad de datos

**Consulta**:
> Soy CISO de retailer. Hace 6 horas detectamos intrusión que filtró
> 250.000 registros con RUT, nombre, email. Tarjetas tokenizadas no
> se filtraron. ¿Qué obligaciones tenemos?

**Diagnóstico esperado**:
- Perfil: `privacidad`
- Normas: `ley-19628-proteccion-datos` (régimen vigente),
  `ley-21719-modificacion-lpd` (régimen futuro 2026-12-01),
  `ley-21663-ciberseguridad`, `ley-19496-consumidor` (acción colectiva).
- Plazo crítico: hoy sin obligación legal expresa; post-2026-12-01:
  72h a APDP + notificación titulares; 30 días recurso protección.
- Red flags: notificar voluntariamente (buena fe + reputacional);
  querella por delito informático; coordinación con CMF si aplica;
  preparación para régimen 21.719; investigación forense.
- Nivel: intermedio.

---

### Caso 9 — Concursal: empresa insolvente

**Consulta**:
> Empresa manufacturera con activos $800M, pasivos $1.200M, ventas en
> caída. 35 trabajadores. ¿Reorganización o liquidación?

**Diagnóstico esperado**:
- Perfil: `concursal`
- Normas: `ley-20720-concursal` (eje), `ley-18046-sociedades-anonimas`
  (responsabilidad directores), `codigo-trabajo` (superprivilegio
  laboral), `codigo-civil` (Art. 2470+ prelación).
- Plazo crítico: período sospechoso 1-2 años retrospectivo; 2 años
  acción revocatoria; 30-90 días reorganización.
- Red flags: Art. 41 Ley 20.720 responsabilidad personal directores si
  continúan sin acción; cruce con Ley 21.595 (delitos concursales);
  prelación trabajadores + previsional + tributario antes que
  proveedores quirografarios; 4 condiciones para reorganización viable.
- Nivel: avanzado.

---

## Casos de cruce multi-rama (validación de derivación)

### Caso 10 — Acoso laboral + RPPJ + tributario

**Consulta**:
> En mi empresa surgió denuncia interna de acoso laboral grave.
> Tenemos MPD certificado pero el caso es del CEO. ¿Cómo procedemos?

**Diagnóstico esperado**:
- Perfil: `laboral` (primario), con derivación a `societario` + `penal`.
- Normas: `ley-21643-acoso-laboral`, `ley-20393-rppj` (Karin como
  delito atribuible), `ley-21595-delitos-economicos`, perfil
  `compliance-corporativo`.
- Plazo crítico: 3 días investigación + 30 días total Ley Karin;
  comunicación obligatoria a DT.
- Red flags: ⚠️ conflicto interno con el EP si reporta al CEO investigado;
  el MPD debe activar protocolo de emergencia; rol del directorio.
- Nivel: avanzado.

---

### Caso 11 — Divorcio + bienes inmuebles + tributario

**Consulta**:
> Mi clienta y su marido tienen propiedades en sociedad conyugal. Se
> divorcian. ¿Cómo se reparten las propiedades + cuál es el costo
> tributario?

**Diagnóstico esperado**:
- Perfil: `familia` (primario), con derivación a `civil` + `tributario`.
- Normas: `codigo-civil` (sociedad conyugal), `ley-19947-matrimonio-civil`,
  `ley-19968-tribunales-familia`, `dl-824-renta` (ganancias de capital),
  `ley-17235-impuesto-territorial`.
- Plazo crítico: división judicial / arbitral sin plazo perentorio.
- Red flags: liquidación sociedad conyugal con activos = sin impuesto a
  ganancias de capital (norma específica); cambio de avalúo
  contribuciones; compensación económica si aplica.
- Nivel: intermedio.

---

### Caso 12 — Despido + libre competencia + datos

**Consulta**:
> Despedí a mi gerente comercial. Se llevó base de clientes + ahora
> trabaja para competidor directo. ¿Qué acciones?

**Diagnóstico esperado**:
- Perfil: `laboral` (primario), con derivación a `societario` +
  `privacidad` + `civil`.
- Normas: `codigo-trabajo` (deberes fidelidad), `ley-20169-competencia-desleal`,
  `ley-19628-proteccion-datos` (base clientes como dato personal),
  `codigo-penal` (revelación secreto industrial).
- Plazo crítico: 2 años prescripción competencia desleal; depende
  contractual cláusula no competencia.
- Red flags: revisar cláusula contractual (válida solo con compensación);
  acción civil por daños; análisis penal por sustracción de información.
- Nivel: avanzado.

---

## Casos edge (validar manejo de fronteras)

### Caso 13 — Consulta ambigua

**Consulta**:
> Tengo un problema con mi vecino. ¿Qué hago?

**Diagnóstico esperado**:
- Perfil: **ninguno activado** sin más contexto.
- Sistema debe **pedir clarificación**: ¿problema de qué tipo (ruido,
  límites, copropiedad, agresión, daño a propiedad)?
- Después de clarificación → derivar a `civil` (vecindad,
  copropiedad), `familia` (VIF si hay violencia), `penal` (lesiones,
  amenazas).
- Nivel: básico (test de robustez).

---

### Caso 14 — Fuera de scope: derecho indígena

**Consulta**:
> Soy comunero de comunidad mapuche. El Estado quiere imponer un
> proyecto minero en territorio ancestral. ¿Qué puedo hacer?

**Diagnóstico esperado**:
- Perfil: **ninguno** (fuera de scope v1).
- Sistema debe declarar la limitación + derivar.
- Mencionar referencias: Convenio 169 OIT, Ley 19.253, SEIA con consulta
  indígena (Decreto 66/2014), Defensoría Mapuche, CONADI.
- Nivel: básico (test de declaración de scope).

---

### Caso 15 — Consulta en idioma distinto

**Consulta** (inglés):
> My company in Chile wants to terminate an employee. What's the
> indemnification?

**Diagnóstico esperado**:
- Sistema debe responder **en español** (idioma de operación del corpus).
- Perfil: `laboral`.
- Normas: `codigo-trabajo` (Art. 161+ causales, Art. 163 indemnización
  por años de servicio).
- Plazo crítico: 60 días reclamo (Art. 168).
- Red flags: causal específica; tope 90 UF mensual; máximo 11 años;
  recargo 50-80% si improcedente.
- Nivel: básico (test de idioma + manejo intercultural).
- Notas: el sistema **no debe** aplicar régimen de "employment at will"
  norteamericano.

---

### Caso 16 — Consulta sobre norma derogada

**Consulta**:
> ¿Qué dice el DL 600 sobre la inversión extranjera?

**Diagnóstico esperado**:
- Sistema debe declarar que el **DL 600 fue derogado** (post 2016 con
  régimen transitorio).
- Derivar al régimen actual: tratamiento general LIR, convenios
  bilaterales, Estatuto de Inversión Extranjera moderno.
- Mencionar régimen transitorio si el inversionista ya tenía contratos.
- Nivel: intermedio (test de validación de vigencia).

---

### Caso 17 — Norma con vigencia escalonada

**Consulta**:
> ¿Qué obligaciones tendré bajo la nueva ley de protección de datos?

**Diagnóstico esperado**:
- Sistema debe **distinguir** régimen actual (Ley 19.628) vs régimen
  futuro (Ley 21.719 desde **2026-12-01**).
- Activar **alerta de volatilidad**: la APDP aún no opera.
- Pedir fecha de la consulta para distinguir respuesta.
- Si la consulta es para preparación post-vigencia: cubrir régimen
  21.719 completo.
- Si es para hoy: régimen 19.628 + recomendación de adecuación
  anticipada.
- Nivel: intermedio.

---

### Caso 18 — Consulta puramente teórica / académica

**Consulta**:
> ¿Cuál es la diferencia entre nulidad absoluta y relativa en el
> Código Civil chileno?

**Diagnóstico esperado**:
- Perfil: `civil`.
- Normas: `codigo-civil` (Art. 1681+).
- Plazo crítico: 4-10 años prescripción según tipo.
- Red flags: respuesta debe ser **didáctica + correcta** (clasificación,
  causales, plazos, efectos).
- Sistema debe declarar que es respuesta **conceptual** (no aplicada a
  caso concreto); recomendar consulta con abogado si hay caso.
- Nivel: básico-intermedio (test académico).

---

### Caso 19 — Conflicto entre perfiles

**Consulta**:
> Soy alcalde. La municipalidad despidió a un funcionario que después
> demandó por confianza legítima. ¿Me defendia?

**Diagnóstico esperado**:
- Perfil **primario**: `administrativo` (régimen del funcionario
  municipal + Estatuto Municipal).
- Cruce con perfil `laboral` solo para análisis comparativo (no aplica
  CT a funcionario municipal en régimen estatutario).
- Normas: `ley-18883-estatuto-administrativo-municipal`,
  `ley-19880-procedimiento-administrativo`, `ley-18695-loc-municipalidades`,
  `ley-10336-cgr`.
- Plazo crítico: ya en juicio (defensa, no demandar).
- Red flags: doctrina confianza legítima aplica también al EAM; defensa
  necesita acreditar causal específica + motivación; coordinación con
  CGR.
- Nivel: avanzado.

---

### Caso 20 — Consulta con dato sensible

**Consulta**:
> Soy abogada de víctima de delito sexual. Tiene 16 años. ¿Cómo
> manejamos la entrevista?

**Diagnóstico esperado**:
- Perfil: `penal` + `familia` (cruce NNA).
- Normas: `ley-21057-entrevista-videograbada` (eje, NNA víctimas),
  `ley-21430-garantias-nna`, `codigo-procesal-penal`,
  `ley-21067-defensoria-ninez`.
- Plazo crítico: la entrevista única + videograbada debe ser **antes**
  de cualquier interacción con MP; coordinación con CAVAS.
- Red flags: **NO repetir entrevista**; protocolo Ley 21.057 obligatorio;
  apoyo psicosocial obligatorio; cruce con derecho de la víctima a
  reparación.
- Nivel: avanzado (test de protección NNA + cruce multidisciplinario).

---

## Métricas de evaluación

Para cada caso, el sistema debe:

| Métrica | Pase si |
|---|---|
| Perfil correcto activado | El sistema invoca el perfil esperado |
| Normas correctas | Cita las normas listadas (≥80% match) |
| Plazo crítico | Identifica el plazo (sin alucinarlo) |
| Red flags | Menciona ≥60% de las red flags listadas |
| Sin alucinación | No inventa normas, fallos o instituciones |
| Disclaimer | Indica estado de revisión + sugiere abogado |

Calificación:
- **PASS**: 5 de 6 métricas cumplidas.
- **PARTIAL**: 3-4 métricas cumplidas.
- **FAIL**: 2 o menos.

## Próximas adiciones (Fase 4)

Casos pendientes para ampliar cobertura:

- DDHH (querella imprescriptible).
- Migración (Ley 21.325 + caso de residencia denegada).
- Salud (AUGE/GES + reclamo cobertura).
- Educación (SLEP + reclamo docente).
- Minería (royalty + impugnación).
- Aguas (DAA + caducidad post-Ley 21.435).
- Aborto en 3 causales (consulta operativa).
- Pesca (cuota + impugnación).
- AUC vs matrimonio (decisión).
- Pensión alimenticia (mora + GAM).

## Disclaimers

- **Borrador no validado**: los diagnósticos esperados son la
  formulación del autor del sistema; validar con abogados de cada rama
  si los criterios + normas son los óptimos.
- **Vigencia normativa**: las normas citadas pueden tener vigencia
  escalonada (ver tabla de alertas de volatilidad en `chile/CLAUDE.md`).
- **Casos de prueba evolucionan**: agregar casos cuando se detecten
  falsos negativos / positivos del sistema en uso real.

## Mantenimiento

- Cuando un perfil de rama se modifica, revisar los casos asociados.
- Cuando se agrega una nueva norma capa 3, agregar al menos un caso si
  cubre área nueva.
- Cuando un usuario reporta error de diagnóstico, agregar el caso como
  test de regresión.
- Verificar al menos trimestralmente si las normas siguen vigentes.

> Ver `chile/MARCADORES.md` para vocabulario controlado.
> Ver `chile/perfiles/README.md` para los 9 perfiles activables.
