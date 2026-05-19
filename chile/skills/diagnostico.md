# Skill — Diagnóstico previo

Skill **transversal y obligatorio**. Antes de aplicar cualquier perfil o citar
normativa, el sistema diagnostica la consulta: identifica jurisdicción, rama del
derecho aplicable, normas relevantes del corpus, vigencia temporal y nivel de
complejidad. El diagnóstico es un acto de **disciplina** — evita aplicar
razonamiento desalineado con el dominio.

## Cuándo se invoca

- **Siempre** al inicio de una conversación nueva, antes de proponer análisis.
- Cada vez que el usuario cambia de tema o introduce un nuevo escenario.
- Antes de citar cualquier norma específica.

## Procedimiento

### Paso 1 — Confirmar jurisdicción

```
¿Es derecho chileno? ¿La situación ocurrió en Chile, involucra a una persona o
empresa chilena, o aplica ley chilena por elección de las partes?
```

**Si la respuesta es ambigua**: preguntar. **Si es derecho extranjero**: declinar
o derivar al abogado, según corresponda.

### Paso 2 — Identificar rama(s) del derecho

Clasificar la consulta en una o más de estas ramas:

| Rama | Indicadores típicos |
|---|---|
| Civil | Contratos generales, responsabilidad extracontractual, sucesiones, derechos reales |
| Comercial | Sociedades, títulos de crédito, contratos mercantiles, navegación |
| Societario | Constitución/operación SA/SpA/SRL, OPR, OPA, deberes fiduciarios |
| Laboral | Relación de trabajo, finiquito, despido, jornada, sindicatos |
| Tributario | Impuestos, declaraciones, fiscalizaciones SII, corrección monetaria |
| Penal | Delitos, querella, investigación, audiencias |
| Procesal civil | Procedimientos civiles, ejecución, prueba |
| Procesal penal | Audiencias, medidas cautelares, juicio oral |
| Administrativo | Procedimiento administrativo, recurso de protección, Contraloría |
| Familia | Divorcio, alimentos, cuidado personal, VIF |
| Concursal | Reorganización, liquidación, deudor insolvente |
| Privacidad | Tratamiento de datos, derechos del titular, brechas |
| Consumidor | B2C, garantía legal, publicidad, SERNAC |
| Constitucional | Recurso de protección, inaplicabilidad, derechos fundamentales |
| Compras públicas | Licitaciones, convenio marco, ChileCompra, TCP |

**Una consulta puede tocar varias ramas**. Identificar todas y priorizar la
principal.

### Paso 3 — Identificar normas relevantes del corpus

Para la rama identificada, buscar archivos en `chile/normativa/`:

- **Constitución** si hay garantías o derechos fundamentales involucrados.
- **Código** que rige la materia principal.
- **Leyes especiales** modificatorias o complementarias.
- **Decretos** reglamentarios cuando aplique.
- **Dictámenes** administrativos del organismo competente (DT, SII, Contraloría).

Si el archivo no existe (capa 1 o no existe en absoluto), declararlo antes de
responder.

### Paso 4 — Verificar vigencia temporal

- ¿La norma está vigente hoy?
- ¿Hay una modificación reciente que cambie el escenario?
- ¿La situación ocurrió bajo el texto antiguo o el nuevo? (especialmente
  relevante para Ley 21.719 — antes/después del 2026-12-01)
- ¿Hay vigencia diferida o transitoria?

### Paso 5 — Evaluar complejidad

| Nivel | Indicadores | Approach |
|---|---|---|
| **Bajo** | Pregunta cerrada con respuesta directa en una norma | Citar y resolver |
| **Medio** | Combinación de 2-3 normas, escenarios típicos | Analizar y proponer |
| **Alto** | Decisión estratégica, conflicto entre normas, ausencia de regulación clara, derechos fundamentales | Identificar opciones y derivar al abogado |
| **Fuera de alcance** | Materias excluidas (indígena, aguas, minero, marítimo, juicio penal específico) | Declarar y derivar |

### Paso 6 — Declarar el diagnóstico

Antes de responder, el sistema enuncia:

```
DIAGNÓSTICO:
- Jurisdicción: Chile
- Rama principal: <rama>
- Ramas secundarias: <si aplica>
- Normas relevantes: <lista de slugs del corpus>
- Vigencia: <fecha y estado>
- Complejidad: <bajo / medio / alto / fuera de alcance>
- Capa de respuesta: <1 / 2 / 3 según archivos disponibles>
```

Si la capa es 1 o no hay archivo, agregar disclaimer extra:

```
⚠ Esta respuesta se basa en metadata catalográfica (capa 1) o conocimiento
general, no en análisis curado y validado. Verificar contra BCN/LeyChile y
con abogado habilitado antes de actuar.
```

## Reglas de oro

1. **Diagnóstico antes de respuesta.** Nunca saltar al análisis sin diagnosticar.
2. **Mejor declinar que inventar.** Si la consulta cae en zona de baja confianza,
   declararlo.
3. **No mezclar jurisdicciones.** No aplicar precedentes españoles, argentinos o
   anglosajones a casos chilenos sin advertencia.
4. **Buscar el archivo del corpus antes de razonar.** Si existe perfil o ley en
   `chile/normativa/`, usarlo. No improvisar.

## Casos de prueba

Ejemplos canónicos para validar el funcionamiento del skill viven en
`chile/ejemplos/diagnostico-*.md` (pendientes de redacción).
