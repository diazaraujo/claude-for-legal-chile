#!/usr/bin/env python3
# std:input chile/normativa/index/catalogo.sqlite3
# std:output chile/normativa/leyes/ley-NNNNN-slug.md (borradores capa 3)
# std:deps stdlib pura
"""
Genera borradores capa 3 para las normas hub del grafo que NO tienen
perfil curado todavía.

Estrictamente desde datos verificables (catálogo BCN + grafo). NO
escribe contenido sustantivo (artículos, doctrina, casos) — eso queda
para abogado.

Marca cada borrador `estado_revision: borrador-no-validado`.

Conforme a [[feedback-no-inventar-ids-urls-referencias]].

Uso:
    python3 chile/scripts/audit/generar-borradores-capa3.py \
        --leyes 18290,18883,19806,19047 \
        [--apply]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DB = REPO_ROOT / "chile/normativa/index/catalogo.sqlite3"
OUTPUT_DIR = REPO_ROOT / "chile/normativa/leyes"


def slug_safe(s: str) -> str:
    """Slug ASCII de un nombre corto."""
    s = s.lower()
    s = s.translate(str.maketrans("áéíóúñü", "aeiounu"))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60]


def short_uri(uri: str) -> str:
    return uri.replace("http://datos.bcn.cl/recurso/cl/", "")


def make_borrador(
    cur: sqlite3.Cursor, tipo: str, numero: str, slug_hint: str | None
) -> tuple[Path, str] | None:
    # Lookup norma por (tipo, numero), preferir capa más alta
    row = cur.execute(
        "SELECT slug, titulo, publicacion, promulgacion, organismo, "
        "leychile_code, bcn_uri, capa FROM normas "
        "WHERE tipo = ? AND numero = ? ORDER BY capa DESC LIMIT 1",
        (tipo, numero),
    ).fetchone()
    if not row:
        return None
    cat_slug, titulo, pub, prom, org, leychile, uri, capa = row

    if capa == 3:
        print(f"  [SKIP] {tipo} {numero}: ya tiene capa 3 ({cat_slug})")
        return None

    # Slug del borrador
    short = slug_hint or slug_safe((titulo or "")[:50])
    slug = f"{tipo}-{numero}-{short}".strip("-")

    # Outgoing & incoming del grafo
    outgoing = cur.execute(
        "SELECT DISTINCT dst_uri FROM relaciones "
        "WHERE rel='modifiesTo' AND src_uri = ? AND dst_uri NOT LIKE '%/es@%' "
        "ORDER BY dst_uri LIMIT 25",
        (uri,),
    ).fetchall() if uri else []
    incoming = cur.execute(
        "SELECT DISTINCT src_uri FROM relaciones "
        "WHERE rel='modifiesTo' AND dst_uri = ? AND src_uri NOT LIKE '%/es@%' "
        "ORDER BY src_uri LIMIT 25",
        (uri,),
    ).fetchall() if uri else []

    titulo_safe = (titulo or "").replace('"', '\\"')

    fm = "---\n"
    fm += f"norma: {tipo.upper()} {numero}\n"
    fm += f"slug: {slug}\n"
    if titulo:
        fm += f'titulo_oficial: "{titulo_safe}"\n'
    if pub:
        fm += f"publicacion: {pub}\n"
    if prom:
        fm += f"promulgacion: {prom}\n"
    if org:
        fm += f"emisor: {org}\n"
    if leychile:
        fm += (
            f"leychile_code: {leychile}\n"
            f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={leychile}\n"
        )
    if uri:
        fm += f"bcn_uri: {uri}\n"
    fm += "vigencia: pendiente-verificar\n"
    fm += "capa: 3\n"
    fm += "materia:\n  - pendiente\n"
    fm += "relacionada_per:\n  - pendiente\n"
    fm += "estado_revision: borrador-generado-no-validado\n"
    fm += "validador: null\n"
    fm += "fecha_validacion: null\n"
    if outgoing or incoming:
        fm += "grafo_relaciones:\n"
        if outgoing:
            fm += "  modifica:\n"
            for (dst,) in outgoing:
                fm += f"    - {short_uri(dst)}\n"
        if incoming:
            fm += "  modificada_por:\n"
            for (src,) in incoming:
                fm += f"    - {short_uri(src)}\n"
    fm += "---\n\n"

    body = (
        f"# {tipo.upper()} {numero}"
        + (f" — {titulo}" if titulo else "")
        + "\n\n"
        "> ⚠️ **Borrador generado automáticamente. No validado por abogado.**\n"
        "> Los datos provienen del catálogo BCN y del grafo de relaciones.\n"
        "> El contenido sustantivo (análisis de artículos, doctrina, casos)\n"
        "> requiere curaduría legal antes de citarse como referencia.\n\n"
        "## Datos oficiales\n\n"
        f"- **Título completo:** {titulo or 'pendiente'}\n"
    )
    if pub:
        body += f"- **Publicación:** {pub}\n"
    if prom:
        body += f"- **Promulgación:** {prom}\n"
    if org:
        body += f"- **Organismo emisor:** {org}\n"
    if leychile:
        body += (
            f"- **Fuente oficial:** "
            f"[BCN/LeyChile idNorma={leychile}]"
            f"(https://www.bcn.cl/leychile/navegar?idNorma={leychile})\n"
        )

    if outgoing:
        body += "\n## Esta norma modifica (grafo BCN)\n\n"
        for (dst,) in outgoing:
            body += f"- `{short_uri(dst)}`\n"

    if incoming:
        body += "\n## Esta norma es modificada por (grafo BCN)\n\n"
        for (src,) in incoming:
            body += f"- `{short_uri(src)}`\n"

    body += (
        "\n## Pendientes de curaduría legal\n\n"
        "- [ ] Vigencia actual (cruzar con BCN)\n"
        "- [ ] Análisis sustantivo de artículos clave\n"
        "- [ ] Jurisprudencia relevante\n"
        "- [ ] Casos canónicos de aplicación\n"
        "- [ ] Cruce con perfiles `relacionada_per` manuales\n"
        "- [ ] Disclaimers operativos (plazos, alcance, sanciones)\n"
        "- [ ] Cambiar `estado_revision` a `validada` cuando revise abogado\n"
    )

    return OUTPUT_DIR / f"{slug}.md", fm + body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leyes", required=True,
                        help="Coma-separados: 18290,18883,...")
    parser.add_argument("--tipo", default="ley")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--slug-hints", default="",
                        help="key=val,... eg 18290=ley-transito")
    args = parser.parse_args()

    hints: dict[str, str] = {}
    for pair in args.slug_hints.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            hints[k.strip()] = v.strip()

    con = sqlite3.connect(str(DB))
    cur = con.cursor()

    generated = 0
    for numero in args.leyes.split(","):
        numero = numero.strip()
        if not numero:
            continue
        hint = hints.get(numero)
        result = make_borrador(cur, args.tipo, numero, hint)
        if not result:
            continue
        path, content = result
        if args.apply:
            path.write_text(content, encoding="utf-8")
            print(f"  [WRITE] {path.relative_to(REPO_ROOT)}")
        else:
            print(f"  [DRY-RUN] {path.relative_to(REPO_ROOT)} ({len(content)} chars)")
        generated += 1

    print(f"\n[DONE] {generated} borradores generados (apply={args.apply})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
