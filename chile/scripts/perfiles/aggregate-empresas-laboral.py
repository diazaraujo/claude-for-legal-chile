#!/usr/bin/env python3
"""
Agrega el perfil de ESTRATEGIA LABORAL por empresa: cruza las empresas demandadas
en Laborales (de partes.sqlite3, FASE0/FASE1) con el resultado extraído por LLM
(laboral_resultado en perfiles.sqlite3) → una fila por empresa con sus métricas.
CPU puro. Alimenta el resumen LLM final. Ver [[project_legal_chile_perfiles_resumenes]].

Salida: tabla `empresa_laboral_perfil` en perfiles.sqlite3:
  empresa, n_juicios, anios, tasa_condena, tasa_rechazo, tasa_conciliacion,
  monto_total_clp, monto_promedio_clp, defensas_top, materias_top

Uso: python3 scripts/perfiles/aggregate-empresas-laboral.py [--min-juicios 5]
"""
import argparse, sqlite3, collections, os

PARTES = "data/_index/partes.sqlite3"
PERFIL = "data/_index/perfiles.sqlite3"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--min-juicios",type=int,default=5); a=ap.parse_args()
    # empresas demandadas en Laborales (sent_id list por empresa) — read-only (FASE1 escribe)
    pc=sqlite3.connect(f"file:{os.path.abspath(PARTES)}?immutable=1",uri=True)
    rows=pc.execute("""SELECT nombre_key, nombre, sent_id FROM partes
                       WHERE rol='demandado' AND competencia='Laborales'""").fetchall()
    pc.close()
    emp=collections.defaultdict(lambda:{"display":collections.Counter(),"sids":set()})
    for k,n,sid in rows:
        emp[k]["display"][n]+=1; emp[k]["sids"].add(sid)

    # resultados laborales por sent_id
    rc=sqlite3.connect(f"file:{os.path.abspath(PERFIL)}?immutable=1",uri=True)
    res={r[0]:r[1:] for r in rc.execute(
        "SELECT sent_id,resultado,materias,monto_total_clp,defensas FROM laboral_resultado").fetchall()}
    rc.close()

    out=sqlite3.connect(PERFIL)
    out.execute("""CREATE TABLE IF NOT EXISTS empresa_laboral_perfil(
        empresa_key TEXT PRIMARY KEY, empresa TEXT, n_juicios INTEGER, n_con_resultado INTEGER,
        tasa_condena REAL, tasa_rechazo REAL, tasa_conciliacion REAL,
        monto_total_clp INTEGER, monto_promedio_clp INTEGER, defensas_top TEXT, materias_top TEXT)""")
    out.execute("DELETE FROM empresa_laboral_perfil")
    n_emp=0
    for k,d in emp.items():
        if len(d["sids"])<a.min_juicios: continue
        sids=d["sids"]; display=d["display"].most_common(1)[0][0]
        cond=rech=conc=0; nres=0; montos=[]; defs=collections.Counter(); mats=collections.Counter()
        for sid in sids:
            if sid not in res: continue
            nres+=1; resultado,materias,monto,defensas=res[sid]
            if resultado in ("acogida","acogida_parcial"): cond+=1
            elif resultado=="rechazada": rech+=1
            elif resultado=="conciliacion": conc+=1
            if monto: montos.append(monto)
            for x in (defensas or "").split(","):
                if x.strip(): defs[x.strip()]+=1
            for x in (materias or "").split(","):
                if x.strip(): mats[x.strip()]+=1
        nj=len(sids)
        out.execute("INSERT INTO empresa_laboral_perfil VALUES(?,?,?,?,?,?,?,?,?,?,?)",(
            k, display, nj, nres,
            round(cond/nres,3) if nres else None,
            round(rech/nres,3) if nres else None,
            round(conc/nres,3) if nres else None,
            sum(montos) if montos else None,
            int(sum(montos)/len(montos)) if montos else None,
            ",".join(f"{x}:{c}" for x,c in defs.most_common(5)),
            ",".join(f"{x}:{c}" for x,c in mats.most_common(5))))
        n_emp+=1
    out.commit()
    print(f"empresa_laboral_perfil: {n_emp} empresas (>= {a.min_juicios} juicios) · resultados disponibles para {len(res)} sentencias")
    for r in out.execute("""SELECT empresa,n_juicios,n_con_resultado,tasa_condena,materias_top
                            FROM empresa_laboral_perfil ORDER BY n_juicios DESC LIMIT 10"""):
        print(" ",r)
    out.close()

if __name__=="__main__":
    main()
