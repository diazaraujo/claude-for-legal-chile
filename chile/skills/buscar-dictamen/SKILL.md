---
name: buscar-dictamen
description: >
  Busca dictámenes y jurisprudencia administrativa chilena en el corpus:
  Contraloría (CGR), Dirección del Trabajo (DT), Consejo para la Transparencia
  (CPLT), SUSESO, SII (oficios). Sobre el corpus real bulk — no inventa números.
  Usar cuando el usuario pide "qué dice Contraloría sobre X", "dictamen de la DT
  sobre Y", "criterio del SII en materia Z", "jurisprudencia administrativa sobre W".
argument-hint: "[materia u organismo]"
---

# /buscar-dictamen

## Cuándo corre
El usuario quiere la postura administrativa/interpretativa de un organismo
chileno sobre una materia (no un fallo judicial — para eso, [[buscar-jurisprudencia]]).

## Qué hacer
1. **Elegir organismo**:
   - Probidad, toma de razón, función pública, municipal → **CGR** (`mcp-cgr-dictamenes`).
   - Código del Trabajo, materia laboral interpretativa → **DT** (`mcp-dt-dictamenes`).
   - Acceso a información, Ley 20.285 → **CPLT** (`corpus_search` source=cplt).
   - Seguridad social, licencias, mutualidades → **SUSESO**.
   - Tributario (renta/IVA), oficios → **SII** (`mcp-sii-juris`).
2. **Consultar** `mode=hybrid` por materia, o por número si el usuario lo da.
3. **Presentar**: organismo + **número exacto** (formato chileno: "Dictamen CGR
   E80945N25", "ORD. DT N°377/33", "Oficio SII N°1777") + fecha + materia +
   extracto del criterio. Si hay varios, ordenar del más reciente y señalar si
   un dictamen reconsidera/aplica/complementa otro (campo de relación cuando exista).
4. **Anti-alucinación**: solo dictámenes recuperados. Sin resultados → decirlo.
   Verificar cada número con [[verificar-cita]] antes de citar en entregable.

## Reglas
- Distinguir dictamen **vigente** vs reconsiderado/derogado cuando el corpus lo marque.
- No confundir dictamen administrativo (interpreta) con sentencia judicial (resuelve litigio).
- CGR: la base bulk cubre dictámenes 1990→hoy; señalar si la materia es muy reciente
  y podría no estar aún indexada.
