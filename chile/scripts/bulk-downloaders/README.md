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

## Próximas fuentes (mismo patrón)

- `sii-bulk.py`: circulares + oficios SII (~30 años, ~1500 PDFs)
- `tdlc-bulk.py`: 213 sentencias × PDFs anexos
- `cgr-bulk.py`: dictámenes CGR por año
- `cmf-bulk.py`: NCG + Circulares CMF
- `tc-bulk.py`: TC legacy IDs 1..12000
- `dt-bulk.py`: dictámenes DT por año
- `sernac-bulk.py`: circulares + dictámenes interpretativos
