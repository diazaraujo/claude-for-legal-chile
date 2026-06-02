#!/usr/bin/env python3
"""
FASE 1 — Extracción LLM de abogados/fiscales/partes/jueces sobre la SECCIÓN
relevante de las sentencias PJUD, para lo que el regex (FASE 0) no atrapa.

Complementa [[reference_pjud_extraccion_partes_fase0]]: el regex saca las
fórmulas estructuradas (~12% fiscal, ~11% abogado), pero el techo es 62-75%
(la mayoría está en fraseo libre). Esto pasa la sección por un LLM local
(llama3.2:3b vía Ollama) con salida JSON forzada para recuperar el resto.

Modelo: llama3.2:3b (Ollama localhost:11434). Rápido en M1 Max (~0.4-4 docs/s
según contención de GPU con los embeddings). NO usar qwen3-32b (satura GPU).

Subset: solo docs cuya sección contiene un ancla (fiscal/defensor/abogad/juez)
→ evita gastar LLM en sentencias sin entidades nombradas.

Salida: tabla SEPARADA `partes_llm` en data/_index/partes.sqlite3 (no toca la
tabla `partes` del regex; se mergea/dedup después). Idempotente vía `fase1_done`.

Uso:
  python3 scripts/extract-partes/fase1-llm.py --comp Penales --workers 4
  python3 scripts/extract-partes/fase1-llm.py --comp Penales --limit 500   # piloto
  python3 scripts/extract-partes/fase1-llm.py --all --workers 4
"""
import argparse, gzip, json, re, sqlite3, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob
from threading import Lock

import os
OLLAMA = os.environ.get("OLLAMA_GEN_URL", "http://localhost:11434/api/generate")
MODEL  = os.environ.get("FASE1_MODEL", "llama3.2:3b")
PJUD   = "data/pjud"
COMPS  = ["Civiles","Cobranza","Corte_de_Apelaciones","Corte_Suprema","Familia","Laborales","Penales"]

BR=re.compile(r"<br\s*/?>",re.I); TAG=re.compile(r"<[^>]+>")
ANCHOR=re.compile(r"fiscal|defensor|abogad|patrocin|apoderad|juez|jueza|ministr", re.I)
ROLES={"fiscal","defensor","juez","abogado","demandante","demandado","representante","querellante","apoderado"}

PROMPT=('Eres un extractor de entidades de sentencias judiciales chilenas. '
'Del TEXTO extrae SOLO las personas nombradas (nombre y apellido) y su rol procesal. '
'Roles válidos: fiscal, defensor, juez, abogado, demandante, demandado, representante, querellante, apoderado. '
'Un rol por persona, el más específico. No inventes personas que no estén en el texto. '
'Si no hay personas nombradas, devuelve {"e":[]}. '
'Responde EXCLUSIVAMENTE JSON válido con esta forma: {"e":[{"n":"Nombre Apellido","r":"rol"}]}. /no_think\n\nTEXTO:\n')

def to_text(t):
    if isinstance(t,list): t=" ".join(map(str,t))
    return re.sub(r"\s+"," ",TAG.sub(" ",BR.sub(" ",t or ""))).strip()

def iter_records(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: data=json.load(f)
    if isinstance(data,dict):
        for k in ("docs","response","results","data"):
            if k in data: data=data[k]; break
        if isinstance(data,dict) and "docs" in data: data=data["docs"]
    yield from (data if isinstance(data,list) else [data])

def llm_extract(section, retries=2):
    body=json.dumps({"model":MODEL,"prompt":PROMPT+section[:3500],"stream":False,
                     "format":"json","options":{"temperature":0,"num_predict":400}}).encode()
    for i in range(retries):
        try:
            req=urllib.request.Request(OLLAMA,data=body,headers={"Content-Type":"application/json"})
            o=json.loads(urllib.request.urlopen(req,timeout=180).read())
            data=json.loads(o.get("response","{}"))
            out=[]
            for e in data.get("e",[]):
                n=str(e.get("n","")).strip(); r=str(e.get("r","")).strip().lower()
                # normaliza rol al vocabulario (toma la primera palabra-rol que aparezca)
                r=next((x for x in ROLES if x in r), None)
                if n and r and 2<=len(n.split())<=6 and len(n)<=60:
                    out.append((n,r))
            return out
        except Exception:
            time.sleep(1.5*(i+1))
    return None

def init_db(p):
    con=sqlite3.connect(p,timeout=120); con.execute("PRAGMA busy_timeout=120000")
    con.execute("""CREATE TABLE IF NOT EXISTS partes_llm(
        sent_id TEXT, competencia TEXT, rol TEXT, nombre TEXT, anio INTEGER)""")
    con.execute("CREATE TABLE IF NOT EXISTS fase1_done(sent_id TEXT PRIMARY KEY, n INTEGER, ts INTEGER)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_llm_rol ON partes_llm(rol)")
    con.commit(); return con

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--comp"); ap.add_argument("--all",action="store_true")
    ap.add_argument("--limit",type=int); ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--out",default="data/_index/partes.sqlite3")
    a=ap.parse_args()
    files = sorted(glob(f"{PJUD}/{a.comp}/*.json.gz")) if a.comp else sorted(glob(f"{PJUD}/*/*.json.gz"))
    if not files: ap.error("usa --comp o --all")

    con=init_db(a.out); dbl=Lock()
    done={r[0] for r in con.execute("SELECT sent_id FROM fase1_done").fetchall()}
    print(f"[FASE1 llm] {MODEL} · {len(files)} archivos · ya hechos={len(done)} · workers={a.workers}",flush=True)

    proc=0; ents=0; t0=time.time(); n_seen=0
    def handle(rec):
        sid=str(rec.get("id") or rec.get("sent__crr_documento_i"))
        if sid in done: return None
        sec=to_text(rec.get("texto_sentencia") or rec.get("texto_sentencia_anon"))
        if not sec or not ANCHOR.search(sec[:3500]):
            return (sid, rec, [])      # sin ancla → marcar hecho, 0 entidades
        return (sid, rec, llm_extract(sec))

    for fp in files:
        comp=fp.split("/")[-2]
        batch=[r for r in iter_records(fp)]
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs=[ex.submit(handle,r) for r in batch]
            for f in as_completed(futs):
                res=f.result()
                if res is None: continue
                sid,rec,extracted=res
                n_seen+=1
                if extracted is None:  # error LLM → no marcar done, reintentar luego
                    continue
                anio=rec.get("sent__FEC_ANIO_i")
                with dbl:
                    for n,r in extracted:
                        con.execute("INSERT INTO partes_llm VALUES(?,?,?,?,?)",(sid,comp,r,n,anio))
                    con.execute("INSERT OR REPLACE INTO fase1_done VALUES(?,?,?)",(sid,len(extracted),int(time.time())))
                    con.commit()
                proc+=1; ents+=len(extracted)
                if proc%50==0:
                    rate=proc/max(time.time()-t0,1)
                    print(f"  · {proc} docs · {ents} entidades · {rate:.2f} docs/s",flush=True)
                if a.limit and proc>=a.limit: break
        if a.limit and proc>=a.limit: break
    print(f"[FIN] {proc} docs procesados · {ents} entidades · {proc/max(time.time()-t0,1):.2f} docs/s",flush=True)
    con.close()

if __name__=="__main__":
    main()
