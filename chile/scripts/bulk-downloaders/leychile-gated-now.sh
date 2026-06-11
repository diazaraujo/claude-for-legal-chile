#!/bin/bash
# Scraper leychile gateado por reloj + probe WAF (regla off-peak 19:00->09:00 CLT).
# Corre pending-fast cuando: hora CLT off-peak Y la norma-probe responde <Norma>.
# Mata el scraper al entrar peak; reintenta cada 20min si WAF activo; para al llegar a 0.
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
export ZYTE_API_KEY=$(grep '^ZYTE_API_KEY' .env | cut -d= -f2)
DB=data/leychile/manifest.sqlite3
SCRAPER="python3 scripts/bulk-downloaders/leychile-pending-fast.py"

is_offpeak() { return 0; }  # gate reloj OFF por orden Antonio 10-jun (peak con probe verde)
probe_green() {
  # probe con norma PENDIENTE real (1044382 está cacheada en CDN → falso verde)
  PROBE_ID=$(sqlite3 "$DB" "SELECT id_norma FROM normas WHERE downloaded=0 AND status IS NULL ORDER BY RANDOM() LIMIT 1")
  PROBE_ID="$PROBE_ID" python3 - <<'PY'
import os,json,base64,urllib.request,sys
AUTH=base64.b64encode(f"{os.environ['ZYTE_API_KEY']}:".encode()).decode()
nid=os.environ.get('PROBE_ID') or '1044382'
for geo in ('GB','US','DE','CA','ES','AU'):
    try:
        p=json.dumps({'url':f'https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma={nid}','httpResponseBody':True,'geolocation':geo}).encode()
        r=urllib.request.Request('https://api.zyte.com/v1/extract',data=p,headers={'Authorization':f'Basic {AUTH}','Content-Type':'application/json'})
        d=json.loads(urllib.request.urlopen(r,timeout=20).read()); b=base64.b64decode(d.get('httpResponseBody','') or '')
        if b'<Norma' in b[:300]: sys.exit(0)
    except Exception: pass
sys.exit(1)
PY
}

while true; do
  pend=$(sqlite3 "$DB" "SELECT count(*) FROM normas WHERE downloaded=0 AND status IS NULL")
  echo "$(TZ=America/Santiago date '+%F %H:%M %Z') · pendientes=${pend:-?}"
  [ "${pend:-0}" -eq 0 ] && { echo "LEYCHILE COMPLETO (sin pendientes NULL)"; break; }
  if is_offpeak && probe_green; then
    echo "  off-peak + WAF verde → corre pasada"
    $SCRAPER & child=$!
    while kill -0 "$child" 2>/dev/null; do
      if ! is_offpeak; then echo "  entra peak (09:00 CLT) → mato scraper, retomo 19:00"; kill "$child" 2>/dev/null; break; fi
      sleep 60
    done
    wait "$child" 2>/dev/null; rc=$?
    [ "$rc" -ne 0 ] && { echo "  pasada abortó (rc=$rc, WAF empty-wall) → pausa 20min"; sleep 1200; }
  else
    echo "  peak o WAF activo → pausa 20min"
    sleep 1200
  fi
done
