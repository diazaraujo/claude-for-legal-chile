# Bulk downloaders

Scripts standalone para descargar el **histórico completo** de fuentes
chilenas — aplicando feedback "toda la data, no muestras".

## diario-oficial-bulk.py

Descarga toda la edición electrónica del Diario Oficial (desde
17-08-2016 hasta hoy).

### Uso

```bash
# Smoke test (1 día, ~4 MB)
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --from 22-05-2026 --to 22-05-2026 \
  --workers 4 --rate-seconds 0.3

# Histórico completo (~2200 ediciones, ~55k PDFs, ~10 GB, ~1.5h)
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --workers 8 --rate-seconds 0.5

# Solo metadata (sin PDFs, rápido)
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --skip-pdfs --workers 8

# Rango específico
python3 chile/scripts/bulk-downloaders/diario-oficial-bulk.py \
  --from 01-01-2024 --to 31-12-2024 \
  --workers 8 --rate-seconds 0.5
```

### Output

```
chile/data/diario-oficial/
├── manifest.sqlite3              # tracking: status por edición
└── YYYY/MM/DD/
    └── edicion_NNNNN/
        ├── publicaciones.jsonl   # metadata estructurada
        ├── sumario.pdf            # tabla contenidos
        └── {CVE}.pdf              # cada publicación
```

### Características

- **Idempotente**: skip ediciones ya en manifest + PDFs ya en disco.
- **Resume**: si se interrumpe, retomar con el mismo comando.
- **Paralelo**: ThreadPoolExecutor configurable (default 8 workers).
- **Rate limit por worker**: respetuoso con BCN.
- **Manifest SQLite**: tracking + reportes.

### Estimación de recursos

| Métrica | Valor |
|---|---|
| Ediciones (días hábiles 2016-2026) | ~2.500 |
| Publicaciones promedio/edición | ~25 |
| Total PDFs | ~60.000 |
| Tamaño promedio/PDF | ~180 KB |
| Total | **~10 GB** |
| Tiempo con 8 workers, rate 0.5s | **~2 horas** |
