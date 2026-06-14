"""Tests de unidad del extractor de citas normativas (siempre corren, sin DB).
Blindan los modos de error que encontramos: truncamiento de nombres de código,
parsing de listas de artículos, tipos de cuerpo (ley/DL/DFL/CPR/código)."""


def _tipos(extractor, texto):
    return {(t, art, cuerpo) for t, art, cuerpo, _raw in extractor.extract(texto)}


def test_articulo_codigo_simple(extractor):
    res = _tipos(extractor, "Que conforme al artículo 1545 del Código Civil los contratos obligan.")
    assert any(t == "art_codigo" and art == "1545" and "Civil" in cuerpo for t, art, cuerpo in res)


def test_codigo_no_se_trunca(extractor):
    """El bug raíz: 'Código de Procedimiento Civil' se cortaba en 'Procedimiento'."""
    for nombre in ("Código de Procedimiento Civil", "Código de Procedimiento Penal",
                   "Código Procesal Penal", "Código Orgánico de Tribunales"):
        res = _tipos(extractor, f"según el {nombre} vigente")
        cuerpos = [c for _, _, c in res]
        assert any(nombre.split()[-1].lower() in c.lower() for c in cuerpos), \
            f"nombre truncado para «{nombre}»: {cuerpos}"


def test_lista_de_articulos(extractor):
    res = _tipos(extractor, "los artículos 1, 7 y 8 del Código del Trabajo")
    arts = {art for t, art, _ in res if t == "art_codigo"}
    assert {"1", "7", "8"} <= arts, f"lista mal parseada: {arts}"


def test_ley_numerada(extractor):
    res = _tipos(extractor, "la ley N° 19.496 sobre protección al consumidor")
    assert any(t == "ley" and "19.496" in cuerpo for t, _, cuerpo in res)


def test_constitucion(extractor):
    res = _tipos(extractor, "el artículo 19 N° 3 de la Constitución Política de la República")
    assert any(t == "art_cpr" for t, _, _ in res)


def test_decreto_ley(extractor):
    res = _tipos(extractor, "el artículo 62 del D.L. 3.500 sobre pensiones")
    assert any(t in ("art_dl", "dl") and "3.500" in cuerpo for t, _, cuerpo in res)


def test_bis_ter_transitorio(extractor):
    res = _tipos(extractor, "el artículo 196 ter de la ley 18.290 y el 4° transitorio")
    arts = {art for _, art, _ in res}
    assert any("196" in a for a in arts)
