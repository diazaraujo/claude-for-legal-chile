#!/bin/bash
# Espera el fin de los loops de considerandos (TEI+Ollama), verifica completitud,
# checkpoint del WAL y sincroniza corpus.fts a enigma (cp-seed + rsync delta +
# swap atómico, patrón de articulos-close.sh). Backend reload = eyes-on.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
LOCAL=data/_index/corpus.fts.sqlite3
ENIGMA=antonio@10.0.0.3
RDIR=/home/antonio/lc-index
LOG(){ echo "$(TZ=America/Santiago date '+%F %H:%M') CLT · $*"; }
q(){ sqlite3 -cmd ".timeout 120000" "$LOCAL" "$1"; }

LOG "waiter considerandos arrancado · espera fin de los loops"
while pgrep -f "considerandos-lo[o]p.sh" >/dev/null; do sleep 30; done

pend=$(q "SELECT (SELECT count(*) FROM considerandos_meta) - (SELECT count(*) FROM considerandos_embeddings WHERE model='bge-m3')")
emb=$(q "SELECT count(*) FROM considerandos_embeddings")
dim=$(q "SELECT dim, count(*) FROM considerandos_embeddings GROUP BY dim")
LOG "loops terminaron · pend=$pend · embebidos=$emb · dims: $dim"
if [ -z "$pend" ] || [ "$pend" -gt 0 ]; then
  LOG "!!! pend=$pend ≠ 0 → NO sincronizo (loops murieron antes de terminar) — revisar logs"
  exit 1
fi

LOG "checkpoint WAL (TRUNCATE)…"
q "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null

free=$(ssh "$ENIGMA" "df -BG --output=avail $RDIR | tail -1 | tr -dc 0-9" 2>/dev/null)
sz=$(du -BG "$LOCAL" | cut -f1 | tr -dc 0-9)
LOG "corpus.fts local=${sz}GB · libre enigma=${free:-?}GB"
if [ "${free:-0}" -lt $((sz + 20)) ]; then LOG "!!! espacio insuficiente en enigma → ABORTO (hacer a mano)"; exit 1; fi

ssh "$ENIGMA" "cp -f $RDIR/corpus.fts.sqlite3 $RDIR/corpus.fts.staging" \
  && LOG "seed OK · rsync delta…" \
  && rsync -a --inplace --no-whole-file --partial "$LOCAL" "$ENIGMA:$RDIR/corpus.fts.staging" \
  && ssh "$ENIGMA" "mv -f $RDIR/corpus.fts.staging $RDIR/corpus.fts.sqlite3 && echo SWAP_OK" \
  && LOG "=== ✓ corpus.fts con 5,16M considerandos_embeddings SINCRONIZADO a enigma — pendiente: faiss considerandos + reload backend (eyes-on) ===" \
  || LOG "!!! ERROR en seed/rsync/swap — revisar a mano"
LOG "waiter considerandos fin"
