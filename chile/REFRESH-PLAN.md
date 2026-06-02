# Plan de Refresh del Corpus — claude-for-legal-chile

> Objetivo: mantener el corpus (51 fuentes, ~4,7M docs + derivados LLM) **actualizado de forma
> incremental, automática y verificada**, sin re-descargar el histórico. Generado 2026-06-02.

## 0. Principios (reglas de oro aplicadas)

1. **Incremental, nunca full**: cada fuente trae solo lo nuevo desde un cursor (última fecha / max id / `modified_after` / max_updated_at). NO re-descargar histórico. (`feedback_buk_incremental_only`, `feedback_ingesta_dia_a_dia`)
2. **Reverse cronológico**: lo más reciente primero — si un batch cae, lo de mayor valor ya quedó. (`feedback_ingest_reciente_a_viejo`)
3. **Verificar DATA REAL, no error**: mirar contenido (no 0-byte/HTML-error), delta de conteo sube, probe post-ingesta. (`feedback_verificar_data_real_no_error`)
4. **Idempotente + persistente**: manifests con `downloaded`/cursor, skip lo hecho, geo-rotation anti-ban + loop hasta bajar todo. (`feedback_persistencia_rotacion_geo_antiban`)
5. **Cómputo en enigma** (RTX 5090) para embed/LLM vía túnel; Mac orquesta scraping/CPU. (`reference_legal_chile_compute_enigma`)
6. **Cobertura total**: toda la data, no muestras. El refresh no recorta. (`feedback_data_completa_no_muestras`, `feedback_corpus_legal_chile_completo`)

## 1. Taxonomía de fuentes por cadencia + mecanismo incremental

### 🔴 DIARIO (alto flujo — corre todos los días)
| Fuente | Mecanismo incremental | Cursor | Scraper |
|---|---|---|---|
| **Diario Oficial** (electrónica) | nueva edición/día hábil | última fecha en manifest | `diario-oficial-bulk.py --from <last+1> --to today` |
| **Boletín Concursal** | publicaciones diarias | última fecha publicación | `boletin-concursal-bulk.py` (POST por fecha nueva) |
| **PJUD jurisprudencia** | sentencias nuevas (Solr `fec_actualiza`) | max `sent__fec_actualiza_dt` por competencia | `scrape-pjud-juris.py` con filtro `fec_actualiza > cursor` |

### 🟠 SEMANAL (flujo medio)
| Fuente | Mecanismo | Cursor | Scraper |
|---|---|---|---|
| **leychile/BCN** | normas nuevas + versiones modificadas | max idNorma + `fechaVersion` modificadas (SPARQL/catálogo) | `leychile-bulk.py` (geo-rotation) |
| **Dictámenes** CGR / CPLT / SUSESO / DT | nuevos dictámenes | `--from-year`/`--from-id` del último | `cgr-dictamenes`, `cplt --from-id`, `suseso`, `dt-bulk` |
| **Jurisprudencia esp.** TTA / TDLC / Trib.Ambiental / recursos-SEA / TCP / TRICEL | nuevas sentencias | último id/fecha | scrapers respectivos (WP-REST/bulk/rsync Enigma) |
| **Jurisprud. adm.** SII oficios / Aduanas / SERNAC | nuevos | `--desde-anio`/`--since` | `sii-oficios`, `aduanas`, `sernac` |

### 🟡 MENSUAL (flujo bajo)
- Doctrina (universidades, OAI-PMH `from=` date), Normativa sectorial (SEC, SUBTEL, DGA, SUBTRANS, SAG, SERVEL, SUPEREDUC, SUPERDESALUD, SPENSIONES, UAF, SISS), TC / TC-moderno / cortes-marciales / TDPI, INDH, DPP, CMF, SII-normativa, historia-ley (`--from-year`).

### ⚪ ESTÁTICO (sin refresh)
- **Diario Oficial histórico 1877-2016** — backfill único; no cambia. (Completar el backfill pendiente, después nunca más.)

## 2. Pipeline de refresh por documento nuevo (las 6 etapas)

Cada fuente, tras traer lo nuevo, alimenta este pipeline (solo sobre el delta):

```
(1) DESCARGA incremental ──► (2) EXTRACCIÓN texto ──► (3) FTS index + EMBED ──►
(PDF→pdftotext; OCR pdftoppm+tesseract       (bge-m3 enigma; embed-loop/embed-new-source
 para escaneados; .txt directo)               toma data/<fuente>/ nuevo automáticamente)

──► (4) LLM EXTRACT (solo sentencias pjud nuevas) ──► (5) RE-AGREGACIÓN perfiles ──► (6) VERIFICACIÓN
     FASE1 partes (qwen) + resultado            jueces/empresas/tribunales      coverage-map +
     laboral/penal (qwen/llama) del delta       (re-run incremental)            audit-embeddings + frescura
```

- Etapa 3: `embed-loop.sh` ya auto-descubre `data/*/` → lo nuevo se embebe solo. Concursal: `embed-concursal.py` (registros nuevos).
- Etapa 4: solo aplica a pjud (las otras fuentes no necesitan extracción de partes/resultado). Procesa solo `sent_id` no en `fase1_done`/`laboral_resultado`/`penal_resultado` (idempotente por diseño).
- Etapa 5: `aggregate-empresas-laboral.py` + `aggregate-jueces.py` (re-run completo, son rápidos en CPU; o incremental si crece).
- Etapa 6: `generate-coverage-map.py` + `audit-embeddings.py` + chequeo de **frescura por fuente** (alertar si una fuente diaria lleva >2 días sin delta esperado).

## 3. Orquestación

### Estructura a construir: `scripts/refresh/`
- `refresh-source.py <fuente>` — wrapper genérico: lee cursor del manifest → corre scraper incremental → verifica delta real → dispara extracción texto → marca cursor nuevo. Idempotente + geo-rotation + persistencia donde aplique.
- `refresh-daily.sh` — Diario Oficial + Concursal + PJUD. Luego embed delta + LLM extract pjud delta.
- `refresh-weekly.sh` — leychile + dictámenes + jurisprudencia especial + jurisprud. adm.
- `refresh-monthly.sh` — doctrina + normativa sectorial + resto.
- `refresh-downstream.sh` — embed nuevos (enigma) → LLM extract pjud delta → re-agregar perfiles → coverage map + audit. Corre al final de cada refresh.

### Scheduling (cron en el Mac; cómputo pesado → enigma vía túnel)
```
# crontab (hora Chile)
0 6  * * *   refresh-daily.sh    >> /var/log/legal-refresh-daily.log   # 06:00 todos los días
0 5  * * 1   refresh-weekly.sh   >> .../weekly.log                     # lunes 05:00
0 4  1 * *   refresh-monthly.sh  >> .../monthly.log                    # día 1, 04:00
*/30 * * * * check-tunnel-enigma.sh                                    # túnel SSH vivo
```
Alternativa a cron: un daemon de persistencia (estilo `retry-pending-all.py`) que cicla por fuente según cadencia. Cron es más simple y observable.

### Asignación de cómputo
- **Mac**: orquestación, scraping (Zyte/HTTP), extracción de texto (pdftotext/OCR), agregaciones (CPU).
- **Enigma (RTX 5090)**: embeddings bge-m3 + LLM extract (qwen2.5:14b / llama3.1:8b) vía túnel `localhost:11435`. El túnel debe estar vivo (check cada 30min).

## 4. Verificación y monitoreo (no declarar actualizado sin evidencia)

Tras cada refresh:
1. **Delta real por fuente**: conteo subió y el contenido es válido (no 0-byte/HTML-error). Log con counters diferenciales.
2. **Frescura**: `frescura_dias` por fuente vs su cadencia esperada. Alertar si una diaria lleva >2 días sin delta (puede ser fin de semana/feriado — ver `reference_chile_fiestas_patrias_semana`, no marcar falso positivo en días sin actividad esperada).
3. **Coverage map + audit-embeddings**: regenerar; confirmar 0 gaps de embedding (todo lo descargado, embebido).
4. **Bans**: si una fuente Zyte acumula `ban=` alto, la geo-rotation falló → escalar geos/estrategia. NO dejar el hueco.
5. **Reporte**: resumen diario de deltas + frescura + gaps (puede ir a un log o a un canal).

## 5. Casos especiales

- **leychile versiones modificadas**: una norma puede tener una versión nueva (texto refundido) sin cambiar idNorma. El refresh debe detectar `fechaVersion` > la guardada y re-bajar esa norma. (Relevante para `legal_citar_solo_vigente`.)
- **PJUD anonimización retroactiva**: el Comité Editorial (Acta 164-2024) puede ampliar anonimización → re-bajar sentencias cuyo `sit_fallo_anonimizado_i` cambió. (`reference_pjud_analitica_dashboard`)
- **Concursal**: re-embeber registros nuevos (`embed-concursal.py` idempotente).
- **Recursos SEA / Tribunal Ambiental**: vienen vía rsync de Enigma (Raúl los deja) → el refresh re-rsyncea + extrae + embebe lo nuevo.

## 6. Roadmap de implementación (prioridad)

1. **[P0] Completar el estado actual**: leychile al 100% (geo-rotation corriendo), concursal embebido, FASE1/laboral/penal terminados. (En curso.)
2. **[P0] `refresh-source.py` genérico + cursores estándar** en los manifests (last_run, cursor). La mayoría de scrapers ya tienen `--from*`; falta estandarizar la lectura/escritura del cursor.
3. **[P1] `refresh-daily.sh` + `refresh-downstream.sh`** — las 3 diarias (DO, concursal, pjud) + embed/extract/aggregate del delta. Cron 06:00.
4. **[P1] PJUD incremental por `fec_actualiza`** — confirmar que `scrape-pjud-juris.py` soporta filtro incremental; si no, agregarlo.
5. **[P2] weekly + monthly** + verificación de frescura + alertas.
6. **[P2] leychile versiones modificadas** + PJUD anonimización retroactiva.
7. **[P3] Dashboard de frescura** — vista "última actualización por fuente" (extensión del coverage map).

## 7. Resumen de cadencias

| Cadencia | Fuentes | Acción |
|---|---|---|
| Diaria 06:00 | Diario Oficial, Boletín Concursal, PJUD | descarga delta → texto → embed → LLM extract (pjud) → agregar → verificar |
| Semanal lun 05:00 | leychile, dictámenes, jurisprudencia especial, jurisprud. adm. | descarga delta → texto → embed → verificar |
| Mensual día-1 04:00 | doctrina, normativa sectorial, TC, resto | descarga delta → texto → embed → verificar |
| Continuo (30min) | túnel enigma, procesos LLM vivos | health-check + relaunch |
| Nunca | DO histórico 1877-2016 | estático tras backfill |
