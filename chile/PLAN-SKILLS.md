# Plan de Skills — claude-for-legal-chile

> Objetivo: dotar a Chile de una capa de skills propia. **Regla dura: cero
> contaminación argentina** — se adapta el MÉTODO/ESTRUCTURA de Argentina, NUNCA
> su contenido normativo (CCCN, LCT, telegrama laboral, fueros provinciales). El
> derecho citado es siempre chileno y recuperado del corpus.

## 1. Estado VERIFICADO de Argentina (`cristianaboitiz-eng/claude-for-legal-argentina`)

Verificado vía GitHub API el 2026-05-29 (lista de archivos + contenido real, no inferido):

- **Scaffold upstream**: 154 `SKILL.md` genéricos (heredados de `anthropics/claude-for-legal`, orientados a derecho US: bar-prep, marketing-claims, etc.). **NO localizados** a Argentina.
- **Capa localizada** (`argentina/`, ~58 .md):
  - 7 perfiles de rama: `administrativo`, `civil`, `concursos`, `contratos`, `familia`, `laboral`, `penal` (CLAUDE.md cada uno).
  - 17 variantes **provinciales** de administrativo (CABA, PBA, Córdoba, Santa Fe…) — estructura federal, **no aplica a Chile** (unitario).
  - **Solo 3 `SKILL.md` localizados**: `diagnostico-SKILL.md`, `plazos-SKILL.md`, `laboral/telegrama/telegramas-SKILL.md` (el telegrama es instrumento laboral argentino).
  - **Framework `evals/`**: casos de verificación manuales — cada caso = carpeta con `caso.md` (pieza procesal anonimizada), `rubrica.md` (puntos binarios que el sistema debe detectar), `resultado.md` (solución esperada). NO corre solo; el abogado pega el caso y compara. (Verificado del `evals-README.md` real.)
  - Soporte: `ejemplos-{civil,laboral,societario}.md`, `marcadores-GLOSARIO.md`, `red-flags-contratos.md`, `fuentes.md`, `setup-interview.md`, `especialidades/medicina-legal-CLAUDE.md`.
- **NO tiene**: corpus scrapeado, RAG, embeddings ni jurisprudencia (verificado: 2 archivos de data en todo el repo). Depende del training de Claude.

## 2. Estado actual de Chile (verificado)

- **151 `SKILL.md`** del mismo scaffold upstream ya presentes (no son un gap; son los genéricos US).
- **5 skills planos** en `chile/skills/`: `diagnostico.md`, `diagnostico-casos-prueba.md`, `citas-verificables.md`, `plazos.md`, `compliance-corporativo.md` (formato .md, NO `SKILL.md` invocable aún).
- **9 perfiles de rama** + 126 perfiles capa-3 + normativa 3-capas.
- **Ventaja única vs Argentina**: corpus masivo (jurisprudencia 1M+, dictámenes 250k+) + MCP `corpus-search` (BM25+bge-m3). Argentina no tiene nada de esto.

## 3. Plan

### Fase 0 — Auditoría y formato (0.5 día)
- Inventariar los 151 SKILL.md heredados: marcar reusables (workspace, matter, diagnóstico) vs US-only descartables. NO localizar todavía.
- Convertir los 5 skills planos de `chile/skills/` a formato **`SKILL.md`** invocable.

### Fase 1 — Adaptar el MÉTODO de Argentina (sin su contenido) (1-2 días)
- **Framework `evals/`** (lo más valioso): replicar la estructura `caso.md` / `rubrica.md` / `resultado.md`. Poblar con **casos chilenos reales** sacados del corpus (un fallo PJUD, un dictamen CGR con solución conocida). Da test-suite jurídica medible.
- **`marcadores-GLOSARIO`**: glosario de marcadores **chilenos** (UF, UTM, CMF, DT, COT, RUT…). Estructura de AR, términos de Chile.
- **`red-flags-contratos`** y **`ejemplos`** por rama: estructura de AR, contenido chileno verificado contra normativa vigente del corpus.
- **`especialidades/`**: medicina-legal + propias fuertes en Chile (minero, aguas, pesca, ambiental).
- **NO portar**: telegrama laboral (AR), variantes provinciales (AR federal).

### Fase 2 — Skills NATIVOS de corpus ⭐ (el diferenciador, 2-3 días)
Lo que Argentina **no puede** tener. Skills que invocan los MCP `corpus-search`/`mcp-cgr-dictamenes`/`mcp-dt-dictamenes`:
- `buscar-dictamen` — CGR/DT/CPLT/SUSESO por materia.
- `buscar-jurisprudencia` — PJUD/TC/TDLC por rol o tema.
- `verificar-cita` — valida rol/número contra el corpus (anti-alucinación real, no por prompt).
- `linea-jurisprudencial` — agrupa fallos/dictámenes sobre un punto de derecho.
- `red-flags-contrato-cl` — revisa contrato contra normativa vigente recuperada.

### Fase 3 — Wiring + tests (1 día)
- Registrar skills en el plugin (`register-mcps.sh` / plugin manifest), smoke con casos reales, golden suite que use el framework evals de Fase 1.

## 4. Principio rector
No clonamos prompts argentinos. Tomamos su **método** (evals, glosario, red-flags) y lo llenamos con **derecho chileno verificado del corpus**. Los skills de corpus (Fase 2) son donde Chile supera estructuralmente a Argentina: anti-alucinación por retrieval, no por confiar en el training del modelo.
