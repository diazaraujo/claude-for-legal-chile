#!/usr/bin/env python3
"""Exporta los JSON del explorador de entidades (frontend legalchile/public/data/):
jueces, tribunales, empresas (de las tablas *_perfil de perfiles.sqlite3) y
abogados, fiscales (de partes.sqlite3 cruzado con los resultados extraídos).

Reusable: re-correr cuando avance/termine la extracción para refrescar las fichas.
Uso: python3 scripts/perfiles/export-explorer-json.py
"""
import sqlite3, json, collections, os
PERF = "data/_index/perfiles.sqlite3"
PART = "data/_index/partes.sqlite3"
ENR  = "data/_index/jueces_enriched.sqlite3"
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
def mat_juez(r10, r11):
    # materias_outcome (JSON [[materia, n, tasa, tipo], ...]) → [[label, n, tasa, tipo]]
    if r11:
        try:
            return [[m[0].replace('_', ' '), m[1], m[2], m[3]] for m in json.loads(r11)][:8]
        except Exception:
            pass
    return [[k.replace('_', ' '), int(v), None, None] for k, v in (x.rsplit(':', 1) for x in (r10 or '').split(',') if ':' in x)][:8]
for r in pc.execute("SELECT juez_key,juez,n_causas,competencias,tribunal_principal,lab_n,lab_tasa_acogida,pen_n,pen_tasa_condena,pen_dias_pena_prom,materias_top,materias_outcome,def_pub_n,def_pub_rate,def_priv_n,def_priv_rate FROM juez_perfil WHERE juez IS NOT NULL AND n_causas>=1 ORDER BY n_causas DESC"):
    row = {"key": r[0], "nombre": cap(r[1]), "n": r[2], "comp": r[3], "trib": cap(r[4]), "lab_n": r[5], "lab_acogida": f(r[6]), "pen_n": r[7], "pen_condena": f(r[8]), "pen_dias": f(r[9], 1), "materias": mat_juez(r[10], r[11])}
    # defensor público vs privado (solo si hay muestra mínima en al menos un lado)
    if (r[12] or 0) >= 15 or (r[14] or 0) >= 15:
        row["defensor"] = {"pub_n": r[12] or 0, "pub_rate": f(r[13]), "priv_n": r[14] or 0, "priv_rate": f(r[15])}
    jr.append(row)

# ---- capa enriquecida PÚBLICA: SOLO la reseña IA (derivada de sentencias públicas). ----
# La ficha civil de Mallas (RUT/avalúo/familia) NO va al sitio público: incluye datos
# personales de terceros (familiares). El patrimonio público del juez se traerá de la
# Declaración de Patrimonio e Intereses (Ley 20.880 / InfoProbidad), fuente oficial pública.
if os.path.exists(ENR):
    ec = sqlite3.connect(f"file:{ENR}?mode=ro", uri=True)
    bios = {e[0]: e[1] for e in ec.execute(
        "SELECT juez_key,biografia FROM juez_enriched WHERE biografia IS NOT NULL AND biografia<>''")}
    ec.close()
    for j in jr:
        if j["key"] in bios:
            j["bio"] = bios[j["key"]]
    # patrimonio PÚBLICO: Declaración de Patrimonio e Intereses (Ley 20.880 / InfoProbidad).
    # Fuente oficial pública, resumen agregado (sin direcciones), SOLO el funcionario.
    ec2 = sqlite3.connect(f"file:{ENR}?mode=ro", uri=True)
    hist = {}
    try:
        for r in ec2.execute(
            "SELECT juez_key,fecha_declaracion,cargo,n_inmuebles,avaluo_inmuebles,n_vehiculos,avaluo_vehiculos,n_pasivos "
            "FROM juez_declaracion_hist ORDER BY fecha_declaracion"):
            hist.setdefault(r[0], []).append(r)
    except Exception:
        hist = {}
    if not hist:  # fallback: tabla de solo-última si no hay histórico
        try:
            for r in ec2.execute("SELECT juez_key,fecha_declaracion,cargo,n_inmuebles,avaluo_inmuebles,n_vehiculos,avaluo_vehiculos,n_pasivos FROM juez_declaracion"):
                hist[r[0]] = [r]
        except Exception:
            pass
    ec2.close()
    for j in jr:
        rows = hist.get(j["key"])
        if not rows:
            continue
        last = rows[-1]
        j["patrimonio"] = {"fecha": (last[1] or "")[:10] or None, "cargo": cap(last[2]),
                           "n_inmuebles": last[3], "avaluo_inmuebles": last[4],
                           "n_vehiculos": last[5], "avaluo_vehiculos": last[6], "n_pasivos": last[7]}
        if len(rows) > 1:
            ts = [{"fecha": (r[1] or "")[:10], "inm": r[3], "av_inm": r[4],
                   "veh": r[5], "av_veh": r[6], "pas": r[7]} for r in rows]
            j["patrimonio"]["hist"] = ts
            # tendencia robusta: media de la mitad reciente vs la antigua (evita ruido de 1 declaración)
            tot = [(t["av_inm"] or 0) + (t["av_veh"] or 0) for t in ts]
            n = len(tot); hf = max(1, n // 2)
            early = sum(tot[:hf]) / hf
            late = sum(tot[hf:]) / (n - hf) if (n - hf) else tot[-1]
            ratio = (late / early) if early > 0 else None
            direc = ("up" if ratio >= 1.15 else "down" if ratio <= 0.87 else "flat") if ratio else "na"
            j["patrimonio"]["tendencia"] = {
                "dir": direc, "ratio": round(ratio, 2) if ratio else None,
                "desde": ts[0]["fecha"][:4], "hasta": ts[-1]["fecha"][:4],
                "peak": max(tot), "actual": tot[-1]}
    # LinkedIn (trayectoria + educación, filtrado a coherencia judicial; método icare).
    ec3 = sqlite3.connect(f"file:{ENR}?mode=ro", uri=True)
    lkd = {}
    try:
        for jk, url, job, comp, head, edu in ec3.execute("SELECT juez_key,url,job_title,company,headline,educacion FROM juez_linkedin"):
            try:
                educ = [e for e in json.loads(edu or "[]") if e.get("school")]
            except Exception:
                educ = []
            lkd[jk] = {"url": url, "job": job, "company": comp, "headline": head, "edu": educ[:2]}
    except Exception:
        pass
    ec3.close()
    for j in jr:
        if j["key"] in lkd:
            j["linkedin"] = lkd[j["key"]]
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
