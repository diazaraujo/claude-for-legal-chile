#!/usr/bin/env python3
"""Auditoría de PRECISIÓN de la extracción/resolución de citas normativas.

No hay ground truth manual de 4,4M citas → medimos consistencia interna verificable,
que acota la precisión real. Sobre muestra estratificada por tipo_cita valida:
  A. parsing: el artículo extraído aparece textualmente en el raw.
  B. resolución: el cuerpo citado es coherente con el título de la norma resuelta
     (nº de ley/DL/DFL coincide; nombre de código aparece en el título).
  C. completitud: nombre de código no truncado ("Código de Procedimiento" sin Civil/Penal).
Reporta precisión por categoría + ejemplos de cada modo de error. Honesto: esto mide
consistencia, no verdad jurídica; las inconsistentes SON errores, las consistentes
son casi-seguro correctas (cota inferior de precisión).
"""
import re, sqlite3, unicodedata, collections, random
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
DB = ROOT / "data/_index/citas_normativas.sqlite3"
N_POR_TIPO = 400


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


def main():
    con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)
    titulos = {r[0]: (norm(r[1]), r[2] or "", norm(r[3] or "")) for r in con.execute(
        "SELECT id_norma, tipo, numero, titulo FROM normas_titulos")}

    tipos = [r[0] for r in con.execute("SELECT DISTINCT tipo_cita FROM citas WHERE id_norma IS NOT NULL")]
    rng = random.Random(42)
    stats = collections.defaultdict(lambda: {"n": 0, "okA": 0, "okB": 0, "trunc": 0})
    errores = collections.defaultdict(list)

    RX_COD_TRUNC = re.compile(r"CODIGO DE (PROCEDIMIENTO|JUSTICIA)$")

    for tc in tipos:
        rows = con.execute(
            "SELECT articulo, cuerpo, raw, id_norma FROM citas "
            "WHERE id_norma IS NOT NULL AND tipo_cita=? ORDER BY RANDOM() LIMIT ?",
            (tc, N_POR_TIPO)).fetchall()
        for art, cuerpo, raw, idn in rows:
            st = stats[tc]; st["n"] += 1
            rawn = norm(raw)
            _tipo, numero, tit_norm = titulos.get(idn, ("", "", ""))
            # A. parsing: artículo aparece en raw
            okA = (not art) or (norm(art).split()[0] in rawn if art else True)
            if okA: st["okA"] += 1
            elif len(errores[f"{tc}:parsing"]) < 4:
                errores[f"{tc}:parsing"].append(f"art={art!r} raw={raw!r}")
            # B. resolución coherente con título
            cn = norm(cuerpo)
            if tc in ("ley", "art_ley", "dl", "art_dl", "dfl", "art_dfl"):
                num_cita = cn.replace(".", "").lstrip("0")
                okB = num_cita == (numero or "").lstrip("0")
            elif tc in ("codigo", "art_codigo"):
                base = re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", cn).strip()
                okB = base and base in re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", tit_norm)
            else:  # cpr/art_cpr
                okB = "CONSTITUCION POLITICA" in tit_norm
            if okB: st["okB"] += 1
            elif len(errores[f"{tc}:resolucion"]) < 4:
                errores[f"{tc}:resolucion"].append(f"cuerpo={cuerpo!r} → id={idn} «{titulos.get(idn,('','',''))[2][:55]}»")
            # C. truncamiento de código
            if RX_COD_TRUNC.search(cn):
                st["trunc"] += 1

    print(f"{'tipo_cita':14} {'n':>5} {'parsing%':>9} {'resoluc%':>9} {'trunc':>6}")
    print("-" * 50)
    tot = collections.Counter()
    for tc, st in sorted(stats.items(), key=lambda x: -x[1]["n"]):
        n = st["n"]
        print(f"{tc:14} {n:>5} {st['okA']*100//n:>8}% {st['okB']*100//n:>8}% {st['trunc']:>6}")
        tot["n"] += n; tot["okA"] += st["okA"]; tot["okB"] += st["okB"]; tot["trunc"] += st["trunc"]
    print("-" * 50)
    print(f"{'TOTAL':14} {tot['n']:>5} {tot['okA']*100//tot['n']:>8}% {tot['okB']*100//tot['n']:>8}% {tot['trunc']:>6}")
    print(f"\nPrecisión global estimada (parsing ∧ resolución coherentes): "
          f"~{min(tot['okA'], tot['okB'])*100//tot['n']}-{tot['okB']*100//tot['n']}%")
    print("\n=== ejemplos de error (modos detectados) ===")
    for k, exs in sorted(errores.items()):
        if exs:
            print(f"\n[{k}]")
            for e in exs[:3]:
                print(f"  {e}")


if __name__ == "__main__":
    main()
