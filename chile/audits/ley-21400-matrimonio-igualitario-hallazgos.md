---
archivo_revisado: ley-21400-matrimonio-igualitario
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#13"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.400 (Matrimonio Igualitario)

> Revisión técnica (consistencia, gaps), NO legal.

## Resumen ejecutivo

El perfil cubre cambios principales (matrimonio, régimen patrimonial,
filiación asistida, adopción, pensión viudez, identidad género).
Hallazgos:

- **4 críticos** para validador de familia.
- **1 técnico**.
- **6 preguntas abiertas**.

## Hallazgos críticos — decisión del validador

### H1 — "Régimen patrimonial por defecto: separación total"

El perfil declara:
> **Si no pacto**: separación total de bienes por defecto.

**Observación**: Esto contradice la regla histórica del CC chileno
donde la **sociedad conyugal era el régimen supletorio**. La Ley
21.400 podría haber:
- Mantenido la sociedad conyugal como supletorio (con administración
  no-asignada por género).
- O cambiado a separación total como supletorio.

**Acción sugerida** (CRÍTICA): verificar contra el texto. Si el
supletorio es **sociedad conyugal** (no separación), el perfil tiene
error fundamental que se propaga a todo el bloque familia patrimonial.

### H2 — Filiación de cónyuge no gestante: presunción legal

El perfil declara:
> **Madre no gestante** (en matrimonio del mismo sexo entre mujeres):
> se presume materna si está casada con la gestante.

**Observación**: El régimen exacto de filiación matrimonial post-21.400
para parejas del mismo sexo es **complejo**:
- ¿Aplica la presunción del Art. 184 CC (pater is) como "co-madre is
  quem matrimonium demonstrat"?
- ¿Requiere reproducción humana asistida (RHA) acreditada o vale
  cualquier técnica?
- ¿Aplica a parejas masculinas (que requieren gestación subrogada,
  prohibida o no regulada en Chile)?

**Acción sugerida**:
- Detallar régimen de filiación matrimonial por sexo de los cónyuges.
- Confirmar interacción con Ley 19.477 (RHA — si existe régimen
  vigente).
- Documentar excepciones / requisitos formales.

### H3 — Adopción: "parejas del mismo sexo casadas"

El perfil declara:
> **Parejas del mismo sexo casadas** pueden postular.

**Observación**: ¿Y parejas en AUC pueden postular? El perfil de AUC
mencionaba que adopción "es posible para parejas con AUC" — verificar
consistencia.

**Acción sugerida**:
- Confirmar quién puede postular tras 21.400: solo matrimonio o
  también AUC.
- Revisar consistencia con `ley-20830-acuerdo-union-civil` y
  `ley-19620-adopciones`.

### H4 — Pensión de viudez para cónyuge mismo sexo

El perfil declara:
> Cónyuge sobreviviente del mismo sexo: derecho a pensión de
> viudez/sobrevivencia.

**Observación**: Falta cómo se aplica retroactivamente a:
- AUC pre-21.400 que se convirtió en matrimonio post-2022.
- Matrimonios celebrados en el extranjero antes de 2022.
- Casos de muerte antes de 2022 con conviviente reclamando.

**Acción sugerida**:
- Documentar régimen transitorio para casos pre-vigencia.
- Confirmar aplicación retroactiva o efectos solo prospectivos.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

Bien aplicado el campo canónico. (Tras fix mecánico del 2026-05-19.)

## Preguntas abiertas para el validador

1. **¿Reproducción asistida**: existe régimen legal o queda en
   reglamento Mineduc / MINSAL? ¿Cobertura FONASA/ISAPRE?

2. **¿Gestación subrogada**: prohibida expresamente, no regulada, o
   permitida bajo ciertas condiciones?

3. **¿Conversión AUC → matrimonio**: trámite + costos + efectos
   patrimoniales sobre comunidad existente del AUC.

4. **¿Matrimonio extranjero pre-2022 entre personas del mismo sexo**:
   ¿se reconoce automáticamente o requiere acto interno?

5. **¿Bonos / cargas familiares previsionales** (Ley 20.255 — bono por
   hijo) se aplica al cónyuge no gestante por filiación legal?

6. **¿Régimen tributario** del divorcio o disolución: ganancia capital
   en liquidación de sociedad conyugal post-21.400 (cuando régimen
   no asignado por género).

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1170048 | ⚠️ BCN no respondió |
| Vigencia "marzo 2022" | ⚠️ confirmar día exacto |
| Régimen patrimonial supletorio | ⚠️ ver H1 (CRÍTICO) |
| OC-24/17 Corte IDH | ✅ es decisión real (2017) |

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #13.
- **Respuesta del validador**: pendiente.
