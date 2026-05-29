# Coverage status — corpus.fts (verificado)

> Verificado uno a uno contra `chile/data/_index/corpus.fts.sqlite3` (1.280.786 docs)
> el 2026-05-29. Conteo por substring de path en `docs_meta`. Reemplaza estimaciones
> previas no verificadas.

## Fuentes presentes (no rehacer)

| Fuente | docs | nota |
|---|---:|---|
| PJUD (juris.pjud.cl Solr) | 921.701 | Familia/C.Suprema/Laborales/Cobranza; scrape Apelaciones/Civiles/Penales ampliando a ~2M+ en enigma |
| CGR fiscalizaciones | 127.608 | general/municipalidades/no-municipales |
| CPLT (Ley 20.285) | 103.864 | 2010–2025 |
| SUSESO dictámenes | 16.021 | desde 2006 |
| TTA (trib. tributarios y aduaneros) | 7.883 | revisar completitud histórica |
| DT dictámenes | 2.035 | parcial vs universo DT |

## Gaps reales (a construir / completar)

| Fuente | docs | acción |
|---|---:|---|
| TRICEL | 502 | parcial — revisar completitud |
| TCP boletines | 5 | +662 PDFs bajados (boletines/otros/estado-diario); **sentencias** vía `tcp.lexsoft.cl` (SPA pública, REST por ingeniería inversa) — pendiente |
| Cortes Marciales / Justicia Militar | 4 | 2.226 PDFs escaneados; OCR (pdftoppm+tesseract) en curso → indexar post-rsync |
| DGA (aguas) | 4 | casi nada — scraper pendiente |
| **CDE** (Consejo Defensa del Estado) | 0 | ausente — scraper pendiente |
| **SAG** | 0 | ausente — scraper pendiente |
| **SUBTRANS** | 0 | ausente — scraper pendiente |

## Notas
- **PJUD pre-2005**: el buscador juris.pjud.cl arranca en 2005; histórico previo existe en otros canales (no en este índice). Verificar contra el manifest del scraper, no contra paths.
- **Gap C**: ~6k normas que Zyte no pudo bajar (probable sin XML público en LeyChile).
- `estadisticaservices.pjud.cl` = API de **estadísticas** judiciales (caseload, no texto de fallos). Fuente distinta; no es corpus de jurisprudencia.
