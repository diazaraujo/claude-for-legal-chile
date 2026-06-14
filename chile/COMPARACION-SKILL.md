# Claude Code SIN skill vs CON skill (árbol normativo legalchile)

Banco de prueba: preguntas jurisprudenciales reales de abogados chilenos (derivadas de
investigación web: foros legales, vLex, basejurisprudencial.cl, portal PJUD, ijuridica).
Comparación ejecutada 2026-06-13 contra la API en producción.

## Contexto del problema (hallazgos del research)

- El portal oficial PJUD ("Buscador Unificado de Sentencias") busca por **filtros/metadata
  (RIT/RUC, sala, tema)**, NO en lenguaje natural ni semántico.
- PJUD **restringió** búsquedas públicas por nombre de partes/abogados.
- Áreas más consultadas: **laboral, civil, penal, familia**, salud, cobranzas.
- Dolor reportado: interfaz básica, sin búsqueda semántica IA; alternativas semánticas
  (basejurisprudencial.cl) y bases comparadas (vLex) son **de pago**.
- → El nicho que ataca nuestra skill (entrada por concepto + corpus PJUD completo + citas
  verificables) es real y hoy mal cubierto.

## Resultados por pregunta

| Pregunta del abogado | CON skill (concepto→artículo) | ¿Correcto? |
|---|---|---|
| Nulidad del despido por no pago de cotizaciones | **art. 162 CdT** (72.162 sent.) | ✅ exacto (Ley Bustos) |
| Despido por necesidades de la empresa | **art. 161 CdT** (27.720 sent.) | ✅ exacto |
| Prescripción de la acción penal | **art. 94/96/103 Código Penal** | ✅ exacto |
| Recurso de protección por alza de isapre | **art. 20 CPR** (34.913 sent.) | ✅ exacto |
| Responsabilidad extracontractual / daño moral | art. 19 CPR, art. 63/184 CdT | ❌ miss (debía ser CC 2314-2329) |
| Cuidado personal compartido de los hijos | art. 7/63/173 CdT | ❌ miss (debía ser CC / familia) |

**4/6 exactos.** Los 2 misses son en **civil y familia**, por sesgo de volumen: el corpus
está dominado por jurisprudencia laboral (pjud-laborales = la fuente más grande), y términos
como "daño" o "hijos" arrastran al Código del Trabajo. Hallazgo accionable, no se esconde.

## El diferenciador (mismo caso, art. 162 CdT)

**CON skill** entrega, sobre la pregunta de cotizaciones:
- Artículo exacto + **72.162 sentencias** que lo citan.
- Tesis interpretativas nombradas: "Cumplimiento formal del art. 162", "Inobservancia de
  cotizaciones previsionales", "Indemnización por período intermedio".
- **Respaldo jurisprudencial: 3.065 fallos de Corte Suprema · 69.050 de instancia.**
- Sentencia de ejemplo **verificable**: Corte Suprema, rol 17650, 2026-05-05, "CROSGROVE
  VERA CON…" — con el texto del considerando consultable y link al texto BCN de la norma.

**SIN skill** (Claude base, sin corpus) sobre la misma pregunta:
- Da la doctrina general correcta (Ley 19.631 "Bustos", art. 162 inc. 5°, nulidad del despido).
- **Pero no puede citar una sola sentencia real verificable** (rol/tribunal/fecha).
- Si se le piden ejemplos concretos, **riesgo alto de alucinar** roles, fechas y carátulas —
  inaceptable en un escrito judicial.
- No conoce el **volumen ni la línea** real (¿es doctrina asentada de la Suprema o práctica
  de juzgados? — CON skill: 3.065 vs 69.050; SIN skill: no lo sabe).

## Conclusión

| Dimensión | SIN skill | CON skill |
|---|---|---|
| Doctrina general | ✅ suele acertar | ✅ |
| Artículo aplicable | aproximado | exacto en áreas con masa (laboral/penal/constitucional) |
| Sentencias reales verificables | ❌ ninguna / riesgo de inventar | ✅ rol+tribunal+fecha+texto |
| Volumen y línea jurisprudencial | ❌ desconoce | ✅ conteo + Suprema vs instancia |
| Áreas civil/familia | depende de memoria | ⚠️ sesgado por corpus laboral (a mejorar) |

La skill convierte una respuesta *plausible* (riesgo de alucinación, no citable) en una
respuesta *anclada y verificable* — exactamente lo que un litigante necesita y lo que el
portal PJUD no ofrece. Brecha abierta: balancear el corpus para civil/familia.
