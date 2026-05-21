#!/usr/bin/env python3
# std:input chile/normativa/catalogo/{tipo}/*.md
# std:output deletes losers (by --apply)
# std:deps stdlib pura
"""
Dedupe del catálogo por `bcn_uri`.

Algoritmo:
1. Para cada bcn_uri con >1 archivo: pick winner.
2. Winner = max(capa, then min(len(filename))).
3. Borra los loser sólo si --apply, o sólo reporta en dry-run.

Razón: el SPARQL scrape generó archivos con slugs largos
(`ley_ministerio-X_YYYY-MM-DD_N.md`), mientras que el REST scrape
inicial usó slugs cortos (`NNNNN.md`). Los slugs cortos suelen ser
capa 2 (estructural enriquecido). Mantenemos el más rico.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"

BCN_URI_RE = re.compile(r"^bcn_uri: (.+)$", re.MULTILINE)
CAPA_RE = re.compile(r"^capa: (\d+)$", re.MULTILINE)
VERSION_RE = re.compile(r"/es@\d{4}-\d{2}-\d{2}$")


def canonical_uri(uri: str) -> str:
    """Canonicaliza URI para comparación: sin alias /es@ + normaliza _/-."""
    uri = VERSION_RE.sub("", uri)
    return uri.replace("_", "-")


def file_score(f: Path) -> tuple[int, int]:
    """Higher tuple wins."""
    text = f.read_text(encoding="utf-8", errors="replace")
    m = CAPA_RE.search(text)
    capa = int(m.group(1)) if m else 1
    # Mayor capa = mejor; nombre corto = mejor (negar len)
    return (capa, -len(f.name))


def main() -> int:
    parser = argparse.ArgumentParser(description="Dedupe catálogo por bcn_uri")
    parser.add_argument("--apply", action="store_true", help="Borra losers")
    args = parser.parse_args()

    by_uri: dict[str, list[Path]] = defaultdict(list)
    total = 0
    for f in CATALOG_ROOT.rglob("*.md"):
        total += 1
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = BCN_URI_RE.search(text)
        if m:
            by_uri[canonical_uri(m.group(1))].append(f)

    dups = {uri: files for uri, files in by_uri.items() if len(files) > 1}
    losers: list[tuple[Path, Path]] = []
    for uri, files in dups.items():
        files_sorted = sorted(files, key=file_score, reverse=True)
        winner = files_sorted[0]
        for loser in files_sorted[1:]:
            losers.append((loser, winner))

    print(f"Total archivos:                  {total}")
    print(f"URIs con duplicados:             {len(dups)}")
    print(f"Loser files a borrar:            {len(losers)}")
    print()
    print("Muestra (10):")
    for loser, winner in losers[:10]:
        print(f"  DROP {loser.name}")
        print(f"  KEEP {winner.name}")
        print()

    if args.apply:
        for loser, _ in losers:
            loser.unlink()
        print(f"\n[APPLIED] {len(losers)} archivos borrados.")
    else:
        print("\nDry-run. Usar --apply para borrar.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
