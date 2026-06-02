#!/bin/bash
# 🥇 Persistencia leychile: re-corre el scraper (con rotación de geos) hasta que
# una pasada completa no baje NADA nuevo (solo quedan 404s o bans en TODAS las geos).
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
export ZYTE_API_KEY=$(grep '^ZYTE_API_KEY' .env | cut -d= -f2)
prev=0
while true; do
  python3 scripts/bulk-downloaders/leychile-bulk.py --workers 6 --zyte
  now=$(sqlite3 data/leychile/manifest.sqlite3 "SELECT COUNT(*) FROM normas WHERE downloaded=1;")
  echo "===== pasada completa · downloaded=$now (antes=$prev) · $(date '+%H:%M:%S') ====="
  [ "$now" -le "$prev" ] && { echo "Sin progreso nuevo → leychile COMPLETO (lo que falta son 404/bans-todas-las-geos)"; break; }
  prev=$now
  sleep 10
done
