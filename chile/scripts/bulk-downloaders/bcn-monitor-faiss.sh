#!/bin/bash
# Monitorea el scraper BCN (gateado). Al completar (0 pendientes NULL, o plateau
# off-peak), espera el catch-up del embed-loop, rsync-ea new-sources.fts a enigma
# y reconstruye el índice faiss (swap atómico, mmap-safe). Backend reload = eyes-on.
# Pensado para correr overnight con nohup.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
DB=data/leychile/manifest.sqlite3
LOCAL_FTS=data/_index/new-sources.fts.sqlite3
ENIGMA=antonio@10.0.0.3
EMB_LOG=/tmp/lc-embed-loop.log
LOG(){ echo "$(TZ=America/Santiago date '+%F %H:%M') CLT · $*"; }
is_offpeak(){ h=$(TZ=America/Santiago date +%H); [ "$h" -ge 19 ] || [ "$h" -lt 9 ]; }
qpend(){ sqlite3 "$DB" "SELECT count(*) FROM normas WHERE downloaded=0 AND status IS NULL" 2>/dev/null; }
qdl(){ sqlite3 "$DB" "SELECT count(*) FROM normas WHERE downloaded=1" 2>/dev/null; }
emb_leychile_pend(){ grep -E "\[leychile\].*pendientes" "$EMB_LOG" 2>/dev/null | tail -1 | grep -oE "[0-9]+ pendientes" | grep -oE "^[0-9]+"; }

LOG "=== monitor BCN+faiss arrancado ==="
last_pend=999999999; stale=0
while true; do
  pend=$(qpend); dl=$(qdl); ep=$(emb_leychile_pend)
  scr=$(pgrep -f leychile-gated >/dev/null && echo on || echo off)
  LOG "BCN dl=$dl pend=${pend:-?} | embed leychile pend=${ep:-?} | scraper=$scr | $(is_offpeak && echo off-peak || echo PEAK)"

  done=0
  [ "${pend:-1}" -eq 0 ] && done=1
  if is_offpeak; then
    if [ "${pend:-0}" -ge "$last_pend" ]; then stale=$((stale+1)); else stale=0; fi
    last_pend=${pend:-$last_pend}
    [ "$stale" -ge 6 ] && [ "${pend:-99999}" -lt 3000 ] && { LOG "plateau off-peak (cola muerta) → tratar como completo"; done=1; }
  fi

  if [ "$done" -eq 1 ]; then
    LOG "=== BCN COMPLETO (pend=${pend:-?}) → catch-up embed ==="
    z=0
    while [ "$z" -lt 2 ]; do
      p=$(emb_leychile_pend); LOG "  embed leychile pend=${p:-?} (z=$z)"
      if [ "${p:-1}" -eq 0 ]; then z=$((z+1)); else z=0; fi
      sleep 300
    done
    LOG "  embed al día → rsync new-sources.fts → enigma (delta, puede tardar)…"
    if rsync -a --inplace --partial "$LOCAL_FTS" "$ENIGMA:/home/antonio/lc-index/new-sources.fts.staging"; then
      LOG "  rsync OK → swap atómico + rebuild faiss…"
      ssh "$ENIGMA" 'set -e
        mv -f /home/antonio/lc-index/new-sources.fts.staging /home/antonio/lc-index/new-sources.fts.sqlite3
        sed "s#new-sources.ivf.faiss#&.new#; s#new-sources.paths.txt#&.new#" /tmp/lc-build-faiss.py > /tmp/lc-build-faiss-new.py
        /home/antonio/faiss-venv/bin/python /tmp/lc-build-faiss-new.py
        mv -f /home/antonio/lc-index/new-sources.ivf.faiss.new  /home/antonio/lc-index/new-sources.ivf.faiss
        mv -f /home/antonio/lc-index/new-sources.paths.txt.new /home/antonio/lc-index/new-sources.paths.txt
        echo SWAP_OK' \
      && LOG "=== ✓ FAISS RECONSTRUIDO Y SWAPEADO — pendiente: reload del backend (eyes-on) ===" \
      || LOG "!!! ERROR en swap/faiss en enigma — revisar a mano"
    else
      LOG "!!! ERROR en rsync — new-sources.fts NO sincronizado, faiss NO reconstruido"
    fi
    break
  fi
  sleep 1200
done
LOG "=== monitor terminado ==="
