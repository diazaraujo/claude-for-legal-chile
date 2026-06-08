#!/usr/bin/env python3
"""Exporta los JSON del explorador de entidades (frontend legalchile/public/data/):
jueces, tribunales, empresas (de las tablas *_perfil de perfiles.sqlite3) y
abogados, fiscales (de partes.sqlite3 cruzado con los resultados extraídos).

Reusable: re-correr cuando avance/termine la extracción para refrescar las fichas.
Uso: python3 scripts/perfiles/export-explorer-json.py
"""
import sqlite3, json, collections
PERF = "data/_index/perfiles.sqlite3"
PART = "data/_index/partes.sqlite3"
OUT  = "legalchile/frontend/public/data"

# Conectores que van en minúscula dentro de un nombre propio (no al inicio).
_LOWER = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "von", "van", "di"}
def cap(n):
    """Normaliza casing a Título respetando conectores y acentos.
    'MAURICIO MIERES MUJICA' -> 'Mauricio Mieres Mujica'; 'FISCO DE CHILE' -> 'Fisco de Chile'."""
    n = (n or "").strip()
    if not n:
        return n
    out = []
    for i, w in enumerate(n.split()):
        wl = w.lower()
        if i > 0 and wl in _LOWER:
            out.append(wl)
        else:
            out.append(wl[:1].upper() + wl[1:])
    return " ".join(out)

def topk(c, k=8): return [[a, b] for a, b in c.most_common(k)]
def f(x, n=3): return round(x, n) if isinstance(x, (int, float)) else None
def mats(s): return [m.strip().replace('_', ' ') for m in (s or '').split(',') if m.strip()]
def clean(n):
    n = (n or '').strip()
    if len(n) < 6 or n.replace(' ', '').isdigit(): return None
    if n.lower() in ('si defensa', 'sin defensa', 'no informa', 'sin informacion'): return None
    return n

pc = sqlite3.connect(PERF, timeout=60)

# ---- jueces / tribunales / empresas (de *_perfil) ----
jr = []
for r in pc.execute("SELECT juez_key,juez,n_causas,competencias,tribunal_principal,lab_n,lab_tasa_acogida,pen_n,pen_tasa_condena,pen_dias_pena_prom,materias_top FROM juez_perfil WHERE juez IS NOT NULL AND n_causas>=1 ORDER BY n_causas DESC"):
    jr.append({"key": r[0], "nombre": cap(r[1]), "n": r[2], "comp": r[3], "trib": cap(r[4]), "lab_n": r[5], "lab_acogida": f(r[6]), "pen_n": r[7], "pen_condena": f(r[8]), "pen_dias": f(r[9], 1), "materias": [[k.replace('_', ' '), int(v)] for k, v in (x.rsplit(':', 1) for x in (r[10] or '').split(',') if ':' in x)][:8]})
json.dump(jr, open(f"{OUT}/jueces.json", "w"), ensure_ascii=False)

tr = []
for r in pc.execute("SELECT tribunal_key,tribunal,n_causas,competencias,lab_n,lab_tasa_acogida,pen_n,pen_tasa_condena,pen_dias_pena_prom FROM tribunal_perfil WHERE tribunal IS NOT NULL AND n_causas>=1 ORDER BY n_causas DESC"):
    tr.append({"key": r[0], "nombre": cap(r[1]), "n": r[2], "comp": r[3], "lab_n": r[4], "lab_acogida": f(r[5]), "pen_n": r[6], "pen_condena": f(r[7]), "pen_dias": f(r[8], 1)})
json.dump(tr, open(f"{OUT}/tribunales.json", "w"), ensure_ascii=False)

er = []
for r in pc.execute("SELECT empresa_key,empresa,n_juicios,n_con_resultado,tasa_condena,tasa_rechazo,tasa_conciliacion,pct_aceptado_prom,monto_acogido_total_clp,defensas_top,materias_top FROM empresa_laboral_perfil WHERE empresa IS NOT NULL AND n_juicios>=1 ORDER BY n_juicios DESC"):
    def parse(s): return [[k.replace('_', ' '), int(v)] for k, v in (x.rsplit(':', 1) for x in (s or '').split(',') if ':' in x)][:8]
    er.append({"key": r[0], "nombre": cap(r[1]), "n": r[2], "nres": r[3], "condena": f(r[4]), "rechazo": f(r[5]), "concil": f(r[6]), "pct_acept": f(r[7]), "monto": r[8], "defensas": parse(r[9]), "materias": parse(r[10])})
json.dump(er, open(f"{OUT}/empresas.json", "w"), ensure_ascii=False)

# ---- abogados / fiscales (de partes × resultados) ----
lab = {r[0]: r[1] for r in pc.execute("SELECT sent_id,materias FROM laboral_resultado")}
pen = {r[0]: (r[1], r[2]) for r in pc.execute("SELECT sent_id,decision,delitos FROM penal_resultado")}
pc.close()

prt = sqlite3.connect(PART, timeout=60)
dem = collections.defaultdict(list)
for sid, nom in prt.execute("SELECT sent_id,nombre FROM partes WHERE rol IN ('demandado','representante_legal') AND competencia='Laborales'"):
    if nom: dem[sid].append(nom.strip())

ab = collections.defaultdict(lambda: {"nombre": None, "sids": set(), "comp": collections.Counter(), "yr": [], "mat": collections.Counter(), "cp": collections.Counter()})
for sid, comp, nom, key, anio in prt.execute("SELECT sent_id,competencia,nombre,nombre_key,anio FROM partes WHERE rol IN ('abogado_patrocinante','apoderado','defensor')"):
    nm = clean(nom)
    if not nm: continue
    d = ab[key]; d["nombre"] = d["nombre"] or nm; d["sids"].add(sid); d["comp"][comp] += 1
    if anio: d["yr"].append(anio)
    for m in mats(lab.get(sid)): d["mat"][m] += 1
    if sid in pen and pen[sid][1]:
        for m in mats(pen[sid][1]): d["mat"][m] += 1
    for e in dem.get(sid, []):
        if clean(e): d["cp"][e] += 1
abr = []
for k, d in ab.items():
    n = len(d["sids"])
    if n < 1: continue
    yr = sorted(d["yr"]); rng = f"{yr[0]}–{yr[-1]}" if yr else ""
    abr.append({"key": k, "nombre": cap(d["nombre"]), "n": n, "comp": d["comp"].most_common(1)[0][0] if d["comp"] else "", "years": rng, "materias": topk(d["mat"]), "contrapartes": [[cap(a), b] for a, b in topk(d["cp"], 6)]})
abr.sort(key=lambda x: -x["n"])
json.dump(abr, open(f"{OUT}/abogados.json", "w"), ensure_ascii=False)

fi = collections.defaultdict(lambda: {"nombre": None, "sids": set(), "yr": [], "cond": 0, "res": 0, "del": collections.Counter()})
for sid, nom, key, anio in prt.execute("SELECT sent_id,nombre,nombre_key,anio FROM partes WHERE rol='fiscal'"):
    nm = clean(nom)
    if not nm: continue
    d = fi[key]; d["nombre"] = d["nombre"] or nm; d["sids"].add(sid)
    if anio: d["yr"].append(anio)
    if sid in pen:
        dec, dl = pen[sid]
        if dec in ("condena", "absolucion"): d["res"] += 1; d["cond"] += (1 if dec == "condena" else 0)
        for m in mats(dl): d["del"][m] += 1
prt.close()
fir = []
for k, d in fi.items():
    n = len(d["sids"])
    if n < 1: continue
    yr = sorted(d["yr"]); rng = f"{yr[0]}–{yr[-1]}" if yr else ""
    fir.append({"key": k, "nombre": cap(d["nombre"]), "n": n, "years": rng, "condena": round(d["cond"] / d["res"], 3) if d["res"] else None, "nres": d["res"], "delitos": topk(d["del"])})
fir.sort(key=lambda x: -x["n"])
json.dump(fir, open(f"{OUT}/fiscales.json", "w"), ensure_ascii=False)

print(f"export OK · jueces={len(jr)} tribunales={len(tr)} empresas={len(er)} abogados={len(abr)} fiscales={len(fir)}")
