#!/usr/bin/env python3
# std:input chile/normativa/index/catalogo.sqlite3 (grafo + catálogo)
# std:output chile/normativa/catalogo/{tipo}/...md
# std:deps stdlib pura
"""
Scrape SELECTIVO de las URIs del grafo BCN que aún no están en el
catálogo local.

Estrategia: en lugar de scrapear los 173k dto + 149k res masivos
(necesario para cobertura total, pero ~10h y endpoint flaky), scrapear
solo los nodos que aparecen como dst en las relaciones del grafo.

Resultado esperado: ~80k URIs adicionales en el catálogo, suficiente
para que >95% de las relaciones se resuelvan a slug local.

Algoritmo:
1. Query SQLite: distinct dst_uri NOT in catalog, sin alias /es@.
2. Batch SPARQL VALUES de N URIs por query (batches de 100).
3. Parsear binding y escribir a `catalogo/{tipo}/{slug}.md`.

Idempotente: skip si archivo ya existe.

Uso:
    python3 chile/scripts/bcn/scrape-sparql-uris-grafo.py \
        [--batch 100] [--max-uris 100000] [--apply]
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
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"
SPARQL_URL = "https://datos.bcn.cl/sparql"
USER_AGENT = "claude-legal-chile/0.7"

TIPO_RE = re.compile(r"http://datos.bcn.cl/recurso/cl/([^/]+)/")


def list_missing_uris(con: sqlite3.Connection, max_uris: int) -> list[str]:
    """URIs en grafo NOT en catalog."""
    rows = con.execute("""
        SELECT DISTINCT dst_uri FROM relaciones
        WHERE dst_uri NOT LIKE '%/es@%'
          AND NOT EXISTS(SELECT 1 FROM normas WHERE bcn_uri = dst_uri)
        LIMIT ?
    """, (max_uris,)).fetchall()
    return [r[0] for r in rows]


def sparql_batch(uris: list[str], timeout: int = 60) -> dict | None:
    """Query SPARQL con VALUES batch."""
    values = " ".join(f"<{u}>" for u in uris)
    query = f"""
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?n ?label ?code ?numero ?pub ?prom ?org WHERE {{
  VALUES ?n {{ {values} }}
  ?n rdfs:label ?label .
  OPTIONAL {{ ?n bcnnorms:leychileCode ?code }}
  OPTIONAL {{ ?n bcnnorms:hasNumber ?numero }}
  OPTIONAL {{ ?n bcnnorms:publishDate ?pub }}
  OPTIONAL {{ ?n bcnnorms:promulgationDate ?prom }}
  OPTIONAL {{ ?n bcnnorms:createdBy ?org }}
}}
"""
    url = SPARQL_URL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.HTTPError, TimeoutError, OSError) as e:
        return None


def normalize(b: dict | None) -> str | None:
    return b.get("value") if b else None


def slug_from_uri(uri: str) -> str | None:
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return None
    return uri[len("http://datos.bcn.cl/recurso/cl/"):].replace("/", "_")


def tipo_from_uri(uri: str) -> str | None:
    m = TIPO_RE.search(uri)
    return m.group(1) if m else None


def organismo_short(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rsplit("/", 1)[-1] if "/" in uri else uri


def write_norma(uri: str, row: dict) -> Path | None:
    tipo = tipo_from_uri(uri)
    if not tipo:
        return None
    slug = slug_from_uri(uri)
    if not slug:
        return None
    out_dir = CATALOG_ROOT / tipo
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.md"
    if path.exists():
        return None

    label = normalize(row.get("label")) or ""
    code = normalize(row.get("code"))
    numero = normalize(row.get("numero"))
    pub = normalize(row.get("pub"))
    prom = normalize(row.get("prom"))
    organismo = organismo_short(normalize(row.get("org")))

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
    if pub:
        fm += f"publicacion: {pub}\n"
    if prom:
        fm += f"promulgacion: {prom}\n"
    if organismo:
        fm += f"emisor: {organismo}\n"
    if code:
        fm += (
            f"leychile_code: {code}\n"
            f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={code}\n"
        )
    fm += (
        f"bcn_uri: {uri}\n"
        "capa: 1\n"
        "estado_revision: catalogo-bcn-grafo-selectivo\n"
        "---\n\n"
        f"# {tipo.upper()} {numero or ''}\n\n"
    )
    if titulo:
        fm += f"**Título oficial:** {label}\n"
    path.write_text(fm, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=100)
    parser.add_argument("--max-uris", type=int, default=100000)
    parser.add_argument("--rate", type=float, default=1.5)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.exists():
        print(f"[FATAL] SQLite no existe: {DB}")
        return 1

    con = sqlite3.connect(str(DB))
    print(f"[INFO] Calculando URIs faltantes (LIMIT={args.max_uris})...")
    uris = list_missing_uris(con, args.max_uris)
    print(f"[INFO] {len(uris):,} URIs únicas a scrapear")

    if not args.apply:
        # Dry-run: muestra distribución por tipo
        by_tipo: dict[str, int] = {}
        for u in uris:
            t = tipo_from_uri(u) or "?"
            by_tipo[t] = by_tipo.get(t, 0) + 1
        for t, n in sorted(by_tipo.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n:,}")
        print("\nDry-run. Usar --apply para scrapear.")
        return 0

    total_written = 0
    total_skipped = 0
    start = time.time()
    for i in range(0, len(uris), args.batch):
        batch = uris[i : i + args.batch]
        retries = 0
        while True:
            data = sparql_batch(batch)
            if data is not None:
                break
            retries += 1
            if retries > 5:
                print(f"  [GIVE-UP] batch {i}-{i+len(batch)}, skip")
                data = {"results": {"bindings": []}}
                break
            sleep_s = 5 * (2 ** retries)
            print(f"  [WARN] retry {sleep_s}s")
            time.sleep(sleep_s)

        rows = data.get("results", {}).get("bindings", [])
        # Agrupa por URI
        by_uri = {}
        for r in rows:
            u = r.get("n", {}).get("value")
            if u and u not in by_uri:
                by_uri[u] = r

        batch_written = 0
        for u in batch:
            if u in by_uri:
                if write_norma(u, by_uri[u]):
                    batch_written += 1
                    total_written += 1
                else:
                    total_skipped += 1
            else:
                total_skipped += 1

        elapsed = time.time() - start
        rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
        eta = (len(uris) - i - len(batch)) / rate if rate > 0 else 0
        print(
            f"  [BATCH {i:>6}-{i+len(batch):<6}] written={batch_written} "
            f"total_written={total_written} skipped={total_skipped} "
            f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
            flush=True,
        )
        time.sleep(args.rate)

    print(f"\n[DONE] {total_written:,} archivos escritos, {total_skipped:,} skipped en {time.time()-start:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
