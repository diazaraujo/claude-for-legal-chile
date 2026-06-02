#!/usr/bin/env python3
"""
Embebe el Boletín Concursal (747k registros estructurados de la tabla `concursal`)
para hacerlo semánticamente searchable. El embed-loop normal solo globea archivos
de texto; el concursal vive en una tabla → este script genera una línea de texto por
registro y la embebe con bge-m3. Path = el path del registro (PK) → la coverage map
lo cuenta como embebido.

Corre contra ENIGMA (bge-m3) vía túnel: OLLAMA_EMBED_URL=http://localhost:11435/api/embed
Uso: OLLAMA_EMBED_URL=http://localhost:11435/api/embed python3 scripts/embed-concursal.py --batch 64
"""
import argparse, json, os, sqlite3, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

DB = "data/_index/new-sources.fts.sqlite3"
OLLAMA = os.environ.get("OLLAMA_EMBED_URL", "http://localhost:11434/api/embed")
MODEL = "bge-m3"

def text_of(rol,tipo,deudor,rut,ente,publicacion,tribunal,fecha):
    parts=[f"Procedimiento concursal rol {rol}." if rol else "Procedimiento concursal."]
    if tipo: parts.append(tipo+".")
    if deudor: parts.append(f"Deudor: {deudor}" + (f" RUT {rut}." if rut else "."))
    if ente: parts.append(f"Veedor/Liquidador: {ente}.")
    if publicacion: parts.append(publicacion+".")
    if tribunal: parts.append(tribunal+".")
    if fecha: parts.append(f"Fecha {fecha}.")
    return " ".join(parts)

def embed(texts, timeout=180):
    payload=json.dumps({"model":MODEL,"input":texts}).encode()
    req=urllib.request.Request(OLLAMA,data=payload,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read()).get("embeddings",[])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--batch",type=int,default=64); ap.add_argument("--limit",type=int); a=ap.parse_args()
    c=sqlite3.connect(DB,timeout=120,check_same_thread=False); c.execute("PRAGMA busy_timeout=120000"); c.execute("PRAGMA journal_mode=WAL")
    have={r[0] for r in c.execute("SELECT path FROM embeddings WHERE path LIKE 'boletin-concursal/%'")}
    rows=c.execute("SELECT path,rol,tipo,deudor,rut,ente,publicacion,tribunal,fecha FROM concursal").fetchall()
    todo=[r for r in rows if r[0] not in have]
    if a.limit: todo=todo[:a.limit]
    print(f"[embed-concursal] {len(rows)} registros · {len(have)} ya · {len(todo)} pendientes · {MODEL} via {OLLAMA}",flush=True)
    n=0; t0=time.time(); lock=Lock()
    def do_batch(chunk):
        texts=[text_of(*r[1:]) for r in chunk]
        try: vecs=embed(texts)
        except Exception as e: print("  embed err:",e,flush=True); return 0
        if len(vecs)!=len(chunk): return 0
        with lock:
            for r,v in zip(chunk,vecs):
                blob=struct.pack(f"{len(v)}f",*v)
                c.execute("INSERT OR REPLACE INTO embeddings(path,model,dim,vec) VALUES(?,?,?,?)",
                          (r[0],MODEL,len(v),blob))
            c.commit()
        return len(chunk)
    batches=[todo[i:i+a.batch] for i in range(0,len(todo),a.batch)]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(do_batch,b) for b in batches]):
            n+=f.result()
            if n and (n//a.batch)%20==0:
                print(f"  · {n}/{len(todo)} · {n/max(time.time()-t0,1):.0f}/s",flush=True)
    print(f"[FIN] {n} embebidos · {n/max(time.time()-t0,1):.0f}/s",flush=True)
    c.close()

if __name__=="__main__": main()
