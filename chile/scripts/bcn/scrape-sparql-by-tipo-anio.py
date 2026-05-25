#!/usr/bin/env python3
"""Scrape BCN SPARQL paginado por (tipo, año) para tipos masivos.

scrape-sparql-by-tipo.py original timeout para dto (173k) y res (149k)
porque la query única sobre el tipo es demasiado pesada en el endpoint.

Este script:
- Itera años 1810..hoy
- Por cada año, query con FILTER(year(?publishDate) = YYYY)
- Cada batch típicamente <5k rows → no timeout

Idempotente: skip si el archivo destino ya existe.
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"
SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"

TIPO_URI = "http://datos.bcn.cl/recurso/cl/norma/tipo#{tipo}"

QUERY_TPL = """
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?norma ?leychileCode ?label ?numero ?publishDate ?promulgationDate ?organismo
WHERE {{
  ?norma a bcnnorms:RootNorm .
  ?norma bcnnorms:type <{tipo_uri}> .
  ?norma bcnnorms:publishDate ?publishDate .
  FILTER (?publishDate >= "{year}-01-01"^^xsd:date && ?publishDate <= "{year}-12-31"^^xsd:date)
  OPTIONAL {{ ?norma bcnnorms:leychileCode ?leychileCode }}
  OPTIONAL {{ ?norma rdfs:label ?label }}
  OPTIONAL {{ ?norma bcnnorms:hasNumber ?numero }}
  OPTIONAL {{ ?norma bcnnorms:promulgationDate ?promulgationDate }}
  OPTIONAL {{ ?norma bcnnorms:createdBy ?organismo }}
}}
"""


def sparql_query(query: str, timeout: int = 180) -> dict:
    """POST query (más tolerante a tamaño que GET URL-encoded)."""
    data = urllib.parse.urlencode({
        "query": query, "format": "application/sparql-results+json",
    }).encode()
    req = urllib.request.Request(
        SPARQL_URL, data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(b: dict | None) -> str | None:
    return b.get("value") if b else None


def slug_from_uri(uri: str) -> str | None:
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return None
    return uri[len("http://datos.bcn.cl/recurso/cl/"):].replace("/", "_")


def write_norma(row: dict, tipo: str) -> bool:
    uri = normalize(row.get("norma"))
    if not uri:
        return False
    slug = slug_from_uri(uri)
    if not slug:
        return False
    out_dir = CATALOG_ROOT / tipo
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.md"
    if path.exists():
        return False  # idempotente
    leychile = normalize(row.get("leychileCode"))
    label = normalize(row.get("label")) or ""
    numero = normalize(row.get("numero"))
    publish = normalize(row.get("publishDate"))
    promulg = normalize(row.get("promulgationDate"))
    organismo = normalize(row.get("organismo"))
    if organismo and "/" in organismo:
        organismo = organismo.rsplit("/", 1)[-1]

    titulo = (label or "").replace('"', '\\"')
    fm = "---\n" + f"slug: {slug}\n" + f"tipo: {tipo}\n"
    if numero: fm += f"numero: {numero}\n"
    if titulo: fm += f'titulo_oficial: "{titulo}"\n'
    if publish: fm += f"publicacion: {publish}\n"
    if promulg: fm += f"promulgacion: {promulg}\n"
    if organismo: fm += f"emisor: {organismo}\n"
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
    if titulo: fm += f"**Título oficial:** {label}\n"
    path.write_text(fm, encoding="utf-8")
    return True


def scrape_tipo_anio(tipo: str, year: int, retries: int = 3) -> int:
    tipo_uri = TIPO_URI.format(tipo=tipo)
    q = QUERY_TPL.format(tipo_uri=tipo_uri, year=year)
    for attempt in range(retries):
        try:
            data = sparql_query(q)
            rows = data.get("results", {}).get("bindings", [])
            n_written = 0
            for r in rows:
                if write_norma(r, tipo):
                    n_written += 1
            return n_written
        except urllib.error.HTTPError as e:
            wait = 10 * (2 ** attempt)
            print(f"  [{tipo} {year}] HTTP {e.code}, retry {wait}s", flush=True)
            time.sleep(wait)
        except TimeoutError:
            wait = 30 * (2 ** attempt)
            print(f"  [{tipo} {year}] timeout, retry {wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:
            print(f"  [{tipo} {year}] err {type(e).__name__}: {str(e)[:60]}", flush=True)
            return -1
    return -1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipos", default="dto,res",
                        help="comma-separated, default tipos masivos")
    parser.add_argument("--from-year", type=int, default=2000)
    parser.add_argument("--to-year", type=int, default=2026)
    parser.add_argument("--rate", type=float, default=1.0,
                        help="sleep entre años")
    args = parser.parse_args()

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    print(f"Tipos: {tipos}, años {args.from_year}..{args.to_year}", flush=True)

    grand_total = 0
    start = time.time()
    for tipo in tipos:
        print(f"\n[TIPO] {tipo}", flush=True)
        tipo_total = 0
        # Reverse cronológica: año más reciente primero
        for year in range(args.to_year, args.from_year - 1, -1):
            n = scrape_tipo_anio(tipo, year)
            if n < 0:
                print(f"  [{tipo} {year}] FAIL after retries, skip", flush=True)
                continue
            tipo_total += n
            print(f"  [{tipo} {year}] +{n} (tipo total {tipo_total})", flush=True)
            time.sleep(args.rate)
        print(f"\n[{tipo} DONE] {tipo_total} normas", flush=True)
        grand_total += tipo_total

    elapsed = time.time() - start
    print(f"\n[ALL DONE] {elapsed:.0f}s | {grand_total} normas total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
