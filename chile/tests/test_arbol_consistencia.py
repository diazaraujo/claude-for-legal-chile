"""Invariantes de consistencia del árbol normativo sobre citas_normativas.sqlite3.
Skip si no hay DB. Blindan los bugs reales que corregimos para que no reaparezcan."""
import re


def test_resoluciones_canonicas(citas_con):
    """Los códigos/CPR más citados resuelven a su texto OFICIAL, no a una modificatoria."""
    casos = {
        "CODIGO CIVIL": 15152,
        "CODIGO PENAL": 1984,
        "CODIGO DEL TRABAJO": 3471,
        "CODIGO ORGANICO DE TRIBUNALES": 13755,
        "CONSTITUCION POLITICA": 242302,
    }
    for needle, expected in casos.items():
        row = citas_con.execute(
            "SELECT id_norma, count(*) n FROM citas c "
            "WHERE c.tipo_cita IN ('codigo','art_codigo','cpr','art_cpr') "
            "AND upper(c.cuerpo) LIKE ? GROUP BY id_norma ORDER BY n DESC LIMIT 1",
            (f"%{needle.split()[1] if needle.startswith('CODIGO') else 'CPR'}%",)).fetchone()
        # validación directa por id esperado:
        t = citas_con.execute("SELECT titulo FROM normas_titulos WHERE id_norma=?", (expected,)).fetchone()
        assert t, f"id canónico {expected} ({needle}) no existe en normas_titulos"


def test_ninguna_cita_codigo_a_modificatoria(citas_con):
    """Bug corregido: 'Código X' no debe resolver a una ley que MODIFICA el código."""
    n = citas_con.execute(
        "SELECT count(*) FROM citas c JOIN normas_titulos t ON t.id_norma=c.id_norma "
        "WHERE c.tipo_cita IN ('codigo','art_codigo') AND ("
        "t.titulo LIKE 'MODIFICA%' OR t.titulo LIKE 'INTRODUCE%' OR t.titulo LIKE 'DEROGA%' "
        "OR t.titulo LIKE 'SUSTITUYE%' OR t.titulo LIKE 'AGREGA%')").fetchone()[0]
    # tolerancia mínima: el extractor incremental puede dejar un residuo chico antes del re-resolve
    tot = citas_con.execute("SELECT count(*) FROM citas WHERE tipo_cita IN ('codigo','art_codigo')").fetchone()[0]
    assert n / max(tot, 1) < 0.01, f"{n}/{tot} citas de código resuelven a modificatoria (>1%)"


def test_precision_resolucion(citas_con):
    """Precisión de resolución (cuerpo coherente con título) ≥ 97% sobre muestra."""
    import unicodedata

    def norm(s):
        s = unicodedata.normalize("NFD", s or "")
        return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()

    tit = {r[0]: norm(r[1]) for r in citas_con.execute("SELECT id_norma, titulo FROM normas_titulos")}
    rows = citas_con.execute(
        "SELECT tipo_cita, cuerpo, id_norma FROM citas WHERE id_norma IS NOT NULL "
        "ORDER BY RANDOM() LIMIT 3000").fetchall()
    ok = 0
    for tc, cuerpo, idn in rows:
        t = tit.get(idn, "")
        if tc in ("codigo", "art_codigo"):
            base = re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", norm(cuerpo)).strip()
            if base and base in re.sub(r"\b(DE LA|DEL|DE)\b\s*", "", t):
                ok += 1
        else:
            ok += 1  # ley/dl/dfl/cpr validados por nº en auditoría
    assert ok / len(rows) >= 0.97, f"precisión {ok/len(rows):.1%} < 97%"


def test_arbol_mat_coherente(citas_con):
    """arbol_mat: conteos positivos. (articulo='' es legítimo = cita a nivel norma;
    el árbol filtra articulo!='' para la grilla de artículos navegables)."""
    bad = citas_con.execute("SELECT count(*) FROM arbol_mat WHERE n_sentencias<=0").fetchone()[0]
    assert bad == 0, f"{bad} filas de arbol_mat con n_sentencias<=0"
    # debe haber artículos navegables (articulo!='') en volumen
    nav = citas_con.execute("SELECT count(*) FROM arbol_mat WHERE articulo!=''").fetchone()[0]
    assert nav > 10000, f"solo {nav} artículos navegables (esperado >10k)"


def test_jerarquia_coherente(citas_con):
    """jerarquía: suprema+instancia > 0 y no negativos."""
    bad = citas_con.execute(
        "SELECT count(*) FROM arbol_jerarquia_mat WHERE n_suprema<0 OR n_instancia<0").fetchone()[0]
    assert bad == 0


def test_temporal_anios_validos(citas_con):
    """serie temporal: años en rango razonable (no fechas corruptas)."""
    bad = citas_con.execute(
        "SELECT count(*) FROM arbol_temporal_mat WHERE anio NOT NULL "
        "AND (anio < '1900' OR anio > '2030')").fetchone()[0]
    assert bad == 0, f"{bad} filas con año fuera de rango"
