#!/bin/bash
# Espera a que termine build-articulos-embeddings.py y sincroniza corpus.fts a enigma
# (cp-seed + rsync delta + swap atómico, mmap-safe). NO hay faiss de artículos: el
# backend (apps/corpus/service.py) lee corpus.fts con immutable=1. Backend reload = eyes-on.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
LOCAL=data/_index/corpus.fts.sqlite3
ENIGMA=antonio@10.0.0.3
RDIR=/home/antonio/lc-index
LOG(){ echo "$(TZ=America/Santiago date '+%F %H:%M') CLT · $*"; }
gap(){ python3 -c "import sqlite3;c=sqlite3.connect('file:$LOCAL?mode=ro',uri=True);print(c.execute('SELECT count(*) FROM articulos_meta').fetchone()[0]-c.execute('SELECT count(*) FROM articulos_embeddings').fetchone()[0])" 2>/dev/null; }

LOG "waiter artículos arrancado · espera fin del embed"
while pgrep -f build-articulos-embeddings >/dev/null; do sleep 30; done
LOG "embed artículos terminó · gap restante=$(gap)"

free=$(ssh "$ENIGMA" "df -BG --output=avail $RDIR | tail -1 | tr -dc 0-9" 2>/dev/null)
LOG "espacio libre enigma=${free:-?}GB · seed corpus.fts.staging (cp same-disk)…"
if [ "${free:-0}" -lt 50 ]; then LOG "!!! <50GB libres en enigma → ABORTO sync (hacer a mano)"; exit 1; fi

ssh "$ENIGMA" "cp -f $RDIR/corpus.fts.sqlite3 $RDIR/corpus.fts.staging" \
  && LOG "seed OK · rsync delta corpus.fts → staging…" \
  && rsync -a --inplace --no-whole-file --partial "$LOCAL" "$ENIGMA:$RDIR/corpus.fts.staging" \
  && ssh "$ENIGMA" "mv -f $RDIR/corpus.fts.staging $RDIR/corpus.fts.sqlite3 && echo SWAP_OK" \
  && LOG "=== ✓ corpus.fts SINCRONIZADO (artículos embebidos live en enigma) — pendiente: reload backend (eyes-on) ===" \
  || LOG "!!! ERROR en seed/rsync/swap — revisar a mano"
LOG "waiter artículos fin"
