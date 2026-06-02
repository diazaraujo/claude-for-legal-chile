#!/bin/bash
# Sync COMPLETO de data/ a enigma (copia primaria, anti-desconexión SSD).
# DOS FASES por prioridad de riesgo:
#   Fase 1 = data raw IRREEMPLAZABLE (todo menos _index) → primero.
#   Fase 2 = data/_index (FTS/DBs derivados, reconstruibles) → después.
# Resumible: --partial guarda lo parcial; reintenta hasta pasada limpia.
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile" || exit 1
unset SSH_AUTH_SOCK
DEST="antonio@10.0.0.3:/mnt/data/legal-chile/data/"
COMMON="--exclude=*-wal --exclude=*-shm --exclude=*.tmp --exclude=*.part --exclude=.rsync-partial"
ssh antonio@10.0.0.3 'mkdir -p /mnt/data/legal-chile/data/_index' 2>/dev/null
sync_until() { # $1=descripcion, resto=args rsync
  local desc="$1"; shift
  local n=0
  while true; do
    n=$((n+1)); echo "[sync-enigma] $desc · intento $n · $(TZ=America/Santiago date '+%H:%M')"
    rsync -a --partial $COMMON "$@"; local rc=$?
    [ $rc -eq 0 ] && { echo "[sync-enigma] $desc COMPLETO $(TZ=America/Santiago date '+%F %H:%M')"; return 0; }
    echo "[sync-enigma] $desc rc=$rc → reintento 30s"; sleep 30
  done
}
# FASE 1: raw (todo menos _index)
sync_until "FASE1-raw" --exclude='_index/***' data/ "$DEST"
# FASE 2: índices derivados
sync_until "FASE2-index" data/_index/ "${DEST}_index/"
echo "[sync-enigma] TODO COMPLETO · local $(du -sh data|cut -f1) · enigma $(ssh antonio@10.0.0.3 'du -sh /mnt/data/legal-chile/data 2>/dev/null'|cut -f1)"
