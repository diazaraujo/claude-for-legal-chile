#!/usr/bin/env python3
"""
Extrae de las sentencias PENALES (592k) lo que el metadato NO trae: días de pena,
tipo de pena (efectiva/remitida/libertad vigilada), delito, grado e iter criminis,
y demografía del imputado. El metadato ya da decisión (sent__GLS_DECISION_s),
juez (gls_juez_ss), juzgado (gls_juz_s), materia (gls_materia_ss) — no se re-extrae.
Recrea la PPT penal (Análisis general + imputados + días de pena + Ficha Juez).
Ver [[project_legal_chile_perfiles_resumenes]].

Corre en ENIGMA (qwen2.5:14b) vía túnel localhost:11435.

Salida: tabla `penal_resultado` en perfiles.sqlite3:
  sent_id, anio, decision, delitos, dias_pena, tipo_pena, grado, iter_criminis,
  imputado_genero, imputado_edad

Uso: OLLAMA_GEN_URL=http://localhost:11435/api/generate FASE1_MODEL=qwen2.5:14b \
       python3 scripts/perfiles/extract-penal-resultado.py --workers 6
"""
import argparse, gzip, json, os, re, sqlite3, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob
from threading import Lock
import urllib.request

OLLAMA = os.environ.get("OLLAMA_GEN_URL", "http://localhost:11434/api/generate")
MODEL  = os.environ.get("FASE1_MODEL", "qwen2.5:14b")
PJUD   = "data/pjud/Penales"
OUT    = "data/_index/perfiles.sqlite3"

BR=re.compile(r"<br\s*/?>",re.I); TAG=re.compile(r"<[^>]+>")
DEC={"condena","absolucion","mixta","sobreseimiento","no_aplica"}
TIPO={"efectiva","remitida","libertad_vigilada","reclusion_nocturna","suspension_condicional","multa","servicio_comunidad","expulsion","otra","no_aplica"}
GRADO={"autor","complice","encubridor","desconocido"}
ITER={"consumado","frustrado","tentado","desconocido"}
GEN={"masculino","femenino","desconocido"}

PROMPT=('Eres analista de sentencias penales chilenas. Del TEXTO (resumen + parte resolutiva) extrae en JSON:\n'
'- decision: condena|absolucion|mixta|sobreseimiento|no_aplica.\n'
'- delitos: lista de hurto_simple|hurto_falta|robo_con_violencia|robo_con_intimidacion|robo_por_sorpresa|robo_lugar_habitado|robo_lugar_no_habitado|trafico_drogas|microtrafico|porte_consumo_drogas|lesiones|amenazas|manejo_estado_ebriedad|receptacion|porte_arma|violencia_intrafamiliar|abuso_sexual|violacion|homicidio|estafa|otra.\n'
'- dias_pena: total de días de pena privativa de libertad impuesta (entero) o null (convierte años/meses a días: 1 año=365, 1 mes=30; 541 días=presidio menor grado medio etc.).\n'
'- tipo_pena: efectiva|remitida|libertad_vigilada|reclusion_nocturna|suspension_condicional|multa|servicio_comunidad|expulsion|otra|no_aplica.\n'
'- grado: autor|complice|encubridor|desconocido.\n'
'- iter_criminis: consumado|frustrado|tentado|desconocido.\n'
'- imputado_genero: masculino|femenino|desconocido (por don/doña, "el acusado"/"la acusada").\n'
'- imputado_edad: edad del imputado en años (entero) o null.\n'
'No inventes. Si no consta usa null o "desconocido". Si hay varios imputados, el principal. '
'Responde SOLO JSON: {"decision":"...","delitos":[],"dias_pena":null,"tipo_pena":"...","grado":"...","iter_criminis":"...","imputado_genero":"...","imputado_edad":null}\n\nTEXTO:\n')

def to_text(t):
    if isinstance(t,list): t=" ".join(map(str,t))
    return re.sub(r"\s+"," ",TAG.sub(" ",BR.sub(" ",t or ""))).strip()

def section(t):
    return t[:2500]+"\n[...]\n"+(t[-3500:] if len(t)>3500 else "")

def iter_records(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: data=json.load(f)
    if isinstance(data,dict):
        for k in ("docs","response","results","data"):
            if k in data: data=data[k]; break
        if isinstance(data,dict) and "docs" in data: data=data["docs"]
    yield from (data if isinstance(data,list) else [data])

def _enum(v,allowed,default): v=str(v).strip().lower(); return v if v in allowed else default
def _int(v): return int(v) if isinstance(v,(int,float)) else None

def llm(sec, retries=2):
    body=json.dumps({"model":MODEL,"prompt":PROMPT+sec,"stream":False,"format":"json",
                     "options":{"temperature":0,"num_predict":300}}).encode()
    for i in range(retries):
        try:
            o=json.loads(urllib.request.urlopen(urllib.request.Request(
                OLLAMA,data=body,headers={"Content-Type":"application/json"}),timeout=180).read())
            d=json.loads(o.get("response","{}"))
            dels=[str(x).strip().lower() for x in (d.get("delitos") or []) if str(x).strip()][:6]
            return (_enum(d.get("decision"),DEC,"no_aplica"), ",".join(dels), _int(d.get("dias_pena")),
                    _enum(d.get("tipo_pena"),TIPO,"no_aplica"), _enum(d.get("grado"),GRADO,"desconocido"),
                    _enum(d.get("iter_criminis"),ITER,"desconocido"), _enum(d.get("imputado_genero"),GEN,"desconocido"),
                    _int(d.get("imputado_edad")))
        except Exception:
            time.sleep(1.5*(i+1))
    return None

def init_db(p):
    c=sqlite3.connect(p,timeout=120); c.execute("PRAGMA busy_timeout=120000")
    c.execute("""CREATE TABLE IF NOT EXISTS penal_resultado(
        sent_id TEXT PRIMARY KEY, anio INTEGER, decision TEXT, delitos TEXT, dias_pena INTEGER,
        tipo_pena TEXT, grado TEXT, iter_criminis TEXT, imputado_genero TEXT, imputado_edad INTEGER)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_pr_dec ON penal_resultado(decision)")
    c.commit(); return c

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workers",type=int,default=6); ap.add_argument("--limit",type=int); a=ap.parse_args()
    c=init_db(OUT); lock=Lock()
    done={r[0] for r in c.execute("SELECT sent_id FROM penal_resultado").fetchall()}
    files=sorted(glob(f"{PJUD}/*.json.gz"))
    print(f"[penal-resultado] {MODEL} via {OLLAMA} · {len(files)} archivos · hechos={len(done)} · workers={a.workers}",flush=True)
    proc=0; t0=time.time()
    def handle(r):
        sid=str(r.get("id") or r.get("sent__crr_documento_i"))
        if sid in done: return None
        t=to_text(r.get("texto_sentencia") or r.get("texto_sentencia_anon"))
        if not t or len(t)<300: return (sid,r,None)
        return (sid,r,llm(section(t)))
    for fp in files:
        batch=list(iter_records(fp))
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for f in as_completed([ex.submit(handle,r) for r in batch]):
                res=f.result()
                if res is None: continue
                sid,r,out=res
                if out is None:
                    t=to_text(r.get("texto_sentencia") or r.get("texto_sentencia_anon"))
                    if t and len(t)>=300: continue   # error LLM → reintentar luego
                row=(sid, r.get("sent__FEC_ANIO_i"), *(out if out else ("no_aplica","",None,"no_aplica","desconocido","desconocido","desconocido",None)))
                with lock:
                    c.execute("INSERT OR REPLACE INTO penal_resultado VALUES(?,?,?,?,?,?,?,?,?,?)",row); c.commit()
                proc+=1
                if proc%50==0: print(f"  · {proc} · {proc/max(time.time()-t0,1):.2f}/s",flush=True)
                if a.limit and proc>=a.limit: break
        if a.limit and proc>=a.limit: break
    print(f"[FIN] {proc} sentencias · {proc/max(time.time()-t0,1):.2f}/s",flush=True)
    c.close()

if __name__=="__main__": main()
