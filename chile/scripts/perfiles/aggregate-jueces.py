#!/usr/bin/env python3
"""
Ficha Juez + Ficha Tribunal (laboral y penal) — recrea el "historial de jueces"
de las PPTs. Cruza el metadato PJUD (juez gls_juez_ss, tribunal gls_juz_s, materia,
año) con los resultados LLM (laboral_resultado / penal_resultado).

Laboral: tendencia de fallo (% acogida demanda trabajador), % monto aceptado, materias.
Penal: % condena, días de pena promedio, materias/delitos.

CPU puro (escanea json.gz). NO toca GPU ni las extracciones. Ver
[[project_legal_chile_perfiles_resumenes]] / [[reference_pjud_analitica_dashboard]].

Salida en perfiles.sqlite3: juez_perfil, tribunal_perfil.
Uso: python3 scripts/perfiles/aggregate-jueces.py [--min-causas 5]
"""
import argparse, gzip, json, os, sqlite3, collections, unicodedata, re
from glob import glob

PERFIL="data/_index/perfiles.sqlite3"
SKIP=re.compile(r"sin informaci|^s/i$|no registra|^\s*$",re.I)

def norm(s):
    s=unicodedata.normalize("NFD",s); s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.sub(r"\s+"," ",s.upper().strip())

def field_list(v):  # gls_juez_ss / gls_juz_s pueden ser str o list (bug str-vs-list)
    out=[]
    if isinstance(v,list):
        for x in v:
            if isinstance(x,str) and x.strip() and not SKIP.search(x): out.append(x.strip())
    elif isinstance(v,str) and v.strip() and not SKIP.search(v): out.append(v.strip())
    return out

def iter_records(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: data=json.load(f)
    if isinstance(data,dict):
        for k in ("docs","response","results","data"):
            if k in data: data=data[k]; break
        if isinstance(data,dict) and "docs" in data: data=data["docs"]
    yield from (data if isinstance(data,list) else [data])

def load_res(con,table,cols):
    return {r[0]:r[1:] for r in con.execute(f"SELECT sent_id,{cols} FROM {table}").fetchall()}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--min-causas",type=int,default=5); a=ap.parse_args()
    rc=sqlite3.connect(f"file:{os.path.abspath(PERFIL)}?immutable=1",uri=True)
    lab={}; pen={}
    try: lab=load_res(rc,"laboral_resultado","resultado,materias,monto_solicitado_clp,monto_acogido_clp")
    except Exception: pass
    try: pen=load_res(rc,"penal_resultado","decision,delitos,dias_pena")
    except Exception: pass
    rc.close()
    print(f"resultados: laboral={len(lab)} penal={len(pen)}",flush=True)

    # acumuladores: juez/tribunal → por competencia
    J=collections.defaultdict(lambda:{"disp":collections.Counter(),"trib":collections.Counter(),
        "comp":collections.Counter(),"mat":collections.Counter(),"n":0,
        "lab_n":0,"lab_acog":0,"lab_rech":0,"pcts":[],
        "pen_n":0,"pen_cond":0,"dias":[]})
    T=collections.defaultdict(lambda:{"disp":collections.Counter(),"comp":collections.Counter(),"n":0,
        "lab_n":0,"lab_acog":0,"pen_n":0,"pen_cond":0,"dias":[]})

    for comp in ("Laborales","Penales"):
        res = lab if comp=="Laborales" else pen
        for fp in sorted(glob(f"data/pjud/{comp}/*.json.gz")):
            for r in iter_records(fp):
                sid=str(r.get("id") or r.get("sent__crr_documento_i"))
                jueces=field_list(r.get("gls_juez_ss"))
                trib=field_list(r.get("gls_juz_s")) or field_list(r.get("gls_corte_s"))
                tname=trib[0] if trib else None
                rr=res.get(sid)
                for j in jueces:
                    k=norm(j); d=J[k]; d["disp"][j]+=1; d["n"]+=1; d["comp"][comp]+=1
                    if tname: d["trib"][tname]+=1
                    if comp=="Laborales" and rr:
                        resultado,materias,msol,macog=rr; d["lab_n"]+=1
                        if resultado in("acogida","acogida_parcial"): d["lab_acog"]+=1
                        elif resultado=="rechazada": d["lab_rech"]+=1
                        if msol and macog and msol>0: d["pcts"].append(min(100.0,100.0*macog/msol))
                        for m in (materias or "").split(","):
                            if m.strip(): d["mat"][m.strip()]+=1
                    elif comp=="Penales" and rr:
                        decision,delitos,dias=rr; d["pen_n"]+=1
                        if decision=="condena": d["pen_cond"]+=1
                        if dias: d["dias"].append(dias)
                        for m in (delitos or "").split(","):
                            if m.strip(): d["mat"][m.strip()]+=1
                if tname:
                    k=norm(tname); t=T[k]; t["disp"][tname]+=1; t["n"]+=1; t["comp"][comp]+=1
                    if comp=="Laborales" and rr:
                        t["lab_n"]+=1
                        if rr[0] in("acogida","acogida_parcial"): t["lab_acog"]+=1
                    elif comp=="Penales" and rr:
                        t["pen_n"]+=1
                        if rr[0]=="condena": t["pen_cond"]+=1
                        if rr[2]: t["dias"].append(rr[2])

    out=sqlite3.connect(PERFIL,timeout=120); out.execute("PRAGMA busy_timeout=120000")
    out.execute("""CREATE TABLE IF NOT EXISTS juez_perfil(
        juez_key TEXT PRIMARY KEY, juez TEXT, n_causas INTEGER, competencias TEXT, tribunal_principal TEXT,
        lab_n INTEGER, lab_tasa_acogida REAL, lab_pct_aceptado REAL,
        pen_n INTEGER, pen_tasa_condena REAL, pen_dias_pena_prom INTEGER, materias_top TEXT)""")
    out.execute("DELETE FROM juez_perfil")
    out.execute("""CREATE TABLE IF NOT EXISTS tribunal_perfil(
        tribunal_key TEXT PRIMARY KEY, tribunal TEXT, n_causas INTEGER, competencias TEXT,
        lab_n INTEGER, lab_tasa_acogida REAL, pen_n INTEGER, pen_tasa_condena REAL, pen_dias_pena_prom INTEGER)""")
    out.execute("DELETE FROM tribunal_perfil")
    nj=0
    for k,d in J.items():
        if d["n"]<a.min_causas: continue
        labden=d["lab_acog"]+d["lab_rech"]
        out.execute("INSERT INTO juez_perfil VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(
            k, d["disp"].most_common(1)[0][0], d["n"],
            ",".join(f"{c}:{n}" for c,n in d["comp"].most_common()),
            d["trib"].most_common(1)[0][0] if d["trib"] else None,
            d["lab_n"], round(d["lab_acog"]/labden,3) if labden else None,
            round(sum(d["pcts"])/len(d["pcts"]),1) if d["pcts"] else None,
            d["pen_n"], round(d["pen_cond"]/d["pen_n"],3) if d["pen_n"] else None,
            int(sum(d["dias"])/len(d["dias"])) if d["dias"] else None,
            ",".join(f"{x}:{c}" for x,c in d["mat"].most_common(6)))); nj+=1
    nt=0
    for k,d in T.items():
        if d["n"]<a.min_causas: continue
        out.execute("INSERT INTO tribunal_perfil VALUES(?,?,?,?,?,?,?,?,?)",(
            k, d["disp"].most_common(1)[0][0], d["n"],
            ",".join(f"{c}:{n}" for c,n in d["comp"].most_common()),
            d["lab_n"], round(d["lab_acog"]/d["lab_n"],3) if d["lab_n"] else None,
            d["pen_n"], round(d["pen_cond"]/d["pen_n"],3) if d["pen_n"] else None,
            int(sum(d["dias"])/len(d["dias"])) if d["dias"] else None)); nt+=1
    out.commit()
    print(f"juez_perfil: {nj} jueces · tribunal_perfil: {nt} tribunales\n")
    print("--- TOP jueces laborales (tendencia de fallo) ---")
    for r in out.execute("""SELECT juez,lab_n,lab_tasa_acogida,lab_pct_aceptado,tribunal_principal FROM juez_perfil
                            WHERE lab_n>=10 ORDER BY lab_n DESC LIMIT 8"""):
        print(f"  {r[0][:34]:<35} causas-lab={r[1]:>4} acoge={round((r[2] or 0)*100)}% %acept={r[3] or '-'} · {(r[4] or '')[:30]}")
    print("--- TOP jueces penales (condena + días pena) ---")
    for r in out.execute("""SELECT juez,pen_n,pen_tasa_condena,pen_dias_pena_prom FROM juez_perfil
                            WHERE pen_n>=10 ORDER BY pen_n DESC LIMIT 8"""):
        print(f"  {r[0][:34]:<35} causas-pen={r[1]:>4} condena={round((r[2] or 0)*100)}% dias_pena_prom={r[3] or '-'}")
    out.close()

if __name__=="__main__": main()
