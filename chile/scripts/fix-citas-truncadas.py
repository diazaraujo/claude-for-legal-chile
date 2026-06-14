#!/usr/bin/env python3
"""Corrige las citas de código con nombre TRUNCADO leyendo el texto del considerando.
El regex viejo cortaba en palabras sin conector ("Código de Procedimiento"→sin Civil/Penal).
Para cada cita truncada: relee el considerando, recupera el nombre completo con el matcher
canónico, re-resuelve al texto oficial del código. Preserva todos los fixes previos.
"""
import re, sqlite3, unicodedata
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
DB = ROOT / "data/_index/citas_normativas.sqlite3"
CORPUS = ROOT / "data/_index/corpus.fts.sqlite3"

_COD_NOMBRES = [
    r"de\s+Procedimiento\s+Civil", r"de\s+Procedimiento\s+Penal", r"de\s+Justicia\s+Militar",
    r"Org[áa]nico\s+de\s+Tribunales", r"de\s+Derecho\s+Internacional\s+Privado",
    r"Procesal\s+Penal", r"Procesal\s+Civil", r"de\s+Aguas", r"de\s+Miner[íi]a",
    r"de\s+Minas", r"de\s+Comercio", r"de\s+Bustamante", r"del\s+Trabajo",
    r"Tributario", r"Sanitario", r"Aeron[áa]utico", r"Aduanero", r"Penal", r"Civil",
]
RX_COD = re.compile(r"C[óo]digo\s+(?:" + "|".join(_COD_NOMBRES) + r")", re.I)
RX_TRUNC = re.compile(r"(PROCEDIMIENTO|JUSTICIA|ORGANICO)$")


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


def main():
    con = sqlite3.connect(str(DB), timeout=120)
    # mapa código canónico → id texto oficial (excluye modificatorias)
    RXmod = re.compile(r"^(MODIFICA|INTRODUCE|DEROGA|SUSTITUYE|AGREGA|REEMPLAZA|INTERPRETA)")
    RXcod = re.compile(r"\bCODIGO\s+(DE\s+|DEL\s+|DE\s+LA\s+)?([A-Z][A-Z ]+?)(?:\s*[,.(]|$)")
    oficial = {}
    for idn, tipo, titulo, derog in con.execute("SELECT id_norma,tipo,titulo,derogado FROM normas_titulos"):
        t = norm(titulo)
        if RXmod.match(t):
            continue
        m = re.search(r"(?:FIJA(?:SE)?\s+(?:EL\s+)?TEXTO[A-Z ,]*DEL?\s+|APRUEBA\s+(?:EL\s+|TEXTO[A-Z ,]*DEL?\s+)?)?(CODIGO\s+.+)", t)
        if not m or "CODIGO" not in t[:90]:
            continue
        mm = RXcod.search(m.group(1))
        if not mm:
            continue
        name = re.sub(r"\s+", " ", ("CODIGO " + (mm.group(1) or "") + mm.group(2)).strip())
        base = re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", name)
        if base not in oficial or (derog == "no derogado"):
            oficial[base] = idn

    def resolve(nombre):
        base = re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", norm(nombre)).strip()
        return oficial.get(base)

    cor = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True, timeout=120)
    # citas truncadas: cuerpo termina en palabra ambigua
    trunc = con.execute(
        "SELECT rowid, chunk_rowid, cuerpo, articulo FROM citas "
        "WHERE tipo_cita IN ('codigo','art_codigo') AND id_norma IS NOT NULL "
        "AND (cuerpo LIKE '%Procedimiento' OR cuerpo LIKE '%Justicia' OR cuerpo LIKE '%Orgánico')").fetchall()
    print(f"citas truncadas candidatas: {len(trunc)}", flush=True)

    fixed = 0; nochange = 0
    cache = {}
    for cid, chunk, cuerpo, art in trunc:
        if not RX_TRUNC.search(norm(cuerpo)):
            continue
        if chunk not in cache:
            row = cor.execute("SELECT content FROM considerandos_chunks WHERE rowid=?", (chunk,)).fetchone()
            cache[chunk] = (row[0] if row else "")
        txt = cache[chunk]
        # buscar el nombre completo de código en el texto (cerca de la cita)
        m = RX_COD.search(txt)
        if not m:
            nochange += 1; continue
        full = re.sub(r"\s+", " ", m.group(0)).strip()
        if norm(full) == norm("Código " + cuerpo) or norm(full).endswith(norm(cuerpo)):
            idn = resolve(full.replace("Código", "").replace("código", "").strip())
            if idn:
                con.execute("UPDATE citas SET cuerpo=?, id_norma=? WHERE rowid=?",
                            (full[7:].strip() if full.lower().startswith("código") else full, idn, cid))
                fixed += 1
        else:
            nochange += 1
        if (fixed + nochange) % 20000 == 0:
            con.commit(); print(f"  procesadas {fixed+nochange} · corregidas {fixed}", flush=True)
    con.commit()
    cor.close()
    print(f"[DONE] truncadas corregidas: {fixed} · sin cambio: {nochange}", flush=True)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")


if __name__ == "__main__":
    main()
