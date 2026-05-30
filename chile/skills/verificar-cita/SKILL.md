---
name: verificar-cita
description: >
  Verifica que una cita legal o jurisprudencial chilena exista REALMENTE en el
  corpus antes de afirmarla. Anti-alucinación por retrieval, no por prompt. Usar
  cuando el usuario pega o pide confirmar un artículo de ley, un rol de causa
  ("CS Rol 12.345-2022"), un número de dictamen ("Dictamen CGR E80945N25",
  "ORD. DT N°377/33"), o cuando se va a citar algo en un escrito. Dispara también
  antes de incluir cualquier cita en un entregable.
argument-hint: "[cita a verificar: artículo, rol o número de dictamen]"
---

# /verificar-cita

## Cuándo corre

El usuario pide validar una cita, o el sistema va a incluir una cita en una
respuesta/escrito. **Regla dura del proyecto: nunca afirmar una cita sin haberla
recuperado del corpus.** Esta skill materializa esa regla.

## Qué hacer

1. **Clasificar la cita**:
   - Artículo de ley/código → `corpus-search` tool `corpus_search_articulos`
     (filtrar por `leychile_code` si se conoce) con `vigentes_only=true`.
   - Rol judicial (CS/CA/TC/TDLC) → MCP correspondiente: `mcp-pjud`,
     `mcp-tc-fallos`, `mcp-tdlc`. Buscar por rol exacto.
   - Dictamen administrativo → `mcp-cgr-dictamenes` (CGR), `mcp-dt-dictamenes`
     (DT), o `mcp-sii-juris` (SII) por número.
   - Texto literal citado → `corpus_verify_quote` (anti-hallucination tool del
     corpus-search).

2. **Resolver**:
   - **Encontrada**: confirmar con la referencia canónica recuperada (texto +
     fuente + vigencia). Formato chileno: "Art. X de Ley Y (vigente)",
     "CS Rol 12.345-2022", "Dictamen CGR E80945N25 (19-05-2025)".
   - **No encontrada**: STOP. Declarar explícitamente: *"No tengo respaldo
     verificable para esta cita en el corpus; verificar en BCN/LeyChile o en el
     Buscador del Poder Judicial antes de usarla."* NUNCA rellenar con una cita
     plausible inventada.
   - **Derogada/superseded**: informar que la norma no está vigente y derivar a
     la versión que la reemplaza (campo `superseded_by`).

3. **Marcar incertidumbre**: si la recuperación es parcial (match difuso),
   etiquetar "NO verificado" en vez de afirmar.

## Reglas
- Citar SOLO derecho vigente al armar entregables (`vigentes_only`); indexado
  incluye derogado pero no se cita como vigente.
- Jurisprudencia: jamás inventar un rol. Si no hay rol exacto, describir el
  criterio sin atribuir cita específica.
- El resultado de esta skill es la base de cualquier cita posterior en el turno.
