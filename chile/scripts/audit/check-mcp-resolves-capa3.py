#!/usr/bin/env python3
# std:input chile/normativa/leyes/*.md + codigos/*.md + decretos/*.md (capa 3)
# std:output stdout report
# std:deps stdlib pura (sqlite3)
"""
Verifica que cada perfil capa 3 sea resoluble via LocalCatalog del MCP.

Para cada .md capa 3:
1. Extrae slug, tipo, numero, leychile_code del frontmatter.
2. Prueba lookup por slug, leychile_code y (tipo, numero).
3. Reporta qué falla y por qué.

Es un smoke test del MCP contra el corpus real. Útil después de
re-indexar o agregar nuevos perfiles.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "chile/scripts/mcp/src"))

from mcp_bcn_leychile.local_catalog import LocalCatalog  # noqa: E402

CAPA3_DIRS = [
    REPO_ROOT / "chile/normativa/leyes",
    REPO_ROOT / "chile/normativa/codigos",
    REPO_ROOT / "chile/normativa/decretos",
]


def parse_fm(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm: dict[str, str] = {}
    for line in text[4:end].split("\n"):
        if not line or line.startswith("  ") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip('"')
        fm[k.strip()] = v
    return fm


LEYCHILE_RE = re.compile(r"idNorma=(\d+)")
SLUG_NUM_RE = re.compile(r"^(?:ley|dl|dfl|ds|aa|tra|acd)-(\d+)")


def main() -> int:
    cat = LocalCatalog()
    if not cat.available:
        print(f"[FATAL] SQLite no existe en {cat.db_path}")
        return 1
    print(f"[INFO] SQLite: {cat.db_path}")
    stats = cat.stats()
    print(f"  Total normas: {stats['total_normas']:,}")

    files: list[Path] = []
    for d in CAPA3_DIRS:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    print(f"\n[INFO] Verificando {len(files)} perfiles capa 3\n")

    ok_slug = 0
    ok_leychile = 0
    ok_numero = 0
    fail = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        fm = parse_fm(text)
        slug = fm.get("slug") or f.stem

        # Extract leychile_code from fuente_oficial if not explicit
        leychile = fm.get("leychile_code")
        if not leychile and (fuente := fm.get("fuente_oficial")):
            m = LEYCHILE_RE.search(fuente)
            if m:
                leychile = m.group(1)

        # Extract numero from slug
        numero = fm.get("numero")
        if not numero:
            m = SLUG_NUM_RE.match(slug)
            if m:
                numero = m.group(1)

        # Resolve tipo from slug prefix
        tipo = "ley"
        if slug.startswith("dl-"):
            tipo = "dl"
        elif slug.startswith("dfl-"):
            tipo = "dfl"
        elif slug.startswith("codigo-") or slug.startswith("cod-"):
            tipo = "cod"

        # Test lookup_by_slug
        r1 = cat.lookup_by_slug(slug)
        if r1:
            ok_slug += 1
        # Test lookup_by_leychile_code
        r2 = cat.lookup_by_leychile_code(leychile) if leychile else None
        if r2:
            ok_leychile += 1
        # Test lookup_by_numero
        r3 = cat.lookup_by_numero(tipo, numero) if numero else None
        if r3:
            ok_numero += 1

        if not (r1 or r2 or r3):
            fail.append((slug, leychile, numero, tipo))

    print(f"[OK]  por slug:          {ok_slug:>4}/{len(files)}")
    print(f"[OK]  por leychile_code: {ok_leychile:>4}/{len(files)}")
    print(f"[OK]  por (tipo,numero): {ok_numero:>4}/{len(files)}")
    print(f"\n[FAIL] {len(fail)} perfiles no resuelven por NINGÚN método:")
    for slug, lc, num, tipo in fail[:20]:
        print(f"  {slug}  (leychile={lc}, num={num}, tipo={tipo})")
    if len(fail) > 20:
        print(f"  ... {len(fail) - 20} más")

    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
