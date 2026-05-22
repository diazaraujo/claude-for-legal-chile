# Bulk downloaders

Scripts standalone para descargar el **histórico completo** de fuentes
chilenas, en **2 fases** (feedback Antonio 2026-05-22):

1. **Fase 1: metadata-only** — `--skip-pdfs`, recorre toda la fuente
   en minutos. Valida cobertura + genera manifest SQLite.
2. **Fase 2: PDFs reverse chronological** — por default `to → from`,
   prioriza material reciente (mayor valor jurídico).

Ver memoria persistente `feedback-bulk-estrategia-2fases` para detalle.

## diario-oficial-bulk.py

### Fase 1 (recomendada primero)

```bash
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --skip-pdfs --workers 8 --rate-seconds 0.3
```

Estimación: ~2.500 días hábiles, ~4 minutos, sin uso de disco
(solo manifest SQLite + JSONL per edition).

### Fase 2 (después de validar Fase 1)

```bash
# Default: reverse (hoy → atrás)
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --workers 8 --rate-seconds 0.5

# Forward (origen → hoy) explícito
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --workers 8 --rate-seconds 0.5 --forward
```

Estimación: ~60k PDFs, ~10 GB, ~1 hora con 8 workers.

### Idempotencia + resume

Manifest SQLite en `chile/data/diario-oficial/manifest.sqlite3`:
- Ediciones con `status='ok'` se saltean en runs subsecuentes.
- PDFs ya en disco se saltean.
- Si el script cae a mitad, simplemente re-lanzar el mismo comando.

### Output

```
chile/data/diario-oficial/
├── manifest.sqlite3
└── YYYY/MM/DD/edicion_NNNNN/
    ├── publicaciones.jsonl
    ├── sumario.pdf
    └── {CVE}.pdf  × ~25
```

## Estado al 2026-05-22

| Bulk | Estado | Docs | Tamaño | Notas |
|---|---|---:|---:|---|
| `diario-oficial-bulk.py` | ✅ Fase 2 done | 37.676 PDFs | 19.8 GB | 2.125 ediciones desde 2014 |
| `tc-bulk.py` | ✅ Completo | 8.081 PDFs | 4.25 GB | UA matters: usar mismo del MCP |
| `dt-bulk.py` | 🟡 Fase 2 en curso | 4.974 enum / N descargados | — | Period_id enumerator + requests session |
| `sii-bulk.py` | ✅ Completo | 596 PDFs | 159 MB | Solo años 2013+ en web |
| `tdlc-bulk.py` | ✅ Completo | 332 PDFs | 142 MB | WP REST API limpio |
| `cmf-bulk.py` | ✅ Completo | 301 PDFs | 240 MB | workers=4 (16 daba 60% 404) |
| `sernac-bulk.py` | ✅ Completo | 127 PDFs | 309 MB | Circulares + dictámenes |
| `subtel-bulk.py` | ✅ Completo | 71 PDFs | 20 MB | res. exentas + decretos supremos |
| `cgr-bulk.py` | 🔴 Bloqueado | — | — | robots.txt Disallow:/, IDs no-secuenciales |

**Total al cierre**: ~52.158 documentos / ~24.9 GB en 8 fuentes operativas.

## Issues comunes y soluciones

1. **SQLite database malformed**: `PRAGMA journal_mode=WAL` + connection-per-thread.
2. **User-Agent rechazado silenciosamente**: usar el mismo UA que el cliente del MCP (no añadir "bulk-X").
3. **Form sin paginación real**: site puede tener límite implícito (DT 57); investigar antes de batch.
4. **DT 302 redirects bloquean urllib**: usar `requests.Session` per-thread con `max_redirects=3` y `timeout=(connect, read)`.
5. **HTML hrefs relativos resuelven a root, no al path**: en Subtel `images/...` resuelve a `BASE + /images/`, no a `BASE + /path/images/`.
6. **CGR `robots.txt: Disallow: /`** + IDs hash-like → enumeración inviable sin autenticación al Lotus Notes interno.
