#!/usr/bin/env python3
# std:input chile/normativa/{leyes,codigos,decretos}/*.md (capa 3 sin bcn_uri)
# std:output modifica frontmatter agregando bcn_uri
# std:deps stdlib pura
"""
Resolver MASS de bcn_uri usando SPARQL VALUES batch.

Pide todos los códigos faltantes en UNA query SPARQL con VALUES:

    SELECT DISTINCT ?n ?c WHERE {
      ?n bcnnorms:leychileCode ?c .
      VALUES ?c { 236106 127911 ... }
      FILTER (!REGEX(str(?n), "/es@"))
    }

100× más rápido que one-by-one con retries.

Uso:
    python3 chile/scripts/audit/resolver-bcn-uri-batch.py [--apply]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CAPA3_DIRS = [
    REPO_ROOT / "chile/normativa/leyes",
    REPO_ROOT / "chile/normativa/codigos",
    REPO_ROOT / "chile/normativa/decretos",
]
SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.7"
LEYCHILE_RE = re.compile(r"idNorma=(\d+)")


def parse_fm_full(text: str) -> tuple[str, str, str]:
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


def insert_bcn_uri(fm_str: str, uri: str) -> str:
    if "bcn_uri:" in fm_str:
        return fm_str
    if "fuente_oficial:" in fm_str:
        return re.sub(
            r"(fuente_oficial:[^\n]*\n)",
            r"\1bcn_uri: " + uri + "\n",
            fm_str,
            count=1,
        )
    return fm_str.replace("---\n", f"bcn_uri: {uri}\n---\n", 1)


def sparql_batch(codes: list[str], timeout: int = 60) -> dict[str, str]:
    """Devuelve dict code → uri. Usa VALUES con integers."""
    if not codes:
        return {}
    values_str = " ".join(codes)  # integer literals
    query = f"""
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
SELECT DISTINCT ?n ?c WHERE {{
  VALUES ?c {{ {values_str} }}
  ?n bcnnorms:leychileCode ?c .
  FILTER (!REGEX(str(?n), "/es@"))
  FILTER (!REGEX(str(?n), "/proyecto-de-ley/"))
}}
"""
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    backoff = 5
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
                out: dict[str, str] = {}
                for row in data.get("results", {}).get("bindings", []):
                    code = row.get("c", {}).get("value")
                    uri = row.get("n", {}).get("value")
                    if code and uri and code not in out:
                        out[code] = uri
                return out
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except (TimeoutError, OSError):
            time.sleep(backoff)
            backoff *= 2
            continue
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch", type=int, default=50)
    args = parser.parse_args()

    # Recopilar perfiles sin bcn_uri + sus leychile_code
    pending: list[tuple[Path, str, str, str]] = []  # (file, fm_str, body, code)
    for d in CAPA3_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            fm_raw, fm_str, body = parse_fm_full(text)
            fm = parse_fm_dict(fm_raw)
            if "bcn_uri" in fm and fm["bcn_uri"]:
                continue
            code = fm.get("leychile_code")
            if not code and (fuente := fm.get("fuente_oficial")):
                m = LEYCHILE_RE.search(fuente)
                if m:
                    code = m.group(1)
            if not code:
                continue
            # Verificar que es un entero
            try:
                int(code)
            except ValueError:
                continue
            pending.append((f, fm_str, body, code))

    print(f"[INFO] {len(pending)} perfiles pendientes de resolver")
    if not pending:
        return 0

    # Batch SPARQL
    unique_codes = list({p[3] for p in pending})
    print(f"[INFO] {len(unique_codes)} códigos únicos a resolver")

    all_uris: dict[str, str] = {}
    for i in range(0, len(unique_codes), args.batch):
        batch = unique_codes[i : i + args.batch]
        print(f"  [BATCH {i}-{i+len(batch)}] resolviendo {len(batch)} códigos...", flush=True)
        uris = sparql_batch(batch)
        all_uris.update(uris)
        print(f"    encontrados {len(uris)}/{len(batch)}", flush=True)
        time.sleep(2)

    # Aplicar
    applied = 0
    no_match = 0
    for f, fm_str, body, code in pending:
        if code in all_uris:
            new_fm = insert_bcn_uri(fm_str, all_uris[code])
            if args.apply:
                f.write_text(new_fm + body, encoding="utf-8")
            applied += 1
        else:
            no_match += 1
            print(f"  [NO-MATCH] {f.stem} code={code}")

    print(f"\n[RESUMEN]")
    print(f"  Pendientes:      {len(pending)}")
    print(f"  Códigos únicos:  {len(unique_codes)}")
    print(f"  Resueltos:       {len(all_uris)}")
    print(f"  Aplicados:       {applied}")
    print(f"  Sin match BCN:   {no_match}")
    print(f"  Apply: {args.apply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
