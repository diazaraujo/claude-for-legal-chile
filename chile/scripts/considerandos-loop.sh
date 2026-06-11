#!/bin/bash
# Embebe TODOS los considerandos pendientes (~4,9M chunks) en pasadas de --max
# acotado (RAM segura: el script carga la pasada completa a memoria). Idempotente:
# cada pasada re-consulta pendientes. Corre hasta 0. GPU bge-m3 vía túnel :11434.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
DB=data/_index/corpus.fts.sqlite3
WORKERS=${WORKERS:-6}
BATCH=${BATCH:-64}
PASS=${PASS:-200000}
EXTRA=${EXTRA:-}   # ej: "--endpoint tei --desc" para 2º stream vía TEI :18002

while :; do
  pend=$(sqlite3 -cmd ".timeout 120000" "$DB" "SELECT (SELECT count(*) FROM considerandos_meta) - (SELECT count(*) FROM considerandos_embeddings WHERE model='bge-m3')")
  echo "$(TZ=America/Santiago date '+%F %H:%M') CLT · considerandos pendientes=$pend"
  # ojo: vacío = error sqlite (db locked), NO cero — el ${pend:-0} de antes daba falso COMPLETO
  [ -z "$pend" ] && { echo "  query falló (DB locked) → reintento en 60s"; sleep 60; continue; }
  [ "$pend" -le 0 ] && { echo "=== CONSIDERANDOS COMPLETO ==="; break; }
  python3 scripts/build-considerandos-embeddings.py --max "$PASS" --workers "$WORKERS" --batch "$BATCH" $EXTRA
  rc=$?
  [ $rc -ne 0 ] && { echo "pasada rc=$rc → pausa 120s y reintento"; sleep 120; }
  sleep 5
done
