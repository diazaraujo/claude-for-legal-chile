#!/bin/bash
# Refresh de fuentes que Raúl deja en Enigma (Tribunal Ambiental + recursos SEA).
# rsync es incremental por diseño (solo trae archivos nuevos/cambiados). Luego
# extrae texto de los PDFs nuevos. El embed/index lo hace refresh-downstream.sh.
# Ver REFRESH-PLAN.md §5 + reference_tribunal_ambiental_sofofa_source.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
unset SSH_AUTH_SOCK
RS="rsync -az --partial -e 'ssh -o BatchMode=yes -o ConnectTimeout=20'"

echo "=== rsync incremental SOFOFA desde Enigma (10.0.0.3) ==="
eval $RS antonio@10.0.0.3:/mnt/data/sofofa-archivos-txt/TA/                       'data/tribunal-ambiental/'        || true
eval $RS antonio@10.0.0.3:/mnt/data/sofofa-archivos-respaldo/TA/sentencias/        'data/tribunal-ambiental/sentencias-pdf/' || true
eval $RS antonio@10.0.0.3:/mnt/data/sofofa-archivos-respaldo/recursos_administrativos/documentos/ 'data/recursos-administrativos/' || true

echo "=== extraer texto de PDFs nuevos (pdftotext + OCR fallback) ==="
nice -n 10 python3 scripts/extract-pdf-text.py --src data/recursos-administrativos --workers 4 || true
nice -n 10 python3 scripts/extract-pdf-text.py --src data/tribunal-ambiental/sentencias-pdf --workers 3 || true
echo "=== rsync-enigma completo · $(date '+%H:%M:%S') ==="
echo "→ el embed/index de lo nuevo lo hace refresh-downstream.sh (embed-loop auto-descubre los .txt/.pdf.txt nuevos)"
