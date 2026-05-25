#!/usr/bin/env python3
"""Scrape BCN SPARQL via CONSTRUCT + turtle.

Descubierto 2026-05-25: el endpoint Virtuoso de datos.bcn.cl timeout
para SELECT sobre tipos masivos (dto 173k, res 149k) — pero acepta
CONSTRUCT con format=text/turtle y LIMIT 5000 en ~110s/batch...

PERO el endpoint aplica rate-limit IP-side luego de pocas requests
fallidas o sostenidas. Tras 3-5 timeouts el endpoint deja de responder
para esa IP durante 30-60 minutos.

WORKFLOW recomendado:
1. Esperar a tener pool fresh (>30 min sin queries)
2. Lanzar UN batch a la vez (no concurrente)
3. Si batch retorna OK, continuar con cursor
4. Si batch timeout: detener + esperar 30 min + retomar con cursor donde quedó

Pagina con FILTER(STR(?n) > "{after}") + ORDER BY ?n + LIMIT — cursor
por URI léxico, idempotente.

Output: chile/normativa/catalogo/{tipo}/{slug}.md (mismo formato que
los otros scrapers).
"""
from __future__ import annotations
import argparse, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"
SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"

TIPO_URI = "http://datos.bcn.cl/recurso/cl/norma/tipo#{tipo}"

# CONSTRUCT con metadata mínima. SIN SUBQUERY ordenado (rompe el endpoint).
# Pagination via FILTER(STR(?n) > "X") — cada batch trae los siguientes
# URIs por orden léxico, sin OFFSET costoso.
QUERY_TPL = """PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
CONSTRUCT {{
  ?n bcnnorms:leychileCode ?code ;
     bcnnorms:hasNumber ?num ;
     bcnnorms:publishDate ?pd ;
     bcnnorms:promulgationDate ?prd ;
     bcnnorms:createdBy ?org ;
     rdfs:label ?lab .
}}
WHERE {{
  ?n a bcnnorms:RootNorm ;
     bcnnorms:type <{tipo_uri}> .
  FILTER (STR(?n) > "{after}")
  OPTIONAL {{ ?n bcnnorms:leychileCode ?code }}
  OPTIONAL {{ ?n bcnnorms:hasNumber ?num }}
  OPTIONAL {{ ?n bcnnorms:publishDate ?pd }}
  OPTIONAL {{ ?n bcnnorms:promulgationDate ?prd }}
  OPTIONAL {{ ?n bcnnorms:createdBy ?org }}
  OPTIONAL {{ ?n rdfs:label ?lab }}
}}
ORDER BY ?n
LIMIT {limit}"""

# Patrones para parsear turtle simple
TRIPLE_RE = re.compile(
    r"<(http://datos\.bcn\.cl/recurso/cl/[^>]+)>\s+"
    r"<(http://datos\.bcn\.cl/ontologies/bcn-norms#\w+|"
    r"http://www\.w3\.org/2000/01/rdf-schema#label)>\s+"
    r'("([^"]*)"(\^\^<[^>]+>)?(@\w+)?|<([^>]+)>)\s*[.;]'
)


def sparql_construct(tipo: str, after: str, limit: int = 5000,
                     timeout: int = 240) -> str:
    q = QUERY_TPL.format(tipo_uri=TIPO_URI.format(tipo=tipo),
                         limit=limit, after=after)
    data = urllib.parse.urlencode({
        "query": q, "format": "text/turtle",
    }).encode()
    req = urllib.request.Request(
        SPARQL_URL, data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/turtle",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_turtle(text: str) -> dict[str, dict]:
    """Parse triples turtle simple → dict[uri][predicate] = value."""
    out: dict[str, dict] = {}
    # Split por triplets — turtle puede usar . o ; como separator
    # Approach: regex sobre cada match
    for m in TRIPLE_RE.finditer(text):
        subject, pred, _full, lit_val, _dtype, _lang, uri_val = m.groups()
        # Local name
        if "#" in pred: local = pred.rsplit("#", 1)[1]
        else: local = pred.rsplit("/", 1)[1]
        val = lit_val if lit_val is not None else uri_val
        out.setdefault(subject, {})[local] = val
    return out


def slug_from_uri(uri: str) -> str | None:
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return None
    return uri[len("http://datos.bcn.cl/recurso/cl/"):].replace("/", "_")


def write_norma(uri: str, props: dict, tipo: str) -> bool:
    slug = slug_from_uri(uri)
    if not slug:
        return False
    out_dir = CATALOG_ROOT / tipo
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.md"
    if path.exists():
        return False  # idempotente

    leychile = props.get("leychileCode")
    label = (props.get("label") or "").replace('"', '\\"')
    numero = props.get("hasNumber")
    publish = props.get("publishDate")
    promulg = props.get("promulgationDate")
    organismo = props.get("createdBy")
    if organismo and "/" in organismo:
        organismo = organismo.rsplit("/", 1)[-1]

    fm = "---\n" + f"slug: {slug}\n" + f"tipo: {tipo}\n"
    if numero: fm += f"numero: {numero}\n"
    if label: fm += f'titulo_oficial: "{label}"\n'
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
    if label: fm += f"**Título oficial:** {props.get('label')}\n"
    path.write_text(fm, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipos", default="dto",
                        help="comma-separated, default dto")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--max", type=int, default=0,
                        help="stop after N URIs written (0 = unlimited)")
    parser.add_argument("--from-uri", default="",
                        help="URI desde el cual continuar (cursor pagination)")
    parser.add_argument("--rate", type=float, default=2.0,
                        help="sleep entre batches")
    args = parser.parse_args()

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    start = time.time()
    grand_total = 0

    for tipo in tipos:
        print(f"\n[TIPO] {tipo}", flush=True)
        after = args.from_uri  # cursor URI
        tipo_total = 0
        consecutive_empty = 0
        while True:
            t0 = time.time()
            try:
                turtle = sparql_construct(tipo, after, args.limit)
            except urllib.error.HTTPError as e:
                wait = 30 * (2 ** min(consecutive_empty, 3))
                print(f"  HTTP {e.code} after={after[-40:]}, retry {wait}s", flush=True)
                time.sleep(wait)
                consecutive_empty += 1
                if consecutive_empty > 3:
                    break
                continue
            except (TimeoutError, urllib.error.URLError, OSError) as e:
                wait = 60 * (2 ** min(consecutive_empty, 3))
                print(f"  conn err {type(e).__name__} after={after[-40:]}, retry {wait}s", flush=True)
                time.sleep(wait)
                consecutive_empty += 1
                if consecutive_empty > 4:
                    break
                continue

            triples = parse_turtle(turtle)
            n_written = 0
            for uri, props in triples.items():
                if write_norma(uri, props, tipo):
                    n_written += 1
            tipo_total += n_written
            grand_total += n_written
            took = time.time() - t0
            # Pick max URI as next cursor
            new_after = max(triples.keys()) if triples else after
            print(f"  URIs={len(triples):>5d} new={n_written:>5d} "
                  f"total={tipo_total} cursor={new_after[-40:]} | {took:.0f}s", flush=True)
            if not triples:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
            else:
                consecutive_empty = 0
            if new_after == after:  # no progress
                break
            after = new_after
            if args.max > 0 and tipo_total >= args.max:
                break
            time.sleep(args.rate)

    elapsed = time.time() - start
    print(f"\n[ALL DONE] {elapsed:.0f}s | {grand_total} normas total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
