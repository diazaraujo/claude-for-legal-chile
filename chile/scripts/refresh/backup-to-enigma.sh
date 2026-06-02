#!/bin/bash
# Backup periódico de las DB SQLite críticas a enigma (15TB, /mnt/data/legal-chile/backups).
# Motivado por la corrupción de perfiles.sqlite3 (2026-06-02): la SSD ADA externa puede
# hiccupear a readonly y corromper SQLite mid-write. Enigma = copia segura. Cada 30 min.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
unset SSH_AUTH_SOCK
DBS="data/_index/perfiles.sqlite3 data/_index/partes.sqlite3 data/leychile/manifest.sqlite3"
DEST=/mnt/data/legal-chile/backups
ssh antonio@10.0.0.3 "mkdir -p $DEST" 2>/dev/null
while true; do
  TS=$(TZ=America/Santiago date +%Y%m%d-%H%M)
  for db in $DBS; do
    [ -f "$db" ] || continue
    name=$(basename "$db" .sqlite3)
    # copia consistente vía .backup (no copiar archivo vivo) → tmp → scp
    tmp="/tmp/bk-$name.sqlite3"
    sqlite3 "$db" ".backup '$tmp'" 2>/dev/null && \
      scp -q "$tmp" "antonio@10.0.0.3:$DEST/$name-$TS.sqlite3" 2>/dev/null && rm -f "$tmp"
  done
  # retener solo las últimas 8 de cada una en enigma
  ssh antonio@10.0.0.3 "cd $DEST 2>/dev/null && for p in perfiles partes manifest; do ls -t \$p-*.sqlite3 2>/dev/null | tail -n +9 | xargs -r rm -f; done" 2>/dev/null
  echo "[backup-enigma] $(TZ=America/Santiago date '+%H:%M') · perfiles+partes+manifest → enigma"
  sleep 1800
done
