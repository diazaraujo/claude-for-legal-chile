---
name: buscar-jurisprudencia
description: >
  Busca sentencias judiciales chilenas en el corpus (Corte Suprema, Cortes de
  Apelaciones, Tribunal Constitucional, TDLC, Tribunales Ambientales, TTA, TDPI)
  por materia, rol o criterio. Retrieval híbrido sobre el corpus real — no
  inventa fallos. Usar cuando el usuario pide "qué ha dicho la jurisprudencia
  sobre X", "fallos de la Corte Suprema sobre Y", "precedentes de tutela
  laboral", "criterio del TC sobre Z".
argument-hint: "[materia, tribunal o rol]"
---

# /buscar-jurisprudencia

## Cuándo corre
El usuario quiere precedentes/sentencias chilenas sobre un punto de derecho.

## Qué hacer
1. **Elegir fuente** según el tribunal pedido (o barrer todas si es por materia):
   - Justicia ordinaria (C. Suprema, Apelaciones, laboral, civil, penal, familia,
     cobranza) → `mcp-pjud` / `corpus_search_considerandos`.
   - Constitucional → `mcp-tc-fallos`.
   - Libre competencia → `mcp-tdlc`.
   - Ambiental, tributario-aduanero (TTA), propiedad industrial (TDPI) → vía
     `corpus_search` con filtro `source`.
2. **Consultar** con `mode=hybrid` (BM25 + bge-m3) para preguntas en lenguaje
   natural; `mode=fts` si el usuario da términos exactos. Usar `corpus_search_considerandos`
   para recuperar el razonamiento (no solo metadata).
3. **Presentar** cada resultado con: tribunal + **rol exacto** (formato chileno) +
   fecha + extracto del considerando relevante + materia. Agrupar por criterio.
4. **Anti-alucinación**: solo fallos recuperados. Si no hay resultados, decirlo;
   no inventar roles ni criterios. Pasar cada cita por [[verificar-cita]] antes de
   incluirla en un entregable.

## Reglas
- Rol siempre verificable y en formato chileno ("CS Rol 12.345-2022").
- Distinguir holding vs obiter cuando el considerando lo permita.
- Marcar si un criterio fue modificado/superado por fallo posterior si el corpus
  lo evidencia; si no, no afirmar línea consolidada.
