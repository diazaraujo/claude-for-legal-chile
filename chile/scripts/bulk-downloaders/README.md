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

| Bulk | Estado | PDFs | Notas |
|---|---|---:|---|
| `diario-oficial-bulk.py` | 🟡 Fase 2 en curso | ~12k de ~38k | Run de ~50 min total |
| `sii-bulk.py` | ✅ Completo | 596 / 159 MB | Solo años 2013+ en web |
| `tdlc-bulk.py` | ✅ Completo | 332 / 142 MB | WP REST API limpio |
| `sernac-bulk.py` | ✅ Completo | 127 / 309 MB | Circulares + dictámenes |
| `tc-bulk.py` | 🟡 75% en curso | ~5500 ok / ~3300 404 | UA matters: usar mismo del MCP |
| `cgr-bulk.py` | 🔴 Pendiente rediseño | — | Números no-secuenciales (~50% 404) |
| `cmf-bulk.py` | 🔴 Pendiente | — | High error rate workers=16; bajar |
| `dt-bulk.py` | 🔴 Form no filtra fechas | ~40 únicos | DT search siempre devuelve mismos |

## Issues comunes y soluciones

1. **SQLite database malformed**: `PRAGMA journal_mode=WAL` + connection-per-thread.
2. **User-Agent rechazado silenciosamente**: usar el mismo UA que el cliente del MCP (no añadir "bulk-X").
3. **Form sin paginación real**: site puede tener límite implícito (DT 57); investigar antes de batch.
