---
ejemplo: societario-02-conflicto-interes-director
rama: societario
nivel: avanzado
archivos_invocados:
  - chile/normativa/leyes/ley-18046-sociedades-anonimas.md
  - chile/normativa/leyes/ley-21314-gobierno-corporativo.md
  - chile/normativa/leyes/ley-21000-cmf.md
estado_revision: borrador-no-validado
---

# Ejemplo · Conflicto de interés del director en operación con parte relacionada

## Escenario

> Soy director de una SA abierta. La empresa está por aprobar la compra
> de una participación en una sociedad inmobiliaria. Yo soy accionista
> del 8% de esa sociedad inmobiliaria a través de un trust familiar
> (no aparece directamente a mi nombre). ¿Tengo que declarar el
> conflicto? ¿Qué pasa si voto sin declararlo?

## Respuesta del sistema (con el corpus cargado)

> **Análisis basado en borradores no validados.** Verificar con abogado
> societario antes de tomar posición en sesión de directorio.

> **Invoca**: [`perfil-societario`](../perfiles/societario.md).

### Régimen aplicable

Las **Operaciones con Partes Relacionadas (OPR)** en SA abiertas se rigen
por el **Título XVI de la Ley 18.046** (Sociedades Anónimas), reforzado
por la **Ley 21.314 (Gobierno Corporativo SA abiertas, 2021)**.

El concepto de "parte relacionada" es **amplio** y **funcional** —
no se limita a la titularidad directa. Incluye:

> **[VERIFICAR]** Texto Art. 146 Ley 18.046: "Son operaciones con partes
> relacionadas… aquellas en que el director, el ejecutivo principal, el
> accionista controlador o sus relacionados, tengan **interés** directo
> o indirecto…"

### ¿Tu trust familiar te genera "interés"?

**Sí, casi con certeza.** La doctrina de la CMF (sucesora de la SVS) ha
sostenido reiteradamente que:

1. **Beneficiario** de un trust = parte relacionada respecto al director.
2. **Aún con titularidad jurídica formal en el trust**, el "interés"
   económico del director subsiste.
3. **Participación indirecta** ≥ 5% genera presunción de interés
   relevante.
4. La **CMF** ha sancionado casos con porcentajes incluso menores cuando
   hay control efectivo o influencia significativa.

Tu **8% a través de trust familiar** cae **claramente** dentro del
concepto de "interés indirecto".

### Obligaciones del director con conflicto de interés

#### 1. **Declarar el conflicto** (Art. 147 Ley 18.046)

- **Por escrito**, al **directorio en pleno** antes de la votación.
- **Identificar** la naturaleza + cuantía del interés.
- **Acreditar** la operación con parte relacionada.
- **Dejar constancia en acta**.

#### 2. **Abstenerse de votar** la operación

- **No participar** en la discusión + votación específica.
- **Salir de la sala** durante la deliberación (no obligatorio pero
  recomendado para evitar influencia).
- **Dejar constancia en acta** del retiro voluntario.

#### 3. **Información** al accionariado + a la CMF

- **OPR significativa** debe ser informada como **Hecho Esencial** vía
  Norma de Carácter General CMF.
- **Identificación** del director con conflicto + su interés.
- **Términos + condiciones de la operación**.
- **Informe del Comité de Directores** (ver §4).

#### 4. **Comité de Directores** (Art. 50 bis Ley 18.046)

- En SA abierta, el **Comité de Directores** debe **pronunciarse
  previamente** sobre la OPR.
- Compuesto por **3 directores** mayoritariamente **independientes**.
- Emite **informe motivado** sobre si la operación se realiza en
  **condiciones de mercado** + es **acorde con el interés social**.
- **Mayoría de 2/3** del directorio en pleno + voto a favor del Comité
  para aprobar.

#### 5. **Derecho de retiro** del accionista minoritario

Si la OPR no se realiza en condiciones de mercado, los accionistas
minoritarios pueden ejercer **derecho de retiro** (Art. 69 Ley 18.046)
dentro de **30 días** desde la junta que apruebe la operación.

### Si votas sin declarar el conflicto: consecuencias

#### Civiles + administrativas

- **Nulidad de la decisión** del directorio (Art. 148 Ley 18.046).
- **Responsabilidad civil personal** del director: indemnización por
  perjuicios a la sociedad + a los accionistas minoritarios.
- **Acción social de responsabilidad** o **acción individual** según el
  daño.

#### Frente a la CMF

- **Multa** hasta **UF 1.000.000** (~USD 35M) en casos graves.
- **Sanciones accesorias**: inhabilitación para ejercer en cargos
  similares.
- **Reporte público** del caso (sancionatorio + reputacional).

#### Frente a la Ley 21.314 (whistleblowing)

- Si un empleado o ejecutivo reporta el conflicto no declarado vía canal
  de denuncia: la SA abierta tiene obligación de investigar.
- **No investigación** o **investigación deficiente** + **represalia**
  al denunciante: nuevas sanciones.

#### Penales (potencial)

- **Administración desleal** (Art. 470 N° 11 CP, modificado por Ley
  21.595): pena de presidio + multa + inhabilitación.
- **Lavado** (si la operación oculta origen de fondos).

### Procedimiento operativo recomendado HOY

#### Paso 1 — Declaración inmediata por escrito

Email + carta certificada al Presidente del Directorio:

> "Estimados:
>
> En relación con la propuesta de adquisición de participación en
> [SOCIEDAD INMOBILIARIA] que se discutirá en la sesión de directorio del
> [FECHA], declaro lo siguiente:
>
> Soy beneficiario de un **trust familiar** que detenta el 8% del capital
> de la mencionada sociedad inmobiliaria. Conforme al Art. 146 y 147 de
> la Ley 18.046 + Norma de Carácter General CMF [#], esta circunstancia
> me genera **interés indirecto** en la operación.
>
> Por tal razón, **me declaro impedido de participar en la deliberación
> y votación** sobre la materia, conforme al Art. 147 Ley 18.046.
>
> Solicito que se deje **expresa constancia en acta** de esta
> declaración y de mi retiro durante la discusión y votación.
>
> Sin perjuicio, manifiesto mi disposición a entregar toda la
> información que el Comité de Directores requiera para evaluar la
> operación en condiciones de mercado.
>
> Atentamente,
> [DIRECTOR]"

#### Paso 2 — Comité de Directores

Solicitar al Presidente del Comité de Directores:

- **Análisis técnico** de la operación con tasación independiente.
- **Comparación** con condiciones de mercado.
- **Informe motivado** que se acompañará al acta.

#### Paso 3 — Hecho Esencial a CMF

Coordinar con el área Legal + Gobierno Corporativo:

- Redactar el Hecho Esencial conforme a NCG 30.
- Identificar director con conflicto (tú).
- Identificar términos + condiciones.

#### Paso 4 — Sesión del directorio

- No asistes a la discusión + votación de la OPR.
- Sí asistes al resto de la sesión.
- El acta refleja claramente tu abstención.

#### Paso 5 — Voto en junta de accionistas (si aplica)

Si la operación es relevante (5% o más del activo), también requiere
junta de accionistas. Como director, no puedes "instruir" voto, pero
puedes:

- Manifestar tu abstención en la propia junta.
- Documentar tu posición.
- En NUNCA caso utilizar acciones que posees como pequeño accionista
  para votar en sentido determinado de la OPR.

## Análisis de riesgo si no actúas según el procedimiento

| Riesgo | Probabilidad | Impacto |
|---|---|---|
| Sanción CMF por no declarar | **ALTA** | UF 100k - 1M + reputacional |
| Nulidad de la decisión del directorio | media | reputacional + operacional |
| Acción civil por accionistas | media | económica + tiempo |
| Investigación interna whistleblowing | **ALTA** (post-21.314) | reputacional |
| Querella penal (admón desleal) | baja (requiere dolo) | personal + económico |
| Investigación CMF por insider trading | media (si hubo info no pública) | sanción + reputacional |

## Red flags activadas (perfil societario)

- 🚩 **Conflicto de interés del director** sin declaración + abstención
  → nulidad del acuerdo + responsabilidad civil.
- 🚩 **OPR (operación con partes relacionadas)** sin condiciones de
  mercado o sin aprobación del comité → riesgo CMF + acción de daños.
- 🚩 **Pacto familiar / trust** no comunicado al directorio → potencial
  fraude por omisión.

## Disclaimers

- **Borrador no validado.** Pendiente revisión por abogado societario.
- **NCG + Circulares CMF** son operativamente determinantes — verificar
  versiones vigentes.
- **Pequeñas SA cerradas** tienen régimen más flexible pero la regla
  básica de declaración + abstención también aplica.
- **Trust internacional**: análisis tributario adicional + posibles
  obligaciones BEPS / FATCA / CRS.
- **Acción accesoria**: el SII puede revisar la operación por precios de
  transferencia si hay parte relacionada extranjera.

## Normas + skills invocados

- [`ley-18046-sociedades-anonimas`](../normativa/leyes/ley-18046-sociedades-anonimas.md) —
  Art. 146-148 (OPR), Art. 50 bis (Comité), Art. 69 (derecho de retiro).
- [`ley-21314-gobierno-corporativo`](../normativa/leyes/ley-21314-gobierno-corporativo.md) —
  whistleblowing + OPR + transparencia.
- [`ley-21000-cmf`](../normativa/leyes/ley-21000-cmf.md) — supervisión
  + sanciones.
- [`ley-21595-delitos-economicos`](../normativa/leyes/ley-21595-delitos-economicos.md) —
  administración desleal (Art. 470 N° 11 CP).
- [`perfil-societario`](../perfiles/societario.md) — orquestador.
- [`compliance-corporativo`](../skills/compliance-corporativo.md) — MPD
  cubre este escenario.
