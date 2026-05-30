#!/bin/bash
# Mantiene la GPU (bge-m3 vía túnel) embebiendo las fuentes nuevas SIN pausa.
# Cada vuelta embebe lo nuevo de cada fuente (idempotente); duerme corto y
# revisita, así a medida que los scrapers llenan, se va embebiendo. Loop infinito.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
EMB="python3 scripts/embed-new-source.py"
cycle=0
while true; do
  cycle=$((cycle+1))
  echo "===== $(date '+%H:%M:%S') ciclo $cycle ====="
  $EMB --src data/cgr-dictamenes/dictamenes --glob '*.txt'  --source cgr-dictamenes --batch 16 --workers 8
  $EMB --src data/dt                         --glob '*.html' --source dt             --batch 16 --workers 8
  $EMB --src data/dga/pdfs                   --glob '*.pdf'  --source dga            --batch 8  --workers 6
  $EMB --src data/subtrans/pdfs              --glob '*.pdf'  --source subtrans       --batch 8  --workers 6
  $EMB --src data/cde/pdfs                   --glob '*.pdf'  --source cde            --batch 8  --workers 6
  sleep 30
done
