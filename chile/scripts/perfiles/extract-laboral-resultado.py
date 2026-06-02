#!/usr/bin/env python3
"""
Extrae el RESULTADO de las sentencias LABORALES (235k) vía LLM — la pieza que el
metadato PJUD no trae (penal sí tiene sent__GLS_DECISION_s; laboral no). Alimenta
los perfiles de EMPRESAS (estrategias en litigios laborales) y de jueces/abogados.
Ver [[project_legal_chile_perfiles_resumenes]].

Corre en ENIGMA (qwen2.5:14b, ya cargado por FASE1 → sin VRAM extra) vía túnel
localhost:11435. CPU del Mac solo orquesta (lee json.gz, escribe SQLite).

Extrae por sentencia (parte resolutiva + encabezado):
  resultado: acogida / rechazada / acogida_parcial / conciliacion / desistimiento / no_aplica
  materias[]: despido_injustificado, despido_indebido, nulidad_despido (Ley Bustos),
              autodespido, cobro_prestaciones, tutela_derechos_fundamentales,
              accidente_trabajo, practica_antisindical, otra
  monto_total_clp: número o null
  defensas_empleador[]: necesidades_empresa_art161, falta_probidad, incumplimiento_grave,
              caso_fortuito, vencimiento_plazo, conclusion_trabajo, niega_relacion_laboral, otra
  via_recursiva: apelacion / nulidad / ninguna / desconocido

Uso:
  OLLAMA_GEN_URL=http://localhost:11435/api/generate FASE1_MODEL=qwen2.5:14b \
    python3 scripts/perfiles/extract-laboral-resultado.py --workers 6
"""
import argparse, gzip, json, os, re, sqlite3, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob
from threading import Lock
import urllib.request

OLLAMA = os.environ.get("OLLAMA_GEN_URL", "http://localhost:11434/api/generate")
MODEL  = os.environ.get("FASE1_MODEL", "qwen2.5:14b")
PJUD   = "data/pjud/Laborales"
OUT    = "data/_index/perfiles.sqlite3"

BR=re.compile(r"<br\s*/?>",re.I); TAG=re.compile(r"<[^>]+>")
RESULT={"acogida","rechazada","acogida_parcial","conciliacion","desistimiento","no_aplica"}
VIA={"apelacion","nulidad","ninguna","desconocido"}

PROMPT=('Eres analista de sentencias laborales chilenas. Del TEXTO (encabezado + parte resolutiva) '
'extrae el resultado del juicio en JSON. Campos:\n'
'- resultado: uno de acogida|rechazada|acogida_parcial|conciliacion|desistimiento|no_aplica '
'(acogida=demanda del trabajador acogida/empresa condenada; rechazada=demanda rechazada/empresa absuelta).\n'
'- materias: lista de despido_injustificado|despido_indebido|nulidad_despido|autodespido|cobro_prestaciones|tutela_derechos_fundamentales|accidente_trabajo|practica_antisindical|otra.\n'
'- monto_total_clp: suma total que se condena a pagar en pesos (entero) o null.\n'
'- defensas_empleador: lista de necesidades_empresa_art161|falta_probidad|incumplimiento_grave|caso_fortuito|vencimiento_plazo|conclusion_trabajo|niega_relacion_laboral|otra (las que invoque la empresa demandada).\n'
'- via_recursiva: apelacion|nulidad|ninguna|desconocido.\n'
'No inventes. Si no consta, usa null o "desconocido". Responde SOLO JSON: '
'{"resultado":"...","materias":[],"monto_total_clp":null,"defensas_empleador":[],"via_recursiva":"..."}\n\nTEXTO:\n')

def to_text(t):
    if isinstance(t,list): t=" ".join(map(str,t))
    return re.sub(r"\s+"," ",TAG.sub(" ",BR.sub(" ",t or ""))).strip()

def section(t):
    # encabezado (materia/partes) + parte resolutiva (el fallo está al final)
    head=t[:2000]; tail=t[-3500:] if len(t)>3500 else t
    return head+"\n[...]\n"+tail

def iter_records(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: data=json.load(f)
    if isinstance(data,dict):
        for k in ("docs","response","results","data"):
            if k in data: data=data[k]; break
        if isinstance(data,dict) and "docs" in data: data=data["docs"]
    yield from (data if isinstance(data,list) else [data])

def llm(sec, retries=2):
    body=json.dumps({"model":MODEL,"prompt":PROMPT+sec,"stream":False,"format":"json",
                     "options":{"temperature":0,"num_predict":300}}).encode()
    for i in range(retries):
        try:
            o=json.loads(urllib.request.urlopen(urllib.request.Request(
                OLLAMA,data=body,headers={"Content-Type":"application/json"}),timeout=180).read())
            d=json.loads(o.get("response","{}"))
            res=str(d.get("resultado","")).strip().lower()
            if res not in RESULT: res="no_aplica"
            via=str(d.get("via_recursiva","desconocido")).strip().lower()
            if via not in VIA: via="desconocido"
            mats=[str(m).strip().lower() for m in (d.get("materias") or []) if str(m).strip()][:6]
            defs=[str(x).strip().lower() for x in (d.get("defensas_empleador") or []) if str(x).strip()][:6]
            monto=d.get("monto_total_clp")
            monto=int(monto) if isinstance(monto,(int,float)) else None
            return res, ",".join(mats), monto, ",".join(defs), via
        except Exception:
            time.sleep(1.5*(i+1))
    return None

def init_db(p):
    c=sqlite3.connect(p,timeout=120); c.execute("PRAGMA busy_timeout=120000")
    c.execute("""CREATE TABLE IF NOT EXISTS laboral_resultado(
        sent_id TEXT PRIMARY KEY, anio INTEGER, resultado TEXT, materias TEXT,
        monto_total_clp INTEGER, defensas TEXT, via_recursiva TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_lr_res ON laboral_resultado(resultado)")
    c.commit(); return c

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workers",type=int,default=6); ap.add_argument("--limit",type=int)
    a=ap.parse_args()
    c=init_db(OUT); lock=Lock()
    done={r[0] for r in c.execute("SELECT sent_id FROM laboral_resultado").fetchall()}
    files=sorted(glob(f"{PJUD}/*.json.gz"))
    print(f"[laboral-resultado] {MODEL} via {OLLAMA} · {len(files)} archivos · hechos={len(done)} · workers={a.workers}",flush=True)
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
                if out is None and to_text(r.get("texto_sentencia") or r.get("texto_sentencia_anon")):
                    # error LLM (no texto-corto) → no marcar, reintentar luego
                    if len(to_text(r.get("texto_sentencia") or "") )>=300: continue
                anio=r.get("sent__FEC_ANIO_i")
                row=(sid,anio,*(out if out else ("no_aplica","",None,"","desconocido")))
                with lock:
                    c.execute("INSERT OR REPLACE INTO laboral_resultado VALUES(?,?,?,?,?,?,?)",row)
                    c.commit()
                proc+=1
                if proc%50==0:
                    print(f"  · {proc} sentencias · {proc/max(time.time()-t0,1):.2f}/s",flush=True)
                if a.limit and proc>=a.limit: break
        if a.limit and proc>=a.limit: break
    print(f"[FIN] {proc} sentencias · {proc/max(time.time()-t0,1):.2f}/s",flush=True)
    c.close()

if __name__=="__main__":
    main()
