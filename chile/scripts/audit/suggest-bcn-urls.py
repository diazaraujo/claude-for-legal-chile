#!/usr/bin/env python3
# std:input chile/normativa/leyes/, chile/normativa/decretos/, chile/normativa/codigos/
# std:output reporte de correcciones sugeridas
# std:deps stdlib pura + catálogo capa 1
"""
Sugiere correcciones de URLs BCN cruzando con el catálogo capa 1.

Estrategia:
1. Para cada perfil capa 3 que tenga discrepancia detectada por
   check-bcn-urls.py, extraer el número de norma declarado.
2. Buscar en chile/normativa/catalogo/<tipo>/NNNNN.md el archivo
   correspondiente.
3. Si existe, extraer `leychile_code:` del frontmatter → ese es el ID
   correcto.
4. Generar reporte de cambios sugeridos.

Si el catálogo capa 1 no tiene la norma (gap del scrape), reportar
como pendiente de verificación manual.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

CAPA3_DIRS = {
    "leyes": REPO_ROOT / "chile/normativa/leyes",
    "codigos": REPO_ROOT / "chile/normativa/codigos",
    "constitucion": REPO_ROOT / "chile/normativa/constitucion",
    "decretos": REPO_ROOT / "chile/normativa/decretos",
}

CATALOG_DIRS = {
    "ley": REPO_ROOT / "chile/normativa/catalogo/ley",
    "dl": REPO_ROOT / "chile/normativa/catalogo/dl",
    "dfl": REPO_ROOT / "chile/normativa/catalogo/dfl",
    "cod": REPO_ROOT / "chile/normativa/catalogo/cod",
}

SLUG_RE = re.compile(r"^(ley|dl|dfl|ds|cod)-(\d+)")


def parse_fm(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}
    raw = content[4:end]
    fields = {}
    for line in raw.split("\n"):
        if ":" not in line or line.startswith("  "):
            continue
        k, _, v = line.partition(":")
        if v.strip():
            fields[k.strip()] = v.strip()
    return fields


def get_id_from_url(url: str) -> str | None:
    m = re.search(r"idNorma=(\d+)", url)
    return m.group(1) if m else None


def find_in_catalog(tipo: str, numero: str) -> tuple[str | None, str | None]:
    """Devuelve (leychile_code, titulo) del catálogo o (None, None)."""
    candidates = []
    if tipo == "ley":
        candidates = [
            CATALOG_DIRS["ley"] / f"{int(numero):05d}.md",
            CATALOG_DIRS["ley"] / f"{numero}.md",
        ]
    elif tipo == "dl":
        candidates = [
            CATALOG_DIRS["dl"] / f"{int(numero):05d}.md",
            CATALOG_DIRS["dl"] / f"{numero}.md",
        ]
    elif tipo == "dfl":
        # DFL puede tener formato distinto en el catálogo (incluye fecha)
        candidates = list(CATALOG_DIRS["dfl"].glob(f"{int(numero):05d}-*.md")) if CATALOG_DIRS["dfl"].exists() else []
    elif tipo == "cod":
        candidates = list(CATALOG_DIRS["cod"].glob("*.md")) if CATALOG_DIRS["cod"].exists() else []

    for c in candidates:
        if c.exists():
            fm = parse_fm(c.read_text(encoding="utf-8"))
            code = fm.get("leychile_code")
            titulo = fm.get("titulo_oficial", "").strip('"')
            if code:
                return code, titulo
    return None, None


def main() -> int:
    files = []
    for d in CAPA3_DIRS.values():
        if d.exists():
            files.extend(sorted(d.glob("*.md")))

    files = [f for f in files if not f.stem.startswith("00-")]
    print(f"[INFO] {len(files)} perfiles capa 3 a procesar")

    sugerencias = []
    sin_catalogo = []

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        m = SLUG_RE.match(f.stem)
        if not m:
            continue
        tipo = m.group(1)
        numero = m.group(2)

        # Mapear tipo del slug al tipo del catálogo
        catalog_tipo = {"ley": "ley", "dl": "dl", "dfl": "dfl", "ds": None, "cod": "cod"}.get(tipo)
        if catalog_tipo is None:
            sin_catalogo.append((rel, tipo, numero, "tipo sin catálogo (ds)"))
            continue

        code, titulo_catalog = find_in_catalog(catalog_tipo, numero)
        if not code:
            sin_catalogo.append((rel, tipo, numero, "no encontrado en catálogo capa 1"))
            continue

        fm = parse_fm(f.read_text(encoding="utf-8"))
        url_actual = fm.get("fuente_oficial", "")
        id_actual = get_id_from_url(url_actual)

        if id_actual == code:
            continue  # OK

        sugerencias.append({
            "archivo": rel,
            "tipo": tipo,
            "numero": numero,
            "id_actual": id_actual,
            "id_sugerido": code,
            "titulo_catalog": titulo_catalog,
        })

    print(f"\n[SUGGEST] {len(sugerencias)} URLs con cambio sugerido (catálogo capa 1):")
    for s in sugerencias:
        print(f"  {s['archivo']}")
        print(f"    {s['tipo']} {s['numero']}: id_actual={s['id_actual']} → id_sugerido={s['id_sugerido']}")
        print(f"    titulo catálogo: {s['titulo_catalog'][:80]}")

    print(f"\n[PENDIENTE-MANUAL] {len(sin_catalogo)} archivos sin match en catálogo:")
    for rel, tipo, numero, razon in sin_catalogo[:30]:
        print(f"  {rel}: {razon}")
    if len(sin_catalogo) > 30:
        print(f"  ... y {len(sin_catalogo)-30} más")

    return 0 if not sugerencias else 0  # informativo, no falla


if __name__ == "__main__":
    sys.exit(main())
