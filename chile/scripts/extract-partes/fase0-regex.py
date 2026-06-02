#!/usr/bin/env python3
"""
FASE 0 — Extracción por regex de PARTES, ABOGADOS y FISCALES sobre el
encabezamiento / parte expositiva de las sentencias PJUD.

Fundamento (deep-research #2): el Art. 170 CPC obliga a "designación precisa de
las partes" y la comparecencia/patrocinio se expresan con fórmulas estables en
el encabezamiento. NO toca los considerandos (idiosincráticos). Sin GPU, sin LLM.
Lo que el regex NO atrapa pasa luego a FASE 1 (LLM structured extraction).

Roles extraídos:
  PENAL    fiscal, defensor (penal público / privado), querellante, acusado
  LABORAL/ demandante (compareciente), demandado, representante_legal,
  CIVIL    abogado_patrocinante, apoderado

Uso:
  python3 scripts/extract-partes/fase0-regex.py --sample           # 1 archivo/competencia
  python3 scripts/extract-partes/fase0-regex.py --comp Penales --limit 2000
  python3 scripts/extract-partes/fase0-regex.py --all --out data/_index/partes.sqlite3
"""
import argparse, gzip, json, os, re, sqlite3, sys, unicodedata
from glob import glob

PJUD_DIR = "data/pjud"
COMPS = ["Civiles","Cobranza","Corte_de_Apelaciones","Corte_Suprema","Familia","Laborales","Penales"]

# ---- normalización de nombres (para clave de dedup, NO para display) ----
def norm_key(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.upper()
    s = re.sub(r"[^A-ZÑ ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ---- patrón de nombre: 2 a 5 tokens capitalizados (UPPER o Title), con conectores ----
TOK = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ’'`]+"
CONN = r"(?:de|del|de\s+la|de\s+los|la|los|y)"
NAME = rf"(?:{TOK})(?:\s+(?:{CONN}\s+)?{TOK}){{1,4}}"

def _name(label):  # named capture — case-sensitive aunque el patrón lleve re.I,
    return rf"(?-i:(?P<{label}>{NAME}))"  # para que el nombre dependa de la MAYÚSCULA

# Cortar el nombre si arrastra basura (palabras-función comunes tras el nombre)
STOP_AFTER = re.compile(r"\b(?:chileno|chilena|c[eé]dula|domiciliad|cesante|del giro|"
                        r"abogad|profesi[oó]n|RUT|RUN|RUC|RIT|en representaci|quien|"
                        r"se ignora|empleada|empleado|jubilad|comuna|nacid|deudor|"
                        r"por la suma|de su denominaci|ambos con|"
                        # etiquetas de rol — cortan el sangrado en formato tabular "FISCAL X DEFENSOR Y"
                        r"defensor|p[uú]blic|privad|juez|jueza|ministr|querellant|"
                        r"fiscal|nacional|regional|secretari|imputad|acusad|víctima|victima)", re.I)
LEAD_DDON = re.compile(r"^(?:don|doña|do[nñ]a|el|la|los|las|sr|sra|señor[a]?|empresa|sociedad)\s+", re.I)

def clean_name(raw):
    if not raw: return None
    raw = raw.strip(" ,.;:")
    m = STOP_AFTER.search(raw)
    if m: raw = raw[:m.start()].strip(" ,.;:")
    raw = LEAD_DDON.sub("", raw).strip(" ,.;:")  # quitar tratamiento residual
    toks = raw.split()
    if not (2 <= len(toks) <= 6): return None
    if norm_key(raw) in ("", "DON","DOÑA","DONA"): return None
    return raw

DDON = r"(?:don|doña|do[nñ]a|el|la|los|las|sr\.?|sra\.?|señor[a]?)\s+"

# ---------- patrones por rol ----------
PAT = {
 # PENAL
 "fiscal": [
    re.compile(rf"intervino\s+(?:el|la)\s+fiscal(?:\s+(?:adjunt[oa]|jefe|regional|militar))?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"(?:el|la)\s+[Ff]iscal\s+(?:adjunt[oa]\s+|jefe\s+)?{DDON}?{_name('n')}\s+(?:sostuvo|formaliz|acus|dedujo|present|sostiene|expuso)", re.I),
    re.compile(rf"Ministerio\s+P[uú]blico[,;]?\s+(?:en cuya representaci[oó]n\s+)?(?:intervino|compareci[oó]|estuvo representad[oa] por|represent[oó]\s+por)\s+(?:el|la)?\s*fiscal\s+{DDON}?{_name('n')}", re.I),
    # formas frecuentes que faltaban (diagnóstico empírico):
    re.compile(rf"representad[oa]?\s+(?:legalmente\s+)?por\s+(?:el|la)\s+fiscal(?:\s+adjunt[oa])?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"(?:intervenci[oó]n|preguntas|parte|cargo)\s+de\s+(?:el|la)\s+fiscal(?:\s+adjunt[oa])?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"\bfiscal(?:\s+adjunt[oa]|\s+jefe)?\s*:\s*{_name('n')}", re.I),  # tabular "FISCAL: NOMBRE"
 ],
 "defensor": [
    re.compile(rf"defensor[a]?\s+(?:penal\s+)?(?:p[uú]blic[oa]|privad[oa])\s*:?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"(?:la\s+)?[Dd]efensa\s+(?:del\s+(?:acusado|imputado|sentenciado|requerido)\s+)?(?:estuvo\s+a\s+cargo\s+de|fue\s+ejercida\s+por|la\s+ejerci[oó])\s+(?:el|la)?\s*(?:defensor[a]?|abogad[oa])?(?:\s+penal\s+p[uú]blic[oa])?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"defensor[a]?\s+(?:penal\s+)?(?:privad[oa]\s+)?{DDON}?{_name('n')}\s+(?:asumi|ejerci|represent|qui[eé]n)", re.I),
 ],
 "querellante": [
    re.compile(rf"querellante[,;]?\s+{DDON}?{_name('n')}", re.I),
 ],
 "acusado": [
    re.compile(rf"(?:en contra del|contra el)\s+acusad[oa]\s+{_name('n')}", re.I),
    re.compile(rf"^Acusad[oa]\s+{_name('n')}", re.I|re.M),
 ],
 # LABORAL / CIVIL
 "demandante": [
    re.compile(rf"compareci[oó]\s+{DDON}{_name('n')}", re.I),
    re.compile(rf"(?:comparece|interpone\s+demanda)\s+{DDON}{_name('n')}", re.I),
 ],
 "demandado": [
    re.compile(rf"demanda\s+a\s+(?:su\s+ex\s+empleador[a]?\s+)?(?:la\s+empresa\s+|la\s+sociedad\s+)?{_name('n')}", re.I),
    re.compile(rf"en\s+contra\s+de\s+(?!(?:el\s+|la\s+)?(?:acusad|imputad|requerid|sentenciad|condenad))(?:la\s+empresa\s+|la\s+sociedad\s+)?{_name('n')}", re.I),
 ],
 "representante_legal": [
    re.compile(rf"representad[oa]\s+legalmente\s+por\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"en\s+representaci[oó]n\s+(?:legal\s+)?de[l]?\s+(?:la\s+)?(?:empresa\s+|sociedad\s+)?{_name('n')}", re.I),
 ],
 "abogado_patrocinante": [
    re.compile(rf"patrocinad[oa]\s+por\s+(?:el|la)?\s*abogad[oa]\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"abogad[oa]\s+patrocinante[,;]?\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"patrocinio\s+y\s+poder\s+(?:a|al|del)?\s*(?:abogad[oa]\s+)?{DDON}?{_name('n')}", re.I),
    # formas dominantes que faltaban (diagnóstico empírico): "por el abogado X", "comparece el abogado X", "abogado don X"
    re.compile(rf"(?:por|de)\s+(?:el|la|su)\s+abogad[oa]\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"compareci?[eoó]+\s+(?:el|la)\s+abogad[oa]\s+{DDON}?{_name('n')}", re.I),
    re.compile(rf"\babogad[oa]\s+{DDON}{_name('n')}", re.I),  # "abogado don/doña X"
    re.compile(rf"patrocini[oa]\s+de\s+(?:el|la)?\s*(?:abogad[oa]\s+)?{DDON}?{_name('n')}", re.I),
 ],
 "apoderado": [
    re.compile(rf"apoderad[oa]\s+{DDON}{_name('n')}", re.I),
    re.compile(rf"confiere\s+poder\s+a\s+{DDON}?(?:abogad[oa]\s+)?{_name('n')}", re.I),
 ],
}

BR = re.compile(r"<br\s*/?>", re.I)
TAG = re.compile(r"<[^>]+>")

def to_text(txt):
    if isinstance(txt, list): txt = " ".join(str(t) for t in txt)
    txt = BR.sub(" ", txt or "")
    txt = TAG.sub(" ", txt)
    return re.sub(r"\s+", " ", txt).strip()

def extract(text):
    """Devuelve dict rol -> [nombres únicos]. Encabezamiento = primeros 4500 chars;
       patrocinio/poder se busca en todo el texto (aparece más tarde)."""
    head = text[:4500]
    out = {}
    for role, pats in PAT.items():
        # patrocinante/apoderado a veces aparecen después → buscar en texto completo
        scope = text if role in ("abogado_patrocinante","apoderado") else head
        seen, names = set(), []
        for pat in pats:
            for m in pat.finditer(scope):
                nm = clean_name(m.group("n"))
                if not nm: continue
                k = norm_key(nm)
                if k in seen: continue
                seen.add(k); names.append(nm)
        if names: out[role] = names
    return out

def iter_records(path):
    with gzip.open(path,"rt",encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        for k in ("docs","response","results","data"):
            if k in data: data = data[k]; break
        if isinstance(data, dict) and "docs" in data: data = data["docs"]
    yield from (data if isinstance(data, list) else [data])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp"); ap.add_argument("--sample", action="store_true")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--limit", type=int)
    ap.add_argument("--out"); ap.add_argument("--show", type=int, default=8)
    a = ap.parse_args()

    if a.sample: files = [sorted(glob(f"{PJUD_DIR}/{c}/*.json.gz"))[:1] for c in COMPS]; files=[f for s in files for f in s]
    elif a.comp:  files = sorted(glob(f"{PJUD_DIR}/{a.comp}/*.json.gz"))
    elif a.all:   files = sorted(glob(f"{PJUD_DIR}/*/*.json.gz"))
    else: ap.error("usa --sample, --comp o --all")

    con=None
    if a.out:
        con=sqlite3.connect(a.out); con.execute("PRAGMA busy_timeout=120000")
        con.execute("""CREATE TABLE IF NOT EXISTS partes(
          sent_id TEXT, competencia TEXT, rol TEXT, nombre TEXT, nombre_key TEXT, anio INTEGER)""")
        con.execute("CREATE INDEX IF NOT EXISTS ix_key ON partes(nombre_key)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_rol ON partes(rol)")

    from collections import Counter, defaultdict
    tot=0; with_text=0; hit=0; role_docs=Counter(); role_ents=Counter()
    examples=defaultdict(list)
    for fp in files:
        comp = fp.split("/")[-2]
        for r in iter_records(fp):
            if a.limit and tot>=a.limit: break
            tot+=1
            text = to_text(r.get("texto_sentencia") or r.get("texto_sentencia_anon"))
            if not text: continue
            with_text+=1
            res = extract(text)
            if res:
                hit+=1
                anio = r.get("sent__FEC_ANIO_i")
                sid = r.get("id") or r.get("sent__crr_documento_i")
                for role, names in res.items():
                    role_docs[role]+=1; role_ents[role]+=len(names)
                    if len(examples[role])<a.show:
                        examples[role].append((comp, names))
                    if con:
                        for nm in names:
                            con.execute("INSERT INTO partes VALUES(?,?,?,?,?,?)",
                                        (str(sid), comp, role, nm, norm_key(nm), anio))
        if con: con.commit()
        if a.limit and tot>=a.limit: break

    print(f"\n===== FASE 0 regex · {tot} sentencias ({with_text} con texto) =====")
    print(f"docs con ≥1 extracción: {hit} ({100*hit/max(with_text,1):.1f}% de los con texto)\n")
    print(f"{'ROL':<22}{'docs':>8}{'%docs':>8}{'entidades':>11}")
    for role in PAT:
        d=role_docs[role]; e=role_ents[role]
        print(f"{role:<22}{d:>8}{100*d/max(with_text,1):>7.1f}%{e:>11}")
    print("\n----- ejemplos -----")
    for role in PAT:
        if examples[role]:
            print(f"\n[{role}]")
            for comp,names in examples[role][:5]:
                print(f"  ({comp}) {' | '.join(names)}")
    if con: con.close(); print(f"\n→ guardado en {a.out}")

if __name__=="__main__":
    main()
