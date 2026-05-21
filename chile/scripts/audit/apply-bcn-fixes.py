#!/usr/bin/env python3
# std:input chile/normativa/leyes/, chile/normativa/codigos/, etc.
# std:output reporte de cambios aplicados; modifica archivos in place
# std:deps stdlib pura + catálogo capa 1
"""
Aplica correcciones de URL BCN derivadas del catálogo capa 1.

A diferencia de suggest-bcn-urls.py, este script SÍ modifica los
archivos. Aplica el cambio solo cuando:

1. El slug del perfil capa 3 matchea unívocamente un archivo del
   catálogo capa 1 (mismo número, mismo tipo).
2. El título del catálogo coincide al menos en una palabra clave
   con el título declarado en el perfil.

Si el match es ambiguo (ej. dfl-2-1998 vs dfl-2-2009 ambos buscan
dfl/2.md) → no aplica.

Reporte por stdout. Modifica archivos in-place.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SLUG_RE = re.compile(r"^(ley|dl|dfl|cod)-(\d+)(?:-(\d+))?")

STOPWORDS = {
    "ley", "la", "el", "de", "del", "los", "las", "que", "por", "sobre",
    "modifica", "establece", "regula", "fija", "diversos", "que",
    "cuerpos", "legales", "para", "se", "y", "a", "en", "un", "una",
    "al", "como", "su", "sus", "es", "no", "lo", "este", "esta",
    "codigo", "decreto", "norma", "art", "n", "del",
}


def _tokens(s: str) -> set[str]:
    s = s.lower()
    repl = str.maketrans("áéíóúñü", "aeiounu")
    s = s.translate(repl)
    return {w for w in re.findall(r"[a-z]+", s) if len(w) >= 4 and w not in STOPWORDS}


def titulo_match(local: str, catalog: str) -> bool:
    a = _tokens(local)
    b = _tokens(catalog)
    if not a:
        return True
    return len(a & b) >= 1


def parse_fm(content: str) -> tuple[dict[str, str], int]:
    """Devuelve (campos, índice donde termina el frontmatter)."""
    if not content.startswith("---\n"):
        return {}, 0
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, 0
    raw = content[4:end]
    fields = {}
    for line in raw.split("\n"):
        if ":" not in line or line.startswith("  "):
            continue
        k, _, v = line.partition(":")
        if v.strip():
            fields[k.strip()] = v.strip()
    return fields, end + 5  # end of '\n---\n'


def find_catalog_file(tipo: str, numero: str, year: str | None) -> Path | None:
    catalog_dir = REPO_ROOT / f"chile/normativa/catalogo/{tipo}"
    if not catalog_dir.exists():
        return None

    if tipo in ("ley", "dl"):
        # Formato: NNNNN.md con padding
        cand = catalog_dir / f"{int(numero):05d}.md"
        if cand.exists():
            return cand
        cand = catalog_dir / f"{numero}.md"
        if cand.exists():
            return cand
        return None

    if tipo == "dfl":
        # DFL incluye año en el nombre: NNNNN-AAAA-...md
        matches = list(catalog_dir.glob(f"{int(numero):05d}-*.md"))
        if year and len(matches) > 1:
            year_matches = [m for m in matches if year in m.stem]
            if year_matches:
                return year_matches[0]
            # Ambiguo
            return None
        if len(matches) == 1:
            return matches[0]
        return None

    if tipo == "cod":
        # Códigos: por nombre único
        return None  # no soportado por slug numérico

    return None


def main() -> int:
    capa3_dirs = [
        REPO_ROOT / "chile/normativa/leyes",
        REPO_ROOT / "chile/normativa/codigos",
        REPO_ROOT / "chile/normativa/constitucion",
        REPO_ROOT / "chile/normativa/decretos",
    ]
    files = []
    for d in capa3_dirs:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    files = [f for f in files if not f.stem.startswith("00-")]

    applied = []
    skipped = []
    for f in files:
        m = SLUG_RE.match(f.stem)
        if not m:
            continue
        tipo = m.group(1)
        numero = m.group(2)
        year = m.group(3)  # solo dfl puede tenerlo

        if tipo == "ds":
            skipped.append((f, "tipo DS sin catálogo"))
            continue

        catalog_file = find_catalog_file(tipo, numero, year)
        if not catalog_file:
            skipped.append((f, "sin match en catálogo"))
            continue

        cat_content = catalog_file.read_text(encoding="utf-8")
        cat_fm, _ = parse_fm(cat_content)
        code = cat_fm.get("leychile_code")
        cat_titulo = cat_fm.get("titulo_oficial", "").strip('"')
        if not code:
            skipped.append((f, "catálogo sin leychile_code"))
            continue

        content = f.read_text(encoding="utf-8")
        fm, fm_end = parse_fm(content)
        url_actual = fm.get("fuente_oficial", "")
        m_url = re.search(r"idNorma=(\d+)", url_actual)
        id_actual = m_url.group(1) if m_url else None

        if id_actual == code:
            continue  # Ya OK

        titulo_perfil = fm.get("titulo_oficial", "").strip('"')
        if not titulo_match(titulo_perfil, cat_titulo):
            skipped.append((f, f"título no matchea catálogo: '{cat_titulo[:50]}'"))
            continue

        # Aplicar el cambio
        new_url = f"https://www.bcn.cl/leychile/navegar?idNorma={code}"
        new_content = re.sub(
            r"^fuente_oficial:.*$",
            f"fuente_oficial: {new_url}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        f.write_text(new_content, encoding="utf-8")

        applied.append({
            "archivo": f.relative_to(REPO_ROOT),
            "id_antes": id_actual,
            "id_despues": code,
            "titulo_catalog": cat_titulo[:70],
        })

    print(f"\n[APPLIED] {len(applied)} URLs corregidas:")
    for a in applied:
        print(f"  {a['archivo']}: {a['id_antes']} → {a['id_despues']}")
        print(f"    catálogo: {a['titulo_catalog']}")

    print(f"\n[SKIPPED] {len(skipped)} archivos:")
    razones = {}
    for f, r in skipped:
        razones[r] = razones.get(r, 0) + 1
    for r, c in razones.items():
        print(f"  {c}× {r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
