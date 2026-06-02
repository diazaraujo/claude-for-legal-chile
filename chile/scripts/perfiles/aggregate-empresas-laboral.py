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

    # resultados laborales por sent_id (schema enriquecido: solicitado + acogido)
    rc=sqlite3.connect(f"file:{os.path.abspath(PERFIL)}?immutable=1",uri=True)
    res={r[0]:r[1:] for r in rc.execute(
        "SELECT sent_id,resultado,materias,monto_solicitado_clp,monto_acogido_clp,defensas FROM laboral_resultado").fetchall()}
    rc.close()

    out=sqlite3.connect(PERFIL,timeout=120); out.execute("PRAGMA busy_timeout=120000")
    out.execute("""CREATE TABLE IF NOT EXISTS empresa_laboral_perfil(
        empresa_key TEXT PRIMARY KEY, empresa TEXT, n_juicios INTEGER, n_con_resultado INTEGER,
        tasa_condena REAL, tasa_rechazo REAL, tasa_conciliacion REAL, pct_aceptado_prom REAL,
        monto_acogido_total_clp INTEGER, monto_acogido_prom_clp INTEGER, defensas_top TEXT, materias_top TEXT)""")
    out.execute("DELETE FROM empresa_laboral_perfil")
    n_emp=0
    for k,d in emp.items():
        if len(d["sids"])<a.min_juicios: continue
        sids=d["sids"]; display=d["display"].most_common(1)[0][0]
        cond=rech=conc=0; nres=0; acog=[]; pcts=[]; defs=collections.Counter(); mats=collections.Counter()
        for sid in sids:
            if sid not in res: continue
            nres+=1; resultado,materias,m_sol,m_acog,defensas=res[sid]
            if resultado in ("acogida","acogida_parcial"): cond+=1
            elif resultado=="rechazada": rech+=1
            elif resultado in ("conciliacion","avenimiento"): conc+=1
            if m_acog: acog.append(m_acog)
            if m_sol and m_acog and m_sol>0: pcts.append(min(100.0,100.0*m_acog/m_sol))
            for x in (defensas or "").split(","):
                if x.strip(): defs[x.strip()]+=1
            for x in (materias or "").split(","):
                if x.strip(): mats[x.strip()]+=1
        nj=len(sids)
        out.execute("INSERT INTO empresa_laboral_perfil VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(
            k, display, nj, nres,
            round(cond/nres,3) if nres else None,
            round(rech/nres,3) if nres else None,
            round(conc/nres,3) if nres else None,
            round(sum(pcts)/len(pcts),1) if pcts else None,
            sum(acog) if acog else None,
            int(sum(acog)/len(acog)) if acog else None,
            ",".join(f"{x}:{c}" for x,c in defs.most_common(5)),
            ",".join(f"{x}:{c}" for x,c in mats.most_common(5))))
        n_emp+=1
    out.commit()
    print(f"empresa_laboral_perfil: {n_emp} empresas (>= {a.min_juicios} juicios) · resultados disponibles para {len(res)} sentencias\n")
    print(f"{'EMPRESA':<42}{'juicios':>8}{'c/result':>9}{'%cond':>7}{'%acept':>8}  defensas_top")
    for r in out.execute("""SELECT empresa,n_juicios,n_con_resultado,tasa_condena,pct_aceptado_prom,defensas_top
                            FROM empresa_laboral_perfil WHERE n_con_resultado>0 ORDER BY n_con_resultado DESC LIMIT 15"""):
        emp_n,nj,nr,tc,pa,dft=r
        print(f"{(emp_n or '')[:40]:<42}{nj:>8}{nr:>9}{(str(round(tc*100))+'%' if tc is not None else '-'):>7}{(str(pa)+'%' if pa else '-'):>8}  {(dft or '')[:40]}")
    out.close()

if __name__=="__main__":
    main()
