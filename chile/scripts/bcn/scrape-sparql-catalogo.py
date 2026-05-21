#!/usr/bin/env python3
# std:input -
# std:output catálogo capa 1 completo en chile/normativa/catalogo/{tipo}/...md
# std:deps stdlib pura
"""
Catálogo capa 1 completo via SPARQL endpoint datos.bcn.cl/sparql.

Reemplaza el scrape REST iterativo (22k requests, frágil) por queries
SPARQL paginadas contra el grafo BCN.

El grafo contiene ~748.765 instancias de bcn-norms#Norm, de las cuales
~359k son RootNorm (versión "raíz" de cada norma, sin versionado por
modificación). Trabajamos con RootNorm: una entrada por norma.

Para cada RootNorm extrae:
- URI (http://datos.bcn.cl/recurso/cl/{tipo}/...)
- leychileCode (id en leychile.cl)
- label
- type (clasificación BCN: ley, decreto-ley, decreto-con-fuerza-de-ley,
  decreto-supremo, resolución, etc.)
- hasNumber
- publishDate, promulgationDate
- createdBy (organismo)

Lo escribe en chile/normativa/catalogo/{tipo}/{slug}.md con frontmatter
canónico.

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: sólo persiste
lo que SPARQL devuelve.

Uso:
    python3 scrape-sparql-catalogo.py --batch 1000 --max 10000 [--offset N]
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
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"

SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.6 (unholster.com)"

# Query template — RootNorm con metadata clave.
# OPTIONAL para tolerar normas con datos parciales.
QUERY_TPL = """
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?norma ?leychileCode ?label ?numero ?publishDate ?promulgationDate ?organismo ?type
WHERE {{
  ?norma a bcnnorms:RootNorm .
  OPTIONAL {{ ?norma bcnnorms:leychileCode ?leychileCode }}
  OPTIONAL {{ ?norma rdfs:label ?label }}
  OPTIONAL {{ ?norma bcnnorms:hasNumber ?numero }}
  OPTIONAL {{ ?norma bcnnorms:publishDate ?publishDate }}
  OPTIONAL {{ ?norma bcnnorms:promulgationDate ?promulgationDate }}
  OPTIONAL {{ ?norma bcnnorms:createdBy ?organismo }}
  OPTIONAL {{ ?norma bcnnorms:type ?type }}
}}
ORDER BY ?norma
LIMIT {limit} OFFSET {offset}
"""

TIPO_FROM_URI = re.compile(r"/recurso/cl/([^/]+)/")
ORGANISMO_FROM_URI = re.compile(r"/organismo/([^/?#]+)")


def sparql_query(query: str, timeout: int = 120) -> dict:
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_value(b: dict | None) -> str | None:
    if not b:
        return None
    return b.get("value")


def slug_from_uri(uri: str) -> str | None:
    """Genera slug estable desde URI BCN.

    Ejemplo:
    http://datos.bcn.cl/recurso/cl/ley/ministerio-de-hacienda/2020-03-04/21210
        -> "21210" si tipo=ley, o el path completo si no es ley con numero.
    """
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return None
    path = uri[len("http://datos.bcn.cl/recurso/cl/"):]
    return path.replace("/", "_")


def tipo_from_uri(uri: str) -> str | None:
    m = TIPO_FROM_URI.search(uri)
    return m.group(1) if m else None


def organismo_short(uri: str | None) -> str | None:
    if not uri:
        return None
    m = ORGANISMO_FROM_URI.search(uri)
    if m:
        return m.group(1)
    if "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return uri


def write_norma(row: dict) -> Path | None:
    uri = normalize_value(row.get("norma"))
    if not uri:
        return None
    tipo = tipo_from_uri(uri)
    if not tipo:
        return None
    slug = slug_from_uri(uri)
    if not slug:
        return None

    leychile_code = normalize_value(row.get("leychileCode"))
    label = normalize_value(row.get("label")) or ""
    numero = normalize_value(row.get("numero"))
    publish_date = normalize_value(row.get("publishDate"))
    promulg_date = normalize_value(row.get("promulgationDate"))
    organismo = organismo_short(normalize_value(row.get("organismo")))
    norm_type = normalize_value(row.get("type"))

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
    if publish_date:
        fm += f"publicacion: {publish_date}\n"
    if promulg_date:
        fm += f"promulgacion: {promulg_date}\n"
    if organismo:
        fm += f"emisor: {organismo}\n"
    if leychile_code:
        fm += (
            f"leychile_code: {leychile_code}\n"
            f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={leychile_code}\n"
        )
    if norm_type:
        fm += f"bcn_type: {norm_type}\n"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Catálogo BCN via SPARQL")
    parser.add_argument("--batch", type=int, default=1000)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument(
        "--max", type=int, default=400000,
        help="Total máximo a procesar (corte de seguridad)",
    )
    parser.add_argument("--rate", type=float, default=2.0)
    args = parser.parse_args()

    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    offset = args.offset
    total_written = 0
    by_tipo: dict[str, int] = {}
    start = time.time()

    print(
        f"[INFO] SPARQL scrape: batch={args.batch} offset={offset} "
        f"max={args.max} rate={args.rate}s",
        flush=True,
    )

    while total_written < args.max:
        query = QUERY_TPL.format(limit=args.batch, offset=offset)
        retries = 0
        while True:
            try:
                data = sparql_query(query)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and retries < 8:
                    sleep_s = 5 * (2 ** retries)
                    print(f"  [WARN] HTTP {e.code}, retry in {sleep_s}s", flush=True)
                    time.sleep(sleep_s)
                    retries += 1
                    continue
                raise
            except Exception as e:
                if retries < 5:
                    sleep_s = 5 * (2 ** retries)
                    print(
                        f"  [WARN] {type(e).__name__}: {e}, retry in {sleep_s}s",
                        flush=True,
                    )
                    time.sleep(sleep_s)
                    retries += 1
                    continue
                raise

        rows = data.get("results", {}).get("bindings", [])
        if not rows:
            print(f"[INFO] Batch vacío en offset {offset}, terminando.", flush=True)
            break

        batch_written = 0
        for row in rows:
            path = write_norma(row)
            if path:
                batch_written += 1
                tipo = path.parent.name
                by_tipo[tipo] = by_tipo.get(tipo, 0) + 1

        total_written += batch_written
        offset += args.batch
        elapsed = time.time() - start
        rate = total_written / elapsed if elapsed > 0 else 0
        print(
            f"[BATCH] offset={offset} batch_written={batch_written} "
            f"total={total_written} elapsed={elapsed:.0f}s "
            f"rate={rate:.0f}/s",
            flush=True,
        )

        time.sleep(args.rate)

    print(f"\n[DONE] {total_written} normas guardadas en {time.time() - start:.0f}s")
    for tipo, n in sorted(by_tipo.items(), key=lambda x: -x[1]):
        print(f"  {tipo}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
