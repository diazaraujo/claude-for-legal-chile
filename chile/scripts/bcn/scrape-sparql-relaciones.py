#!/usr/bin/env python3
# std:input -
# std:output chile/normativa/grafo/relaciones-bcn.jsonl
# std:deps stdlib pura
"""
Dump del grafo de relaciones entre normas BCN via SPARQL.

Para cada relación explícita en el ontology bcn-norms:
- modifiesTo / isModifiedBy
- regulates / isRegulatedBy
- recasts / isRecastedBy
- rectifies / isRectifiedBy
- agreeWith

Escribe una línea JSONL por relación: {"src": uri, "rel": "modifies",
"dst": uri}. Permite reconstruir el grafo dirigido sin parsing de texto.

Sólo persiste lo que SPARQL devuelve. Conforme a
[[feedback-no-inventar-ids-urls-referencias]].

Uso:
    python3 scrape-sparql-relaciones.py --batch 5000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = REPO_ROOT / "chile/normativa/grafo"
OUTPUT_FILE = OUTPUT_DIR / "relaciones-bcn.jsonl"

SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.6 (unholster.com)"

RELATIONS = [
    "modifiesTo",
    "isModifiedBy",
    "regulates",
    "isRegulatedBy",
    "recasts",
    "isRecastedBy",
    "rectifies",
    "isRectifiedBy",
    "agreeWith",
]

QUERY_TPL = """
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>

SELECT ?src ?dst
WHERE {{
  ?src bcnnorms:{rel} ?dst .
}}
ORDER BY ?src ?dst
LIMIT {limit} OFFSET {offset}
"""


def sparql_query(query: str, timeout: int = 180) -> dict:
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump relaciones BCN")
    parser.add_argument("--batch", type=int, default=5000)
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument(
        "--max-per-rel", type=int, default=500000,
        help="Tope de seguridad por relación",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    by_rel: dict[str, int] = {}
    start = time.time()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        for rel in RELATIONS:
            print(f"\n[REL] {rel}", flush=True)
            offset = 0
            rel_count = 0
            while rel_count < args.max_per_rel:
                query = QUERY_TPL.format(rel=rel, limit=args.batch, offset=offset)
                retries = 0
                while True:
                    try:
                        data = sparql_query(query)
                        break
                    except urllib.error.HTTPError as e:
                        if e.code in (429, 502, 503, 504) and retries < 5:
                            sleep_s = 5 * (2 ** retries)
                            print(f"  HTTP {e.code}, retry {sleep_s}s", flush=True)
                            time.sleep(sleep_s)
                            retries += 1
                            continue
                        raise
                    except Exception as e:
                        if retries < 5:
                            sleep_s = 5 * (2 ** retries)
                            print(
                                f"  {type(e).__name__}: {e}, retry {sleep_s}s",
                                flush=True,
                            )
                            time.sleep(sleep_s)
                            retries += 1
                            continue
                        raise

                rows = data.get("results", {}).get("bindings", [])
                if not rows:
                    break

                for row in rows:
                    src = row.get("src", {}).get("value")
                    dst = row.get("dst", {}).get("value")
                    if src and dst:
                        fh.write(
                            json.dumps(
                                {"src": src, "rel": rel, "dst": dst},
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                        rel_count += 1
                        total += 1

                offset += args.batch
                elapsed = time.time() - start
                print(
                    f"  offset={offset} rel_total={rel_count} "
                    f"grand_total={total} elapsed={elapsed:.0f}s",
                    flush=True,
                )
                time.sleep(args.rate)

            by_rel[rel] = rel_count

    elapsed = time.time() - start
    print(f"\n[DONE] {total} edges en {elapsed:.0f}s")
    for rel, n in sorted(by_rel.items(), key=lambda x: -x[1]):
        print(f"  {rel}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
