#!/usr/bin/env python3
# std:input lista de tipos
# std:output chile/normativa/catalogo/{tipo}/...md
# std:deps stdlib pura
"""
Scrape catálogo BCN paginando por TIPO de norma.

Evita el bug observado en el endpoint SPARQL público con OFFSET > ~10000
(devuelve HTTP 500 repetido). Particionando por tipo, cada partición es
manejable (max ~16k para ley, ~4k para dl, etc.).

Para los tipos masivos (dto=173k, res=149k), reusar este script con un
filtro adicional por año o organismo (no implementado aquí — pasada
posterior).

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: solo persiste
lo que SPARQL devuelve.

Uso:
    python3 scrape-sparql-by-tipo.py --tipos ley,dl,dfl,cod,tra,aa,acd
    python3 scrape-sparql-by-tipo.py --tipos dto --max-per-tipo 5000
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
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"
SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.6 (unholster.com)"

TIPO_URI = "http://datos.bcn.cl/recurso/cl/norma/tipo#{tipo}"

QUERY_TPL = """
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?norma ?leychileCode ?label ?numero ?publishDate ?promulgationDate ?organismo
WHERE {{
  ?norma a bcnnorms:RootNorm .
  ?norma bcnnorms:type <{tipo_uri}> .
  FILTER (str(?norma) > "{after_uri}")
  OPTIONAL {{ ?norma bcnnorms:leychileCode ?leychileCode }}
  OPTIONAL {{ ?norma rdfs:label ?label }}
  OPTIONAL {{ ?norma bcnnorms:hasNumber ?numero }}
  OPTIONAL {{ ?norma bcnnorms:publishDate ?publishDate }}
  OPTIONAL {{ ?norma bcnnorms:promulgationDate ?promulgationDate }}
  OPTIONAL {{ ?norma bcnnorms:createdBy ?organismo }}
}}
ORDER BY ?norma
LIMIT {limit}
"""


def sparql_query(query: str, timeout: int = 120) -> dict:
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(b: dict | None) -> str | None:
    return b.get("value") if b else None


def slug_from_uri(uri: str) -> str | None:
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return None
    return uri[len("http://datos.bcn.cl/recurso/cl/"):].replace("/", "_")


def organismo_short(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rsplit("/", 1)[-1] if "/" in uri else uri


def write_norma(row: dict, tipo: str) -> Path | None:
    uri = normalize(row.get("norma"))
    if not uri:
        return None
    slug = slug_from_uri(uri)
    if not slug:
        return None

    leychile = normalize(row.get("leychileCode"))
    label = normalize(row.get("label")) or ""
    numero = normalize(row.get("numero"))
    publish = normalize(row.get("publishDate"))
    promulg = normalize(row.get("promulgationDate"))
    organismo = organismo_short(normalize(row.get("organismo")))

    out_dir = CATALOG_ROOT / tipo
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.md"

    titulo = label.replace('"', '\\"')

    fm = (
        "---\n"
        f"slug: {slug}\n"
        f"tipo: {tipo}\n"
    )
    if numero:
        fm += f"numero: {numero}\n"
    if titulo:
        fm += f'titulo_oficial: "{titulo}"\n'
    if publish:
        fm += f"publicacion: {publish}\n"
    if promulg:
        fm += f"promulgacion: {promulg}\n"
    if organismo:
        fm += f"emisor: {organismo}\n"
    if leychile:
        fm += (
            f"leychile_code: {leychile}\n"
            f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={leychile}\n"
        )
    fm += (
        f"bcn_uri: {uri}\n"
        "capa: 1\n"
        "estado_revision: catalogo-bcn-sparql\n"
        "---\n\n"
        f"# {tipo.upper()} {numero or ''}\n\n"
    )
    if titulo:
        fm += f"**Título oficial:** {label}\n"
    path.write_text(fm, encoding="utf-8")
    return path


def scrape_tipo(tipo: str, batch: int, max_per_tipo: int, rate: float) -> int:
    tipo_uri = TIPO_URI.format(tipo=tipo)
    after_uri = ""
    total = 0
    start = time.time()
    print(f"\n[TIPO] {tipo} (uri={tipo_uri})", flush=True)

    while total < max_per_tipo:
        query = QUERY_TPL.format(tipo_uri=tipo_uri, limit=batch, after_uri=after_uri)
        retries = 0
        data = None
        while True:
            try:
                data = sparql_query(query)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and retries < 8:
                    sleep_s = 5 * (2 ** retries)
                    print(f"  [WARN] HTTP {e.code}, retry {sleep_s}s", flush=True)
                    time.sleep(sleep_s)
                    retries += 1
                    continue
                print(f"  [FATAL] HTTP {e.code}, abort tipo {tipo}", flush=True)
                break
            except Exception as e:
                if retries < 8:
                    sleep_s = 5 * (2 ** retries)
                    print(
                        f"  [WARN] {type(e).__name__}: {e}, retry {sleep_s}s",
                        flush=True,
                    )
                    time.sleep(sleep_s)
                    retries += 1
                    continue
                print(f"  [FATAL] {type(e).__name__}: {e}", flush=True)
                break

        if data is None:
            break

        rows = data.get("results", {}).get("bindings", [])
        if not rows:
            break

        written = 0
        new_after = after_uri
        for row in rows:
            uri = row.get("norma", {}).get("value", "")
            if write_norma(row, tipo):
                written += 1
            if uri and uri > new_after:
                new_after = uri
        if new_after == after_uri:
            print(f"  [BREAK] cursor sin avance, fin de {tipo}", flush=True)
            break
        after_uri = new_after

        total += written
        elapsed = time.time() - start
        print(
            f"  [BATCH] after={after_uri[-50:]!r} written={written} total={total} "
            f"elapsed={elapsed:.0f}s",
            flush=True,
        )
        time.sleep(rate)

        if len(rows) < batch:
            break

    elapsed = time.time() - start
    print(f"  [DONE] {tipo}: {total} normas en {elapsed:.0f}s", flush=True)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape BCN by tipo")
    parser.add_argument(
        "--tipos", required=True,
        help="Lista de tipos separados por coma (ley,dl,dfl,cod,tra,aa,acd,...)",
    )
    parser.add_argument("--batch", type=int, default=500)
    parser.add_argument("--max-per-tipo", type=int, default=20000)
    parser.add_argument("--rate", type=float, default=2.0)
    args = parser.parse_args()

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    grand_total = 0
    start = time.time()
    by_tipo: dict[str, int] = {}

    for tipo in tipos:
        n = scrape_tipo(tipo, args.batch, args.max_per_tipo, args.rate)
        by_tipo[tipo] = n
        grand_total += n

    elapsed = time.time() - start
    print(f"\n[ALL DONE] {grand_total} normas en {elapsed:.0f}s")
    for tipo, n in sorted(by_tipo.items(), key=lambda x: -x[1]):
        print(f"  {tipo}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
