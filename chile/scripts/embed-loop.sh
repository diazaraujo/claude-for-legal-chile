#!/bin/bash
# Mantiene la GPU (bge-m3 vía túnel) embebiendo TODA la data bajada, sin pausa.
# Cubre todas las fuentes de data/ (txt/html/pdf). embed-new-source salta lo ya
# embebido en el master (corpus.fts) y en el índice local → embebe solo el gap
# real. Loop hasta terminar: cuando todo está embebido, los ciclos son rápidos
# (todo skip) + sleep; a medida que los scrapers llenan, lo nuevo se embebe.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
EMB="python3 scripts/embed-new-source.py"
cycle=0
while true; do
  cycle=$((cycle+1))
  echo "===== $(date '+%H:%M:%S') ciclo $cycle ====="
  for d in data/*/; do
    name=$(basename "$d")
    [ "$name" = "_index" ] && continue
    for ext in txt html htm pdf xml; do
      [ -n "$(find "$d" -name "*.$ext" -print -quit 2>/dev/null)" ] || continue
      $EMB --src "$d" --glob "*.$ext" --source "$name" --batch 16 --workers 8
    done
  done
  echo "----- ciclo $cycle completo, sleep 30s -----"
  sleep 30
done
