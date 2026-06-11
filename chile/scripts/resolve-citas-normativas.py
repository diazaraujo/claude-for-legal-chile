#!/usr/bin/env python3
"""Resuelve citas textuales → id_norma vía normas_titulos (sin inventar IDs).

- ley/art_ley:  numero (sin puntos) → normas_titulos tipo='Ley'
- dl, dfl:      numero → tipo 'Decreto Ley' / 'Decreto con Fuerza de Ley'
- codigo:       nombre → titulo LIKE 'CODIGO <X>%' o 'FIJA TEXTO%CODIGO <X>%'
                (prefiere vigente sobre derogado; ambigüedad → NULL + log)
- cpr:          titulo CONSTITUCION POLITICA (texto refundido vigente)

Crea: citas.id_norma (columna), vista arbol_normativo (norma×artículo×docs).
"""
import re, sqlite3, sys, unicodedata
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
DB = ROOT / "data/_index/citas_normativas.sqlite3"


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def main():
    conn = sqlite3.connect(str(DB), timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(citas)")]
    if "id_norma" not in cols:
        conn.execute("ALTER TABLE citas ADD COLUMN id_norma INTEGER")

    titulos = list(conn.execute(
        "SELECT id_norma, tipo, numero, titulo, derogado FROM normas_titulos"))

    by_tipo_num = {}
    for idn, tipo, numero, titulo, derog in titulos:
        key = (norm(tipo), (numero or "").lstrip("0"))
        # vigente pisa derogado; si empata, conserva el primero
        prev = by_tipo_num.get(key)
        if prev is None or (prev[1] != "no derogado" and derog == "no derogado"):
            by_tipo_num[key] = (idn, derog)

    # códigos y CPR: candidatos por título
    codigo_map, ambiguos = {}, {}
    rx_cod = re.compile(r"\bCODIGO\s+(DE\s+|DEL\s+|DE\s+LA\s+)?([A-Z][A-Z ]+?)(?:\s*[,.(]|$)")
    for idn, tipo, numero, titulo, derog in titulos:
        t = norm(titulo)
        m = re.search(r"(?:FIJA(?:SE)?\s+(?:EL\s+)?TEXTO[A-Z ,]*DEL?\s+)?(CODIGO\s+.+)", t)
        if not m or "CODIGO" not in t[:80]:
            continue
        mm = rx_cod.search(m.group(1))
        if not mm:
            continue
        name = ("CODIGO " + (mm.group(1) or "") + mm.group(2)).strip()
        name = re.sub(r"\s+", " ", name)
        prev = codigo_map.get(name)
        if prev is None or (prev[1] != "no derogado" and derog == "no derogado"):
            if prev and prev[1] == "no derogado" and derog == "no derogado" and prev[0] != idn:
                ambiguos.setdefault(name, {prev[0]}).add(idn)
            codigo_map[name] = (idn, derog)
    for name in ambiguos:
        print(f"  AMBIGUO (queda el de menor id, revisar): {name} → {sorted(ambiguos[name])}")

    cpr = [(i, d) for i, t, n, ti, d in
           [(r[0], r[1], r[2], r[3], r[4]) for r in titulos]
           if "CONSTITUCION POLITICA" in norm(ti)]
    cpr_vig = [i for i, d in cpr if d == "no derogado"]
    cpr_id = min(cpr_vig) if cpr_vig else (min(i for i, _ in cpr) if cpr else None)
    print(f"CPR resuelta a id_norma={cpr_id} (candidatas: {len(cpr)})")

    def resolve(tipo_cita, cuerpo):
        c = norm(cuerpo)
        if tipo_cita in ("ley", "art_ley"):
            hit = by_tipo_num.get(("LEY", c.replace(".", "").lstrip("0")))
            return hit[0] if hit else None
        if tipo_cita in ("dl", "art_dl"):
            hit = by_tipo_num.get(("DECRETO LEY", c.replace(".", "").lstrip("0")))
            return hit[0] if hit else None
        if tipo_cita in ("dfl", "art_dfl"):
            hit = by_tipo_num.get(("DECRETO CON FUERZA DE LEY", c.replace(".", "").lstrip("0")))
            return hit[0] if hit else None
        if tipo_cita in ("cpr", "art_cpr") or c.startswith("CPR"):
            return cpr_id
        if tipo_cita in ("codigo", "art_codigo"):
            c2 = re.sub(r"\s+", " ", c)
            hit = codigo_map.get(c2)
            if not hit:  # tolerar genitivos: CODIGO DEL TRABAJO vs CODIGO TRABAJO
                base = re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", c2)
                hit = next((v for k, v in codigo_map.items()
                            if re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", k) == base), None)
            return hit[0] if hit else None
        return None

    pares = list(conn.execute("SELECT DISTINCT tipo_cita, cuerpo FROM citas"))
    print(f"pares distintos (tipo,cuerpo): {len(pares)}")
    n_res = 0
    for tipo_cita, cuerpo in pares:
        idn = resolve(tipo_cita, cuerpo)
        if idn:
            conn.execute("UPDATE citas SET id_norma=? WHERE tipo_cita=? AND cuerpo=?",
                         (idn, tipo_cita, cuerpo))
            n_res += 1
    conn.commit()

    tot, res = conn.execute(
        "SELECT count(*), count(id_norma) FROM citas").fetchone()
    print(f"citas: {tot} · resueltas a id_norma: {res} ({res/tot*100:.1f}%) · pares resueltos: {n_res}/{len(pares)}")

    conn.execute("DROP VIEW IF EXISTS arbol_normativo")
    conn.execute(
        "CREATE VIEW arbol_normativo AS "
        "SELECT c.id_norma, t.titulo, c.articulo, "
        "count(DISTINCT c.doc_path) AS n_sentencias, count(*) AS n_citas "
        "FROM citas c JOIN normas_titulos t USING(id_norma) "
        "WHERE c.id_norma IS NOT NULL "
        "GROUP BY c.id_norma, c.articulo")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_citas_norma ON citas(id_norma, articulo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_citas_doc ON citas(doc_path)")
    conn.commit()
    print("[DONE] vista arbol_normativo + índices listos")


if __name__ == "__main__":
    sys.exit(main())
