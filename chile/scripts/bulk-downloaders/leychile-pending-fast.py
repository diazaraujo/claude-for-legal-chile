#!/usr/bin/env python3
"""Downloader directo de las normas pending de leychile. Lógica del probe que SÍ baja:
rota geos (EU primero, que funcionan bajo el WAF actual), timeout corto, primera que
devuelve <Norma> gana → escribe XML + marca downloaded en el manifest. Verificable:
loguea ok/stub/ban por lote. Bypassa el scraper threading que se colgaba."""
import os, json, base64, sqlite3, urllib.request, urllib.error, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
AUTH = base64.b64encode(f"{os.environ['ZYTE_API_KEY']}:".encode()).decode()
GEOS = ["GB","DE","ES","NL","FR","IT","PL","US","CA","AR","BR","MX"]  # EU primero (funcionan hoy)
BASE = "https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma="
DB   = "data/leychile/manifest.sqlite3"
OUT  = Path("data/leychile"); RAW = OUT/"_raw"; RAW.mkdir(parents=True, exist_ok=True)
lock = threading.Lock(); S = {"ok":0,"stub":0,"ban":0}
def fetch(nid, geo, timeout=6):
    time.sleep(1.5)
    p = json.dumps({"url":BASE+str(nid),"httpResponseBody":True,"geolocation":geo}).encode()
    r = urllib.request.Request("https://api.zyte.com/v1/extract", data=p,
        headers={"Authorization":f"Basic {AUTH}","Content-Type":"application/json"})
    d = json.loads(urllib.request.urlopen(r, timeout=timeout).read())
    b = d.get("httpResponseBody",""); return base64.b64decode(b) if b else b""
def mark(nid, downloaded, status, size=0):
    c = sqlite3.connect(DB, timeout=60); c.execute("PRAGMA busy_timeout=60000")
    c.execute("UPDATE normas SET downloaded=?, size=?, status=? WHERE id_norma=?",(downloaded,size,status,nid)); c.commit(); c.close()
def worker(row):
    nid, tipo = row
    dest = OUT/tipo/f"{nid}.xml"
    if dest.exists() and dest.stat().st_size > 500:
        mark(nid,1,"ok",dest.stat().st_size); 
        with lock: S["ok"]+=1
        return
    got_response = False                    # ¿algún geo respondió (aunque vacío)? distingue norma MUERTA de WAF/timeout
    for geo in GEOS:
        try: body = fetch(nid, geo)
        except Exception: continue          # timeout/520/conn → el request NO llegó → siguiente geo
        got_response = True                 # BCN respondió (aunque sea vacío)
        if body and b"<Norma" in body[:300]:
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(body)
            mark(nid,1,"ok",len(body))
            with lock: S["ok"]+=1
            return
        if body:                            # algo pero no Norma → stub terminal
            (RAW/f"stub-{nid}.bin").write_bytes(body[:4000]); mark(nid,0,"stub")
            with lock: S["stub"]+=1
            return
        # body vacío (b"") → este geo confirma norma vacía; sigue probando otros geos
    if got_response and S["ok"] > 0:        # VACÍO con WAF demostradamente abierto (hubo oks en la pasada) → norma MUERTA
        mark(nid,0,"ban")
        with lock: S["ban"]+=1
    else:                                   # vacío sin ningún ok = WAF empty-wall (10-jun: 50 falsos bans) o todos
        with lock: S["ban"]+=1              # timeout → NO terminal, queda pending p/ retry
c = sqlite3.connect(DB); pend=[(r[0],r[1]) for r in c.execute("SELECT id_norma,tipo FROM normas WHERE downloaded=0 AND status IS NULL ORDER BY id_norma DESC")]; c.close()
print(f"pending: {len(pend)} · {time.strftime('%H:%M:%S')}", flush=True); t0=time.time()
with ThreadPoolExecutor(max_workers=4) as ex:
    for i,_ in enumerate(ex.map(worker, pend),1):
        if i % 50 == 0:
            el=time.time()-t0; print(f"  {i}/{len(pend)} ok={S['ok']} stub={S['stub']} ban={S['ban']} · {i/el:.2f}/s · {time.strftime('%H:%M:%S')}", flush=True)
        if i >= 100 and S["ok"] == 0:
            print(f"ABORT: {i} normas sin un solo ok → WAF empty-wall, pasada estéril · {time.strftime('%H:%M:%S')}", flush=True)
            os._exit(3)
print(f"FIN {S} · {time.strftime('%H:%M:%S')}", flush=True)
