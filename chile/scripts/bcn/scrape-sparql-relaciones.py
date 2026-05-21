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
  FILTER (str(?src) > "{after_src}")
}}
ORDER BY ?src ?dst
LIMIT {limit}
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
    parser.add_argument("--batch", type=int, default=2000)
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument(
        "--max-per-rel", type=int, default=500000,
        help="Tope de seguridad por relación",
    )
    parser.add_argument(
        "--append", action="store_true",
        help="Append al JSONL existente y reanudar por last_src",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    by_rel: dict[str, int] = {}
    start = time.time()

    # Resume from existing jsonl: precompute last src per rel
    last_src_by_rel: dict[str, str] = {rel: "" for rel in RELATIONS}
    counts_by_rel: dict[str, int] = {rel: 0 for rel in RELATIONS}
    if OUTPUT_FILE.exists() and args.append:
        print(f"[INFO] Reanudando desde {OUTPUT_FILE}", flush=True)
        with open(OUTPUT_FILE, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rel = row.get("rel")
                src = row.get("src")
                if rel in last_src_by_rel and src:
                    if src > last_src_by_rel[rel]:
                        last_src_by_rel[rel] = src
                    counts_by_rel[rel] += 1
        for rel, n in counts_by_rel.items():
            if n:
                print(f"  [RESUME] {rel}: {n} edges ya en JSONL, last_src={last_src_by_rel[rel][:60]!r}")

    mode = "a" if args.append else "w"
    with open(OUTPUT_FILE, mode, encoding="utf-8") as fh:
        for rel in RELATIONS:
            print(f"\n[REL] {rel}", flush=True)
            after_src = last_src_by_rel[rel]
            rel_count = counts_by_rel[rel]
            while rel_count < args.max_per_rel:
                query = QUERY_TPL.format(
                    rel=rel, limit=args.batch, after_src=after_src
                )
                retries = 0
                while True:
                    try:
                        data = sparql_query(query)
                        break
                    except urllib.error.HTTPError as e:
                        if e.code in (429, 500, 502, 503, 504) and retries < 8:
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

                batch_added = 0
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
                        batch_added += 1
                        if src > after_src:
                            after_src = src
                fh.flush()

                if batch_added == 0:
                    print(f"  [BREAK] batch sin datos nuevos, fin de {rel}")
                    break
                elapsed = time.time() - start
                print(
                    f"  added={batch_added} rel_total={rel_count} "
                    f"grand_total={total} elapsed={elapsed:.0f}s "
                    f"after_src={after_src[-60:]!r}",
                    flush=True,
                )
                if len(rows) < args.batch:
                    break
                time.sleep(args.rate)

            by_rel[rel] = rel_count

    elapsed = time.time() - start
    print(f"\n[DONE] {total} edges en {elapsed:.0f}s")
    for rel, n in sorted(by_rel.items(), key=lambda x: -x[1]):
        print(f"  {rel}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
