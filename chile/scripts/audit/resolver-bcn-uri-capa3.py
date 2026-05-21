#!/usr/bin/env python3
# std:input chile/normativa/{leyes,codigos,decretos}/*.md (capa 3)
# std:output modifica frontmatter agregando bcn_uri
# std:deps stdlib pura
"""
Resuelve `bcn_uri` para perfiles capa 3 que solo tienen `leychile_code`
o lo derivan de `fuente_oficial`.

Estrategia:
1. SQLite catálogo: lookup por leychile_code (instantáneo).
2. SPARQL fallback: query `?n bcnnorms:leychileCode "CODE"` (red).

Resuelve UNA pasada: el bcn_uri queda en el frontmatter, lo cual
permite que el enriquecedor del grafo lo use sin más SPARQL.

Conforme a no-inventar: solo persiste URIs que BCN/SQLite confirman.

Uso:
    python3 chile/scripts/audit/resolver-bcn-uri-capa3.py [--apply] [--max-sparql N]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DB = REPO_ROOT / "chile/normativa/index/catalogo.sqlite3"
CAPA3_DIRS = [
    REPO_ROOT / "chile/normativa/leyes",
    REPO_ROOT / "chile/normativa/codigos",
    REPO_ROOT / "chile/normativa/decretos",
]

SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.7"
LEYCHILE_RE = re.compile(r"idNorma=(\d+)")


def parse_fm_full(text: str) -> tuple[str, str, str]:
    """Devuelve (fm_raw, fm_dict_str, body)."""
    if not text.startswith("---\n"):
        return "", "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", "", text
    return text[4:end], text[: end + 5], text[end + 5 :]


def parse_fm_dict(fm_raw: str) -> dict[str, str]:
    fm: dict[str, str] = {}
    for line in fm_raw.split("\n"):
        if not line or line.startswith("  ") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip('"')
        fm[k.strip()] = v
    return fm


def lookup_sqlite(con: sqlite3.Connection, code: str) -> str | None:
    row = con.execute(
        "SELECT bcn_uri FROM normas WHERE leychile_code = ? "
        "AND bcn_uri IS NOT NULL AND bcn_uri NOT LIKE '%/es@%' LIMIT 1",
        (code,),
    ).fetchone()
    return row[0] if row else None


def lookup_sparql(code: str, timeout: int = 30) -> str | None:
    """Busca URI canónica (sin alias /es@) por leychileCode con backoff 429."""
    query = f'''
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
SELECT DISTINCT ?n WHERE {{
  ?n bcnnorms:leychileCode ?c .
  FILTER (str(?c) = "{code}")
  FILTER (!REGEX(str(?n), "/es@"))
}} LIMIT 1
'''
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    backoff = 5
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
                rows = data.get("results", {}).get("bindings", [])
                return rows[0]["n"]["value"] if rows else None
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
        except (TimeoutError, OSError):
            time.sleep(backoff)
            backoff *= 2
            continue
    return None


def insert_bcn_uri(fm_dict_str: str, uri: str) -> str:
    """Inserta `bcn_uri: <uri>` después de fuente_oficial, o al final del fm."""
    if "bcn_uri:" in fm_dict_str:
        return fm_dict_str  # no-op
    # Insertar después de fuente_oficial si existe, sino antes del cierre ---
    if "fuente_oficial:" in fm_dict_str:
        return re.sub(
            r"(fuente_oficial:[^\n]*\n)",
            r"\1bcn_uri: " + uri + "\n",
            fm_dict_str,
            count=1,
        )
    return fm_dict_str.replace("---\n", f"bcn_uri: {uri}\n---\n", 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--max-sparql", type=int, default=200)
    parser.add_argument("--rate", type=float, default=1.0)
    args = parser.parse_args()

    if not DB.exists():
        print(f"[FATAL] SQLite no existe: {DB}")
        return 1

    con = sqlite3.connect(str(DB))
    files: list[Path] = []
    for d in CAPA3_DIRS:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))

    print(f"[INFO] Revisando {len(files)} perfiles capa 3")

    by_sqlite = 0
    by_sparql = 0
    no_code = 0
    not_found = 0
    already = 0
    sparql_attempts = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        fm_raw, fm_str, body = parse_fm_full(text)
        fm = parse_fm_dict(fm_raw)

        if "bcn_uri" in fm and fm["bcn_uri"]:
            already += 1
            continue

        code = fm.get("leychile_code")
        if not code and (fuente := fm.get("fuente_oficial")):
            m = LEYCHILE_RE.search(fuente)
            if m:
                code = m.group(1)
        if not code:
            no_code += 1
            continue

        uri = lookup_sqlite(con, code)
        source = "sqlite"
        if not uri and sparql_attempts < args.max_sparql:
            sparql_attempts += 1
            uri = lookup_sparql(code)
            source = "sparql"
            time.sleep(args.rate)

        if not uri:
            not_found += 1
            print(f"  [MISS] {f.stem} leychile={code}")
            continue

        if source == "sqlite":
            by_sqlite += 1
        else:
            by_sparql += 1

        if args.apply:
            new_fm = insert_bcn_uri(fm_str, uri)
            f.write_text(new_fm + body, encoding="utf-8")
        print(f"  [OK-{source}] {f.stem}: {uri[-60:]}")

    print(f"\n[RESUMEN]")
    print(f"  Ya tenían bcn_uri:    {already}")
    print(f"  Resueltos via SQLite: {by_sqlite}")
    print(f"  Resueltos via SPARQL: {by_sparql}")
    print(f"  Sin leychile_code:    {no_code}")
    print(f"  No encontrados:       {not_found}")
    print(f"  Apply: {'sí' if args.apply else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
