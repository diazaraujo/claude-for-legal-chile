# Changelog — adaptación chilena

Cambios al contenido de `chile/`. Para cambios del upstream ver `git log` con
`upstream/main`.

## 0.8.0 — 2026-05-27 — Retrieval semántico/híbrido por artículo en el MCP

### Embeddings: las 4 capas completas

Estado del índice `corpus.fts.sqlite3` (bge-m3, dim 1024):

| Capa | Filas | Embebidas | Cobertura |
|---|---|---|---|
| docs (ley/sentencia completa) | 80.145 | 80.145 | 100% |
| **artículos** | 161.033 | 156.965 | 100% del contenido sustantivo |
| considerandos (chunks) | 246.121 | 246.121 | 100% |
| doctrina | — | 10.032 | — |

Los 4.068 artículos sin embedding son stubs `<30` chars (DEROGADO / ELIMINADO /
encabezados de sección) que el builder filtra a propósito (`len(content) >= 30`).
No es deuda: es ruido excluido.

### `corpus_search_articulos` ahora soporta `mode`

Hasta ahora la tool era solo FTS5/BM25 — no usaba los 157k `articulos_embeddings`.
Nuevo parámetro `mode`:

- **`fts`** (default): BM25 keyword, comportamiento previo intacto.
- **`hybrid`**: vector bge-m3 como backbone + BM25 fusionado vía Reciprocal Rank
  Fusion (RRF, K=60). El query natural se sanitiza a un FTS5 OR-de-términos para
  el boost keyword. Recomendado para preguntas en lenguaje natural.
- **`semantic`**: orden puro por similitud coseno.

Implementación (`mcp-corpus-search/search_client.py`):
- Matriz de embeddings de artículos cacheada por proceso (numpy, normalizada →
  coseno = producto punto). Primera query ~10s (carga 157k×1024), siguientes ~1s.
- Degrada con gracia a FTS si no hay Ollama/numpy/tabla de embeddings.

Ejemplo resuelto que FTS doc-level no acertaba:
`"puede el empleador despedir a una trabajadora embarazada"` → semantic devuelve
Art. 202 Código del Trabajo (fuero maternal) en el top, sin overlap léxico exacto.

### Tests

- Smoke MCP: 11/11.
- Golden suite extendida a 14 casos (de 12): el harness soporta `articulos_mode`
  (compara `path_contains` contra `leychile_code|articulo_num|snippet`). Nuevos
  casos: fuero maternal (semantic) y jornada Código del Trabajo (hybrid filtrado).

### Versiones superseded (`docs_norma.superseded_by`)

Nueva columna `superseded_by` (idNorma de la versión que reemplaza) para el caso
de un refundido reemplazado por otro más nuevo, que LeyChile deja ambos como
"no derogado". `vigentes_only` ahora también oculta las versiones superseded
(además de las derogadas). Cableado en `_load_norma_meta` (tolerante a DBs sin la
columna) + `_passes_vigencia`.

`mark-superseded-versions.py` aplica **solo pares verificados caso a caso** — NO
hay detección automática: la clave (tipo,numero,titulo) es insegura (p.ej. los
certificados "DETERMINA INTERÉS CORRIENTE…" comparten tipo+numero+titulo pero son
publicaciones periódicas distintas, no versiones). Único par marcado hoy:
**3471 → 207436** (Código del Trabajo 1994 → 2002, verificado). Validado: con
`vigentes_only` el 3471 desaparece y queda el 207436. Golden suite a 16 casos.

### Gap A: 3.332 leyes con XML pero sin texto en el full-text search

Detectado al auditar `sin_dato`: había 8.240 XML de leyes en disco pero solo
4.908 con `.xml.txt` extraído → 3.332 leyes estaban en la búsqueda por artículo
pero NO en `corpus_search` (full-text doc). `extract-xml-text.py` generó los 3.332
`.xml.txt` (offline, 2s) y `build-fts-index.py` los indexó: **leychile-ley en
docs 4.908 → 8.240**.

Nota operativa: `build-fts-index.py` debe correrse con `--root` ABSOLUTO. Con ruta
relativa, `source_from_path` (que usa `relative_to(DATA_ROOT)` absoluto) falla y
asigna `source='unknown'` + paths relativos que no matchean los existentes →
duplica filas. (Pasó y se limpió: `DELETE WHERE path LIKE 'data/%'` + reindex
absoluto.) Pendiente: doc-level embeddings de esas 3.332 (tabla `embeddings`).

### Tools MCP nuevas: considerandos y doctrina (consumen embeddings ya hechos)

Los embeddings de considerandos (246k) y doctrina (10k) estaban construidos pero
sin ninguna tool que los usara. Agregadas a `mcp-corpus-search`:

- **`corpus_search_considerandos`**: busca párrafos de razonamiento de fallos
  (TC 224k, tribunales ambientales, TDLC, TDPI). mode fts/hybrid/semantic + RRF,
  filtro `source`. Matriz cacheada por proceso (~1GB, 1ª query ~30s, luego ~7s).
- **`corpus_search_doctrina`**: tesis/papers universitarios (UCh, UV, UFT, U.
  Autónoma, UCN). Semántico puro (sin FTS); extrae título del frontmatter +
  snippet del .md.

Golden suite a 18 casos (considerandos TC igualdad, doctrina responsabilidad del
Estado). Mismos helpers que artículos (`_ollama_embed`, `_cosine`, `_fts_or_query`).

### Re-extracción del corpus completo de artículos: 161.666 → 214.839

El bug del regex "Art." no era solo del 207436: medido a nivel corpus, **4.452
docs afectados, ~56.939 artículos perdidos** por colisión en UNIQUE(doc_path,
articulo_num). Incluía los textos más citados — Código Penal (756 bloques, solo
**27** en meta), Código Orgánico de Tribunales (18), Código de Justicia Militar
(13), refundidos varios.

Rebuild limpio de la capa de artículos (no parche): drop de `articulos` +
`articulos_meta`, delete de `articulos_embeddings`, y re-extracción de los 35.977
XML con el regex arreglado + alineación `id==rowid`. Resultado: **214.839
artículos** (+53.173), FTS==meta, 0 mismatch de alineación. Código Penal 27→756,
COT 18→680, Justicia Militar 13→473. (No se tocaron docs/considerandos.)
Re-embedding de los 214.839 corriendo en background.

### Re-extracción Código del Trabajo vigente (207436): 104 → 737 artículos

Bug en `build-articulos-index.py`: el regex `ART_RE` solo reconocía
"Artículo N" (palabra completa), no el formato abreviado "Art. N.o" que usa el
DFL 1 de 2002 (207436). De 842 bloques `<EstructuraFuncional>` solo matcheaban
220; los 619 restantes quedaban con `articulo_num=''` y colisionaban en el
`UNIQUE(doc_path, articulo_num)` → solo 104 artículos en `articulos_meta` (pese a
766 filas en el FTS).

Correcciones al extractor (general, beneficia a toda ley con formato "Art."):
- `ART_RE` acepta "Artículo N", "Art. N", "Art.N", "Art. N.o", ordinales y
  sufijos bis/ter/quáter/quinquies/sexies.
- `TITULO_RE` reconoce "Párrafo" como sección.
- Desambiguación de números repetidos dentro del mismo doc (artículos
  transitorios) sufijando "(2)", "(3)" — antes se perdían por el UNIQUE.
- **Alineación `articulos_meta.id == articulos.rowid`** en el insert (FTS rowid
  explícito). Resuelve el drift histórico que el builder de embeddings asume.
- Flags `--leychile-code` y `--reset` (borra articulos+meta+embeddings del doc).

207436 re-extraído: **104 → 737 artículos** (0 mismatch de alineación),
re-embebidos (732 ok, 5 stubs <30c). Ahora los Art. 22, 159, 161, 162, 202 del
Código del Trabajo **vigente** aparecen en la búsqueda. Total corpus: 161.033 →
161.666 artículos, 156.965 → 157.593 embeddings.

Efecto colateral: de los 444 artículos del 3471 (1994) solo **9 no están en
207436** (204, 314 bis, 334 bis, 374 bis, 412, 413, 428 bis, 473 bis, 478 bis).
Revisados caso a caso (2026-05-27): **verificado** que ni su número ni su
contenido distintivo están en el texto consolidado vigente (207436) — la
secuencia del XML fuente tiene huecos exactos ahí (…203,205…; …411,415…) y
contienen disposiciones procesales de negociación colectiva / juicios laborales.
O sea: NO son parte del Código del Trabajo vigente. El **mecanismo** (derogación
formal vs renumeración en reforma vs traslado a otra ley) NO se verificó por
artículo — requeriría historia legislativa BCN. Implicación operativa: para citar
derecho vigente esos 9 no aplican; 3471 funciona como versión histórica.

### Vigencia: backfill desde XML local (cobertura 20% → 76%)

Diagnóstico: `docs_norma.derogado` estaba 80% en `sin_dato` y `version_xml` 20%
poblado — al construir el índice no se parsearon los atributos del root `<Norma>`
para la mayoría de las normas. La señal autoritativa ya estaba en disco
(`data/leychile/{tipo}/{idNorma}.xml`, atributos `derogado` + `fechaVersion`).

`backfill-vigencia-from-xml.py` recorre los 35.977 XML locales y actualiza
`docs_norma` (offline, idempotente, ~9s):

| | derogado | no derogado | sin_dato |
|---|---:|---:|---:|
| antes | 413 | 9.010 | 38.019 (80%) |
| después | 3.138 | 33.030 | 11.274 (24%) |

Cobertura del núcleo legal: dto/dl/dfl ahora 100%, ley 71% (de 32%), cod 57%.
**2.725 normas derogadas nuevas identificadas → 24.618 artículos indexados ahora
correctamente marcados como de norma derogada**, que `vigentes_only` filtra.

Los 11.274 `sin_dato` restantes son fuentes sin XML LeyChile (cer/acd/avi/cir de
otras agencias + 3.369 leyes catalog-only no descargadas) — requieren fetch BCN.

Sobre el "dedup canónico" que se había anotado como pendiente: investigado y
**descartado como tarea**. La duplicación aparente es legítima — (a) versiones
complementarias con artículos disjuntos (Código del Trabajo 3471 1994 vs 207436
2002), (b) plantillas de decretos realmente distintas (p.ej. 195 decretos de
concesión eléctrica con texto base común). Solo existe **1 grupo** de refundido
multi-versión por título exacto (el Código del Trabajo), y su causa raíz es que
207436 (vigente) está sub-extraído (104 de ~500 artículos): se resuelve
re-extrayendo su XML, no con una regla de superseding frágil.

### Filtros de vigencia en la búsqueda por artículo

`corpus_search_articulos` ahora acepta `vigentes_only` y `exclude_modificadoras`
(igual que `corpus_search` a nivel doc), en los tres modos (fts/hybrid/semantic).
Resuelve la vigencia vía `docs_norma` usando el `leychile_code` del artículo;
helper compartido `_passes_vigencia`. Over-fetch de candidatos (×4 en FTS, ×16 en
semantic) para compensar lo que se descarta. Sin metadata de norma se deja pasar
(no se asume derogación sin dato).

Validado: query de fuero maternal con `vigentes_only` excluye el Art. del idNorma
6850 (derogado) y conserva los artículos vigentes de embarazo. Golden suite a 15
casos (harness soporta `expect_none` para aseverar exclusión).

### Pendiente conocido

Duplicación de versiones del mismo código en el corpus (p.ej. Código del Trabajo
bajo idNorma 3471 antiguo y 207436, ambos marcados "no derogado" en docs_norma)
sigue inyectando ruido: `vigentes_only` NO los desambigua porque metadata no marca
el antiguo como derogado. Pendiente: deduplicar por norma canónica / preferir la
versión refundida vigente.

## 0.7.1 — 2026-05-21 — Resolver batch + dedupe canonical + bug Virtuoso

### Resolver bcn_uri masivo (batch SPARQL VALUES)

- `resolver-bcn-uri-batch.py`: una query con `VALUES ?c { ... }` resuelve
  hasta 50 leychile_codes a la vez. **63/66 perfiles capa 3 huérfanos
  resueltos en 4 segundos** (vs ~80s/perfil del approach 1-por-1).
- Filtros: `!REGEX("/es@")` excluye versiones, `!REGEX("/proyecto-de-ley/")`
  excluye URIs de proyectos (cuando misma leychile_code apunta a proyecto
  + ley promulgada).

### Bug Virtuoso descubierto

`SELECT ?n LIMIT 1` con duplicados internos puede devolver 0 results.
Solución: `SELECT DISTINCT ?n`. Documentado en
[reference-bcn-sparql-endpoint](memoria persistente).

### Otros findings técnicos

- `leychileCode` es `xsd:integer` (no string) — query con literal
  `"123"` NO matchea; usar `FILTER (str(?c) = "...")` o VALUES.
- Muchas URIs del grafo no tienen `rdfs:label` propio (referencias
  no entidades). `?n rdfs:label ?label .` REQUIRED filtra los huérfanos.
- BCN inconsistencia separadores: `_` y `-` para mismo organismo.
  Canonicalizar para dedup.

### Dedupe canónico (-696 archivos)

`dedupe-catalogo.py` mejorado con canonical_uri():
- quita `/es@YYYY-MM-DD`
- normaliza `_` → `-`

Detecta 687 grupos vs 113 del dedupe anterior. Catalog ahora 20.839
archivos.

### Cleanup pendientes verificación BCN

8 perfiles que tenían `fuente_oficial_status: pendiente-verificacion-bcn`
ahora con bcn_uri canónico via resolver. Disclaimer removido.

### URI fix: idNorma 172986 era DFL refundido

- Código Civil: idNorma 172986 → **1973** + `texto_refundido_dfl: 172986`
- Ley 14908: idNorma 172986 → **27977** + `texto_refundido_dfl: 172986`

### Scrape selectivo URIs grafo (corriendo)

`scrape-sparql-uris-grafo.py`: scrapea SOLO las URIs del grafo BCN no
presentes en catálogo (~80k pendientes vs 322k scrape masivo). Batch
SPARQL VALUES, ~1.5 URI/s steady. Subida densidad grafo 3.0% → 4.4%
con 15% completo.

## 0.7.0 — 2026-05-21 — Grafo BCN completo + backlog capa 3 priorizado

### Grafo BCN (pilar 2 cerrado)

Scrape SPARQL de los 9 predicados de bcn-norms completo en 2h:

| Predicado | Edges |
|---|---:|
| modifiesTo | 328.203 |
| isModifiedBy | 327.507 |
| agreeWith | 91.853 |
| isRegulatedBy | 3.906 |
| regulates | 2.049 |
| isRectifiedBy | 959 |
| rectifies | 901 |
| recasts | 661 |
| isRecastedBy | 126 |
| **Total** | **746.165** |

Paginación por URI lexicográfica (evita bug Virtuoso de OFFSET >10k).

### Capa 3 enriquecida con grafo (90 perfiles, 3.017 edges)

Frontmatter ahora incluye 9 sub-campos en `grafo_relaciones`:
modifica, modificada_por, reglamenta, reglamentada_por, refunde,
refundida_por, rectifica, rectificada_por, acuerda_con.

Canonicalización: quita `/es@YYYY-MM-DD` (versiones temporales) +
normaliza separadores BCN inconsistentes (`_` vs `-`).

### 22 borradores capa 3 nuevos (priorizados por degree del grafo)

Generador `generar-borradores-capa3.py` crea perfiles con **solo
metadata verificable** (catálogo BCN + grafo) + checklist de pendientes
para abogado. Marca `borrador-generado-no-validado`.

Borradores nuevos:
- Tránsito/Civil: Ley 18290 (Tránsito), Ley 18020 (SUF)
- Penal: Ley 19806 (Adecuatorias PP), Ley 19047 (Garantías), Ley 19828 (SENAMA)
- Societario: Ley 19705 (OPAs), Ley 20552 (Modernización Financiera), DFL 3 (Propiedad Industrial)
- Administrativo: Ley 19653 (Probidad), Ley 20088 (Decl. Patrimonial), Ley 19882 (Personal Funcionarios), Ley 20128 (Resp. Fiscal)
- Tributario: Ley 19738 (Evasión), Ley 20322 (TTA), Ley 20026 (Royalty Minero), Ley 18634 (Aduana)
- Otros: Ley 19925 (Bebidas), Ley 20502 (SENDA), Ley 20530 (Min Des Social), Ley 20283 (Bosque Nativo), DL 3501 (Cotiz. Previsional), DFL 850 (Caminos OOPP)

### MCP enriquecido

- `lookup_by_uri()` en LocalCatalog.
- `get_relaciones` ahora resuelve dst URIs a slugs locales (output más útil).
- CLI `mcp-bcn-cli` con misma mejora.
- 11/11 tests offline en verde.

### Auditorías nuevas

- `audits/densidad-grafo-2026-05-21.md` — densidad 3% del grafo, gap dto/res.
- `audits/cobertura-leyes-2026-05-21.md` — distribución por rango numérico.
- `scripts/audit/hubs-sin-capa3.py` — backlog priorizado por degree.
- `scripts/audit/check-mcp-resolves-capa3.py` — verifica 158/158 perfiles resuelven via MCP.

### Capa 3 corpus

- 158 perfiles inicial + 22 borradores sesión = **180 perfiles**.

## 0.6.0 — 2026-05-21 — Catálogo + grafo BCN + MCP local-first

**Resumen:** transición arquitectural del scrape REST-por-norma al
endpoint SPARQL del grafo BCN. Cobertura del catálogo +193% (de ~9.500
a 17.817 normas) en una sesión, con 7 tools MCP expuestas y testeadas.

### Catálogo (capa 1)

- **+8.360 normas nuevas via SPARQL** en 10 tipos previamente no
  cubiertos: cer (2.952), avi (1.008), cir (791), aa (533), dfl (530),
  tra (167), cci (143), bando (71), cod (19), alc (16).
- **DL/DFL/DS resueltos** — eran bloqueo crítico: el endpoint REST
  `cl/ley/{N}` solo soporta `ley/`. Vía SPARQL ahora 3.656 DL + 530 DFL.
- Pendiente segunda pasada: ~340k dto/res operacionales (no core legales).

### Mapping relacional (capa 2 grafo)

- `chile/normativa/grafo/relaciones-bcn.jsonl` — JSONL con edges del
  ontology bcn-norms (modifiesTo, isModifiedBy, regulates,
  isRegulatedBy, recasts, rectifies, agreeWith, hasVersion).
- Scraper `scrape-sparql-relaciones.py` con pagination por URI
  lexicográfico (evita el bug Virtuoso de OFFSET >10k).
- 329k+ edges solo de `modifiesTo` (a medida que termine la pasada).

### MCP `mcp-bcn-leychile` v0.6

**4 tools nuevas** complementan las 3 BCN-remote existentes:

| Tool | Lat. | Descripción |
|---|---|---|
| `lookup_norma` | <10ms | Resuelve por tipo+numero / leychile_code / slug |
| `search_normas` | <50ms | LIKE en título, ordenado por capa DESC |
| `get_relaciones` | <50ms | Edges del grafo BCN (outgoing/incoming/both) |
| `catalog_stats` | <10ms | Totales por tipo + edges |

- `LocalCatalog` (cliente SQLite read-only, 10 tests offline en verde).
- SQLite indexa capa 1 + 2 + 3 unificadamente. Lookup prioriza capa
  alta (3 > 2 > 1) — si hay perfil curado, gana sobre el catálogo.
- Indexer `build-sqlite-catalog.py` deriva `leychile_code` desde
  `fuente_oficial` URL si no está explícito + `numero` desde slug.

### Setup

`chile/scripts/mcp/INSTALL.md` — instrucciones para registrar el MCP
en Claude Code (`claude mcp add bcn-leychile <path>`).

### Aprendizajes técnicos (memoria)

- `reference_bcn_sparql_endpoint.md` — datos.bcn.cl/sparql, 748k
  normas, paginar por tipo o por URI (OFFSET >10k rompe).
- `feedback_no_inventar_ids_urls_referencias.md` (2026-05-20):
  nunca generar IDs/URLs por inferencia cronológica.

## 0.0.15 — 2026-05-19

- **Ley 21.057 — Entrevista Videograbada** (1 archivo capa 3):
  - `leyes/ley-21057-entrevista-videograbada.md` — Resguardo a NNA víctimas
    de delitos sexuales: entrevista investigativa videograbada (EI) por
    entrevistador certificado en sala especializada, declaración judicial
    videograbada en juicio oral, una sola entrevista (evita
    revictimización), profesionales certificados Mintrab+Mineduc+MINSAL.
- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 51 leyes + 3
  skills + setup interview + fuentes.md = 63 archivos curados.

## 0.0.14 — 2026-05-19

- **Cluster DD.HH. específicos** (2 archivos capa 3):
  - `leyes/ley-21331-salud-mental.md` — Derechos en salud mental:
    presunción capacidad jurídica, apoyo en toma de decisiones (no
    sustitución), hospitalización psiquiátrica voluntaria como regla,
    involuntaria solo con autorización judicial + revisión 90 días,
    Comisión Nacional de Protección.
  - `leyes/ley-21120-identidad-genero.md` — Cambio nombre y sexo
    registral: adulto soltero vía SRCEI, adulto casado / adolescente
    vía Tribunal de Familia, sin requisito de cirugía / examen
    psiquiátrico, reserva de cambio anterior, identidad como categoría
    protegida (cruce Ley 20.609).

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 50 leyes + 3
  skills + setup interview + fuentes.md = 62 archivos curados.

## 0.0.13 — 2026-05-19

- **Cluster digital del Estado** (2 archivos capa 3):
  - `leyes/ley-21180-transformacion-digital.md` — Transformación digital
    del Estado: expediente electrónico, notificación electrónica como
    regla, interoperabilidad obligatoria (no pedir info que otro órgano
    ya tiene), ClaveÚnica, PISEE, vigencia escalonada 2020-2024.
  - `leyes/ley-19799-firma-electronica.md` — Firma electrónica simple +
    avanzada (FEA), documento electrónico con equivalencia plena al de
    papel, Entidades Certificadoras acreditadas por Mineco, régimen
    probatorio (FEA = instrumento privado autenticado).

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 48 leyes + 3
  skills + setup interview + fuentes.md = 60 archivos curados.

## 0.0.12 — 2026-05-19

- **Cluster salud + discapacidad + antidiscriminación** (3 archivos
  capa 3 nuevos):
  - `leyes/ley-20584-derechos-deberes-paciente.md` — Ley del Paciente:
    consentimiento informado obligatorio, ficha clínica (propiedad
    prestador, 15 años conservación), voluntad anticipada / LET /
    cuidados paliativos, salud mental Ley 21.331, comité ético
    investigación.
  - `leyes/ley-20422-discapacidad.md` — CDPD ONU implementada, RND +
    COMPIN, accesibilidad universal, ajustes razonables, autismo
    Ley 21.545, inclusión laboral (cruce Ley 21.015) + educacional (PIE).
  - `leyes/ley-20609-no-discriminacion.md` — Ley Zamudio: acción de no
    discriminación arbitraria, 14+ categorías protegidas (sexo,
    orientación, identidad, raza, religión, edad, etc.), juzgado civil
    + 90 días, multa 5-50 UTM, agravante penal Art. 12 N° 21 CP.

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 46 leyes + 3
  skills + setup interview + fuentes.md = 58 archivos curados.

## 0.0.11 — 2026-05-19

- **Cluster probidad + lobby + LGUC** (3 archivos capa 3 nuevos):
  - `leyes/ley-20730-lobby.md` — Lobby: registros públicos audiencias /
    viajes / donativos, sujetos pasivos (Ejecutivo + Legislativo + altos
    cargos), exclusiones, Contraloría + CPLT como fiscalizadores,
    infolobby.cl.
  - `leyes/ley-20880-probidad-publica.md` — Probidad: DIP (Declaración de
    Intereses y Patrimonio) pública, fideicomiso ciego / mandato especial
    para altas autoridades, deberes de abstención, sanciones CGR.
  - `leyes/dfl-458-urbanismo-construcciones.md` — LGUC: planificación
    urbana (PRC, PRI, PRM), permisos DOM (edificación, ampliación,
    regularización, demolición), OGUC (DS 47/1992), responsabilidad civil
    por daños (10/5/3 años según tipo), expropiación.

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 43 leyes +
  3 skills + setup interview + fuentes.md = 55 archivos curados.

- **Catálogo capa 1**: re-run BCN agregó 170 leyes más (total 4.921).

## 0.0.10 — 2026-05-19

- **Cluster laboral colectivo + administrativo + fintec + RPA + climático**
  (5 archivos capa 3 nuevos):
  - `leyes/ley-20940-relaciones-laborales.md` — Reforma 2016: titularidad
    sindical, piso de negociación, servicios mínimos, prohibición de
    reemplazo en huelga, fueros, prácticas antisindicales.
  - `leyes/ley-18575-bases-administracion-estado.md` — LOC: principios
    (servicio a persona, probidad, eficiencia, transparencia, control
    jerárquico), organización, declaración intereses Ley 20.880.
  - `leyes/ley-21521-fintec.md` — Marco Fintec 2023: 7 categorías licencias
    CMF, Sistema Financiero Abierto, iniciación de pagos, cruce con LPDP
    + AML + ciberseguridad.
  - `leyes/ley-20084-rpa.md` — Responsabilidad Penal Adolescente 14-18:
    sanciones diferenciadas, internación cerrada/semicerrada hasta 5/10
    años, Servicio Nacional de Reinserción Social Juvenil.
  - `leyes/ley-21455-cambio-climatico.md` — Marco 2022: carbono neutralidad
    2050, NDC, presupuesto de carbono nacional + sectorial, planes
    sectoriales mitigación + adaptación.

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 40 leyes + 3
  skills + setup interview + fuentes.md = 52 archivos curados.

## 0.0.9 — 2026-05-19

- **Cluster orgánico + NNA + migratorio + ciberseguridad** (4 archivos capa 3):
  - `codigos/codigo-organico-tribunales.md` — Ley 7.421/1943: estructura
    judicial, competencia absoluta vs relativa, prórroga, implicancias vs
    recusaciones, notarios + conservadores + abogados.
  - `leyes/ley-21430-garantias-nna.md` — Convención Derechos del Niño
    implementada, Sistema de Garantías, OLN, Servicio Mejor Niñez, derecho
    a ser oído + autonomía progresiva, interés superior NNA.
  - `leyes/ley-21325-extranjeria.md` — SERMIG, residencia temporal +
    definitiva, refugio Ley 20.430, no devolución, reunificación familiar,
    expulsión administrativa, reconducción inmediata.
  - `leyes/ley-21663-ciberseguridad.md` — Ley Marco 2024: ANCI, OIV +
    ICI, notificación incidentes 3hrs/72hrs, CSIRT nacional, multas
    hasta 40.000 UTM.

- **Cobertura capa 3 ahora**: 1 Constitución + 7 códigos + 35 leyes +
  3 skills + setup interview + fuentes.md = 47 archivos curados.

## 0.0.1 — 2026-05-18

- Fork inicial de `anthropics/claude-for-legal`.
- Carpeta `chile/` creada con esqueleto: `README.md`, `CLAUDE.md` general,
  este `CHANGELOG.md`.
- Estado: WIP. Perfiles por rama del derecho pendientes de redacción y de
  revisión por abogado habilitado.

## 0.0.8 — 2026-05-19

- **Cluster regulatorio + penal especial + previsional + familia** (7 leyes
  nuevas capa 3):
  - `dl-211-libre-competencia.md` — FNE + TDLC, colusión / abuso posición
    dominante, control de fusiones (Ley 20.945), delación compensada,
    colusión como delito penal (Cat. 1 de Ley 21.595).
  - `ley-20000-drogas.md` — tráfico, microtráfico (Art. 4), distinción con
    consumo personal, agente encubierto, entrega vigilada, comiso, Ley 21.020
    cannabis medicinal.
  - `ley-20066-vif.md` — VIF: sujetos protegidos Art. 5, maltrato habitual
    (Art. 14 — delito), medidas cautelares Art. 9, femicidio (Ley 21.212),
    circuito familia/penal.
  - `dl-3500-pensiones.md` — sistema AFP, cotización 10%, fondos A-E, PGU
    (Ley 21.419), cotización obligatoria independientes, reforma 2024-2026
    en debate.
  - `ley-18168-telecomunicaciones.md` — concesiones SUBTEL, neutralidad de
    red (Ley 20.453 — primera en el mundo), Ley 21.541 Acceso Universal a
    Internet, sanciones SUBTEL hasta 30.000 UTM.
  - `ley-19728-seguro-cesantia.md` — AFC, CIC + FCS, cotización 2,4%/0,6%
    indefinido vs 3%/0% plazo fijo, giro decreciente, Ley 21.227 protección
    empleo (COVID).

- **Cobertura capa 3 ahora**: 1 Constitución + 6 códigos + 32 leyes + 3 skills
  + setup interview + fuentes.md.

## 0.0.7 — 2026-05-19

- **Cluster compliance + IP + transparencia** (capa 3, 8 archivos nuevos):
  - `leyes/ley-20285-transparencia.md` — Transparencia activa + SAI, CPLT,
    amparo, causales reserva Art. 21, plazos 20+10 días hábiles.
  - `leyes/ley-20393-rppj.md` — Responsabilidad penal personas jurídicas:
    MPD, Encargado de Prevención, catálogo de delitos (ampliado 21.595),
    penas (multa, disolución, inhabilitación contratar Estado).
  - `leyes/ley-21595-delitos-economicos.md` — Reforma estructural penal 2023:
    4 categorías de delitos económicos, multas hasta 60.000 UTM, comiso
    valor equivalente, restricciones beneficios alternativos.
  - `leyes/ley-18045-mercado-valores.md` — LMV: oferta pública, hecho
    esencial, insider trading (Art. 165), manipulación bursátil, OPA
    obligatoria, Ley 21.314 gob. corp., Ley 21.521 Fintec.
  - `leyes/ley-19039-propiedad-industrial.md` — Marcas (10 años renovables),
    patentes (20 años), modelos utilidad, diseños, INAPI, TPI, Ley 21.355.
  - `leyes/ley-17336-propiedad-intelectual.md` — Derecho de autor + conexos,
    plazo vida+70, derechos morales + patrimoniales, software Art. 88,
    excepciones (cita, parodia, educación).
  - `leyes/ley-19913-lavado-activos.md` — UAF, ROS, sujetos obligados,
    diligencia debida PEP, GAFI, multas administrativas.
  - `leyes/ley-14908-alimentos.md` — Pensión 40% IMR, alimentos provisorios
    + definitivos, apremios (arraigo, suspensión licencia/pasaporte/arresto),
    RNDPA (Ley 21.389), GAM (Ley 21.515).
- **Cobertura capa 3 ahora**: 1 Constitución + 6 códigos + 25 leyes + 3 skills
  + setup interview + fuentes.md.

## 0.0.6 — 2026-05-18

- **Cluster procesal/familia/ambiental** (capa 3 borrador):
  - `leyes/ley-19968-tribunales-familia.md` — Tribunales de Familia,
    procedimiento ordinario, mediación obligatoria, medidas de protección NNA.
  - `leyes/ley-19947-matrimonio-civil.md` — Matrimonio civil con Ley 21.400
    matrimonio igualitario, divorcio mutuo acuerdo (1 año) vs unilateral (3),
    compensación económica, regímenes patrimoniales.
  - `leyes/ley-19300-medio-ambiente.md` — SEIA (DIA vs EIA), institucionalidad
    MMA/SMA/SEA/Tribunales Ambientales, sanciones SMA, delitos ambientales
    Ley 21.595, acción de reparación por daño.
- **Cobertura capa 3 ahora**: 1 Constitución + 6 códigos + 17 leyes + 3 skills
  + setup interview + fuentes.md.

## 0.0.5 — 2026-05-18

- **Skills transversales publicados** en `chile/skills/`:
  - `diagnostico.md` — protocolo de 6 pasos (jurisdicción, rama, normas,
    vigencia, complejidad, declaración) que el sistema corre antes de toda
    respuesta.
  - `citas-verificables.md` — formato canónico por tipo (constitucional,
    código, ley, jurisprudencia CS/CA/TC/TDLC/JL, doctrina administrativa
    DT/SII/CGR/CMF/SUSESO) + niveles de verificación (✅/🟨/🟧/🟥).
  - `plazos.md` — distinción días corridos vs hábiles, sábado no hábil (CPC
    Art. 66), feriado judicial, plazos críticos por rama.
- **`chile/fuentes.md`** — mapa de fuentes autoritativas (BCN, DO, PJUD, TC,
  TDLC, DT, SII, Contraloría, CMF, SUSESO, SERVEL, Registro Civil) con URLs y
  reglas de citación.
- **`chile/setup-interview.md`** y `chile/setup-output-TEMPLATE.md` — entrevista
  cold-start de 15 preguntas en 6 bloques que genera CLAUDE.md personalizado
  para la firma/práctica del usuario.
- **Cluster civil/tributario foundational** (capa 3, borrador):
  - `codigos/codigo-civil.md` — Andrés Bello 1855, 60+ artículos clave
    indexados, reformas 2014-2023.
  - `codigos/codigo-tributario.md` — DL 830, 30+ artículos clave, reforma
    21.713 anotada.
  - `leyes/dl-824-renta.md` — LIR completa: regímenes 14A/14D ProPyme, II Cat.,
    Global Compl., Adicional, retenciones, prescripción.
  - `leyes/dl-825-iva.md` — IVA 19%, débito/crédito fiscal, DTE, servicios
    digitales (Ley 21.210/21.713), exenciones, exportaciones.
  - `leyes/ley-19886-compras-publicas.md` — Bases, modalidades, ChileCompra,
    TCP, plazos.
- **Cobertura capa 3 actual**: 1 Constitución + 4 códigos + 13 leyes = 18
  archivos capa 3 borrador.

## 0.0.4 — 2026-05-18

- **Constitución Política de la República** publicada (`constitucion/constitucion-politica.md`),
  base de todo el ordenamiento; índice de Capítulos I-XVI, Art. 19 con 26 numerales
  tabulados, Recurso de Protección (Art. 20), inaplicabilidad por
  inconstitucionalidad, Art. 5 inc. 2° sobre tratados de DD.HH.
- **Estrategia de tres capas** documentada como ADR-0002 en el STD wrapper. Define
  cómo escalar el corpus: capa 1 catálogo auto (BCN scraping), capa 2 estructural
  semi-auto, capa 3 análisis operativo curado + validado. Frontmatter `capa: N`
  agregado en archivos curados.
- **Cluster civil/comercial inicial**: `codigo-comercio.md` (actos de comercio,
  sociedades de personas, materias migradas a leyes especiales) +
  `ley-18046-sociedades-anonimas.md` (gobierno corporativo, OPR, OPA, deberes
  fiduciarios) + `ley-19496-consumidor.md` (LPC: cláusulas abusivas, garantía legal,
  SERNAC Financiero, retracto).
- **Cobertura ampliada**: ahora 1 Constitución + 2 códigos + 11 leyes = 14 archivos
  capa 3 borrador. Cubre operativamente: laboral, privacidad, B2C, societario, marco
  constitucional.

## 0.0.3 — 2026-05-18

- **Cluster laboral completo en el corpus** (todos en `borrador-no-validado`):
  - `leyes/ley-16744-accidentes-trabajo.md` — seguro social, Mutuales, DIAT, DS 40/54
  - `leyes/ley-20123-subcontratacion.md` — responsabilidad subsidiaria/solidaria, F30,
    EST
  - `leyes/ley-21561-reduccion-jornada.md` — calendario 45→44→42→40h hasta 2028
  - `leyes/ley-21220-teletrabajo.md` — pacto, derecho a desconexión, reversibilidad
  - `leyes/ley-21015-inclusion-laboral.md` — cuota 1% en empresas 100+
- **Cobertura laboral actual**: Código del Trabajo + 6 leyes especiales (16.744,
  20.123, 21.015, 21.220, 21.561, 21.643). Permite responder consultas operativas
  laborales típicas (terminación, jornada, subcontratación, teletrabajo, acoso,
  accidentes, inclusión) sin gaps mayores.
- **Total corpus publicado**: 1 código + 8 leyes (9 archivos, todos
  `borrador-no-validado`).

## 0.0.2 — 2026-05-18

- **Pivot arquitectónico**: el corpus normativo (códigos, leyes, decretos) pasa a ser
  el eje del sistema, en lugar de perfiles por rama. Coherente con tradición civil law
  chilena.
- Estructura `chile/normativa/{codigos,leyes,decretos,dictamenes}` creada con índices.
- Estructura `chile/{perfiles,skills,ejemplos}` creada para vistas/skills/casos.
- Esquema de archivo de norma definido en `normativa/README.md` (frontmatter con
  vigencia, modificaciones, estado de revisión, conexiones).
- Primeros 4 archivos de norma publicados (todos `borrador-no-validado`):
  - `leyes/ley-19628-proteccion-datos.md` (LPD vigente)
  - `leyes/ley-21719-modificacion-lpd.md` (modificación + APDP, vigencia 2026-12-01)
  - `leyes/ley-21643-acoso-laboral.md` (Ley Karin)
  - `codigos/codigo-trabajo.md` (DFL 1/2002, ~22 artículos clave indexados)
- Índices de leyes (19 entradas), códigos (12) y decretos (4) listados con estado.
- `CLAUDE.md` general actualizado para apuntar al corpus normativo como spine.
- `README.md` reescrito para explicar la arquitectura normativa-spine y diferenciación
  vs el fork argentino.
