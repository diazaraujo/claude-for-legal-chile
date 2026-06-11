#!/bin/bash
# Canal DIRECTO (IP Mac) gateado por reloj + probe 429 (regla off-peak 19:00->09:00 CLT).
# Espejo de leychile-gated.sh (canal Zyte): corre leychile-direct.py cuando hora CLT
# off-peak Y la norma-probe responde <Norma> desde la IP directa (429/timeout = throttle
# per-IP activo -> pausa). Mata el scraper al entrar peak; para al llegar a 0 pendientes.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
DB=data/leychile/manifest.sqlite3
SCRAPER="python3 scripts/bulk-downloaders/leychile-direct.py"

is_offpeak() { return 0; }  # gate reloj OFF por orden Antonio 10-jun (peak con probe verde)
probe_green() {
  # probe con norma PENDIENTE real (1044382 está cacheada en CDN → falso verde)
  pid_norma=$(sqlite3 "$DB" "SELECT id_norma FROM normas WHERE downloaded=0 AND status IS NULL ORDER BY RANDOM() LIMIT 1")
  body=$(curl -s -m 15 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
    "https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma=${pid_norma:-1044382}" | head -c 300)
  case "$body" in *"<Norma"*) return 0;; *) return 1;; esac
}

while true; do
  pend=$(sqlite3 "$DB" "SELECT count(*) FROM normas WHERE downloaded=0 AND status IS NULL")
  echo "$(TZ=America/Santiago date '+%F %H:%M %Z') · pendientes=${pend:-?}"
  [ "${pend:-0}" -eq 0 ] && { echo "LEYCHILE COMPLETO (sin pendientes NULL)"; break; }
  if is_offpeak && probe_green; then
    echo "  off-peak + IP directa verde → corre pasada directa"
    $SCRAPER & child=$!
    while kill -0 "$child" 2>/dev/null; do
      if ! is_offpeak; then echo "  entra peak (09:00 CLT) → mato scraper, retomo 19:00"; kill "$child" 2>/dev/null; break; fi
      sleep 60
    done
    wait "$child" 2>/dev/null
  else
    echo "  peak o throttle IP activo → pausa 20min"
    sleep 1200
  fi
done
