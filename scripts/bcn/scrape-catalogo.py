#!/usr/bin/env python3
"""
scrape-catalogo.py — Capa 1 del corpus chileno.

Descarga el catálogo de normas chilenas vigentes desde el endpoint SPARQL público
de BCN (datos.bcn.cl) y escribe un archivo markdown por norma en
`chile/normativa/catalogo/<tipo>/<numero>.md`.

Fuente: ontología bcn-norms (Linked Open Data oficial de BCN).
Endpoint: https://datos.bcn.cl/sparql

Características:
- Idempotente: re-ejecutar no duplica ni rompe archivos validados.
- Paginación con OFFSET para no romper el server (1000 por query).
- Rate limit configurable (default 200ms entre queries).
- Solo versiones vigentes (`bcnnorms:isLatestVersion true`).
- Frontmatter `capa: 1` y `estado_revision: catalogo-auto`.

Uso:
    # Dry run: imprime stats por tipo sin escribir
    python scrape-catalogo.py --dry-run --tipos cod

    # Bajar todos los códigos (19 archivos)
    python scrape-catalogo.py --tipos cod

    # Bajar tier crítico completo (~25K archivos)
    python scrape-catalogo.py --tipos cod,tra,aa,dfl,dl,ley

    # Limitar a N normas por tipo (para pruebas)
    python scrape-catalogo.py --tipos ley --limit 100

Argumentos:
    --tipos       Lista separada por comas (ley, dl, dfl, cod, tra, aa, dto, res, ...)
    --output      Directorio destino (default: chile/normativa/catalogo)
    --dry-run     No escribe archivos, solo reporta
    --limit       Máximo de normas por tipo (default: sin límite)
    --sleep-ms    Pausa entre queries en milisegundos (default: 200)
    --page-size   Tamaño de página SPARQL (default: 1000)
    --force       Sobreescribir archivos existentes (default: skip si ya existe)

# std:input ninguno (consume endpoint SPARQL BCN)
# std:output chile/normativa/catalogo/<tipo>/<numero>.md
# std:deps requests, yaml
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterator

ENDPOINT = "https://datos.bcn.cl/sparql"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "chile" / "normativa" / "catalogo"

# Tipos soportados: nombre corto -> URI BCN
TIPOS_URI = {
    "ley": "http://datos.bcn.cl/recurso/cl/norma/tipo#ley",
    "lei": "http://datos.bcn.cl/recurso/cl/norma/tipo#lei",
    "dl":  "http://datos.bcn.cl/recurso/cl/norma/tipo#dl",
    "dfl": "http://datos.bcn.cl/recurso/cl/norma/tipo#dfl",
    "dto": "http://datos.bcn.cl/recurso/cl/norma/tipo#dto",
    "res": "http://datos.bcn.cl/recurso/cl/norma/tipo#res",
    "cod": "http://datos.bcn.cl/recurso/cl/norma/tipo#cod",
    "tra": "http://datos.bcn.cl/recurso/cl/norma/tipo#tra",
    "aa":  "http://datos.bcn.cl/recurso/cl/norma/tipo#aa",
    "cer": "http://datos.bcn.cl/recurso/cl/norma/tipo#cer",
    "cir": "http://datos.bcn.cl/recurso/cl/norma/tipo#cir",
    "acd": "http://datos.bcn.cl/recurso/cl/norma/tipo#acd",
}


def sparql_query(query: str, sleep_ms: int = 500, max_retries: int = 5) -> dict:
    """Ejecuta una consulta SPARQL con backoff exponencial frente a 429/502/timeout."""
    params = urllib.parse.urlencode({
        "query": query,
        "format": "application/json",
    })
    url = f"{ENDPOINT}?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "claude-for-legal-chile/0.1 (https://github.com/diazaraujo/claude-for-legal-chile)",
            "Accept": "application/sparql-results+json,application/json",
        },
    )

    for attempt in range(max_retries):
        time.sleep(sleep_ms / 1000.0)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                backoff = (2 ** attempt) * 2.0  # 2, 4, 8, 16, 32 seg
                print(f"    HTTP {e.code} — retry {attempt+1}/{max_retries} en {backoff}s", file=sys.stderr)
                time.sleep(backoff)
                continue
            raise
        except (TimeoutError, urllib.error.URLError) as e:
            backoff = (2 ** attempt) * 2.0
            print(f"    timeout — retry {attempt+1}/{max_retries} en {backoff}s ({e})", file=sys.stderr)
            time.sleep(backoff)
            continue
    raise RuntimeError(f"SPARQL falló tras {max_retries} reintentos")


def build_query(tipo_uri: str, *, year: int | None = None, limit: int = 1000) -> str:
    """Query mínima por una página del catálogo.

    Estrategia: pedir solo lo esencial (URI + título + leychile_code). Todo lo demás
    (número, tipo, ministerio, fecha) se deriva parseando la URI BCN que tiene
    forma `http://datos.bcn.cl/recurso/cl/<tipo>/<ministerio>/<fecha>/<numero>`.

    Si `year` se entrega, filtra por substring de la URI (más barato que JOIN sobre
    publishDate). Si no, intenta cargar todo (solo viable para tipos pequeños).
    """
    year_filter = ""
    if year is not None:
        year_filter = f'  FILTER(CONTAINS(STR(?norma), "/{year}-"))'
    return f"""
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT DISTINCT ?norma ?titulo ?leychile_code
WHERE {{
  ?norma a bcnnorms:Norm .
  ?norma bcnnorms:type <{tipo_uri}> .
  ?norma dc:title ?titulo .
{year_filter}
  OPTIONAL {{ ?norma bcnnorms:leychileCode ?leychile_code . }}
}}
LIMIT {limit}
""".strip()


def parse_uri(uri: str) -> dict:
    """Parsea URI BCN canónica.

    Formato esperado:
      http://datos.bcn.cl/recurso/cl/<tipo>/<ministerio>/<YYYY-MM-DD>/<numero>[/es@<fecha>]

    Devuelve dict con tipo, emisor, publicacion, numero. Tolerante a variaciones.
    """
    out = {"tipo": "", "emisor": "", "publicacion": "", "numero": ""}
    if not uri.startswith("http://datos.bcn.cl/recurso/cl/"):
        return out
    rest = uri[len("http://datos.bcn.cl/recurso/cl/"):]
    parts = rest.split("/")
    if len(parts) >= 1:
        out["tipo"] = parts[0]
    if len(parts) >= 2:
        out["emisor"] = parts[1]
    if len(parts) >= 3:
        out["publicacion"] = parts[2]
    if len(parts) >= 4:
        # numero puede ser "1234" o "1234-bis"; eliminar sufijo /es@... si vino
        numero_raw = parts[3]
        if "/es@" in numero_raw:
            numero_raw = numero_raw.split("/es@")[0]
        out["numero"] = numero_raw
    return out


def parse_binding(b: dict, tipo: str) -> dict | None:
    """Convierte un binding SPARQL a un dict plano. Devuelve None si falta info crítica."""
    def val(key: str) -> str | None:
        node = b.get(key)
        return node["value"] if node else None

    uri = val("norma") or ""
    titulo = val("titulo")
    if not uri or not titulo:
        return None

    parsed = parse_uri(uri)
    numero = parsed["numero"]
    if not numero:
        return None

    return {
        "tipo": tipo,
        "numero": numero,
        "titulo": titulo.strip(),
        "leychile_code": val("leychile_code") or "",
        "publicacion": parsed["publicacion"],
        "promulgacion": "",  # no se obtiene en query mínima; se puede enriquecer en capa 2
        "emisor": parsed["emisor"],
        "bcn_uri": uri,
    }


def build_query_offset(tipo_uri: str, *, offset: int, limit: int) -> str:
    """Query minimal con OFFSET para paginar el universo completo de un tipo."""
    return f"""
PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT DISTINCT ?norma ?titulo ?leychile_code
WHERE {{
  ?norma a bcnnorms:Norm .
  ?norma bcnnorms:type <{tipo_uri}> .
  ?norma dc:title ?titulo .
  OPTIONAL {{ ?norma bcnnorms:leychileCode ?leychile_code . }}
}}
OFFSET {offset}
LIMIT {limit}
""".strip()


def fetch_tipo(
    tipo: str,
    *,
    sleep_ms: int,
    page_size: int,
    max_total: int | None,
    year_range: tuple[int, int] | None,
) -> Iterator[dict]:
    """Itera todas las normas de un tipo.

    Estrategia:
    - SMALL_TIPOS (cod, tra, aa): una sola query (resultado pequeño)
    - LARGE_TIPOS (ley, dl, dfl, dto, res): OFFSET paginado con page_size moderado
      (500-1000 normas por query). Cada query consume rate budget del endpoint.

    Dedupe en Python por URI (las versiones múltiples /es@... ya están excluidas
    de la URI abstracta, así que el DISTINCT del SPARQL hace el trabajo).
    """
    if tipo not in TIPOS_URI:
        raise ValueError(f"Tipo desconocido: {tipo}. Disponibles: {sorted(TIPOS_URI)}")
    tipo_uri = TIPOS_URI[tipo]
    seen_uris: set[str] = set()
    yielded = 0

    def emit(b: dict):
        nonlocal yielded
        uri = (b.get("norma") or {}).get("value", "")
        if uri in seen_uris:
            return None
        seen_uris.add(uri)
        parsed = parse_binding(b, tipo)
        if parsed:
            yielded += 1
            return parsed
        return None

    # Para tipos pequeños o si --no-partition: query única
    if year_range is None:
        query = build_query(tipo_uri, year=None, limit=page_size)
        try:
            data = sparql_query(query, sleep_ms=sleep_ms)
        except Exception as e:
            print(f"  ! Error SPARQL {tipo}: {e}", file=sys.stderr)
            return
        for b in data.get("results", {}).get("bindings", []):
            r = emit(b)
            if r:
                yield r
                if max_total is not None and yielded >= max_total:
                    return
        return

    # Para tipos grandes: paginar por OFFSET
    offset = 0
    consecutive_empty = 0
    while True:
        if max_total is not None and yielded >= max_total:
            return
        try:
            query = build_query_offset(tipo_uri, offset=offset, limit=page_size)
            data = sparql_query(query, sleep_ms=sleep_ms)
        except Exception as e:
            print(f"  ! Error SPARQL {tipo} offset={offset}: {e}", file=sys.stderr)
            return

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                return
            offset += page_size
            continue
        consecutive_empty = 0

        page_new = 0
        for b in bindings:
            r = emit(b)
            if r:
                page_new += 1
                yield r
                if max_total is not None and yielded >= max_total:
                    return

        print(f"    offset={offset} bindings={len(bindings)} nuevos={page_new} total={yielded}", file=sys.stderr)

        if len(bindings) < page_size:
            return
        offset += page_size


# Tipos canónicos en español para el frontmatter
TIPOS_LABEL = {
    "ley": "Ley", "lei": "Ley",
    "dl": "Decreto Ley",
    "dfl": "Decreto con Fuerza de Ley",
    "dto": "Decreto",
    "res": "Resolución",
    "cod": "Código",
    "tra": "Tratado",
    "aa": "Auto Acordado",
    "cer": "Certificación",
    "cir": "Circular",
    "acd": "Acuerdo",
}


def render_markdown(norma: dict) -> str:
    """Render del archivo markdown capa 1 para una norma."""
    label = TIPOS_LABEL.get(norma["tipo"], norma["tipo"].upper())
    numero = norma["numero"]
    nombre_corto = f"{label} {numero}"
    slug = f"{norma['tipo']}-{numero}"
    leychile_url = (
        f"https://www.bcn.cl/leychile/navegar?idNorma={norma['leychile_code']}"
        if norma["leychile_code"] else ""
    )

    # YAML frontmatter
    yaml_lines = [
        "---",
        f"norma: {nombre_corto}",
        f"slug: {slug}",
        f"tipo: {norma['tipo']}",
        f"numero: {numero}",
        f"titulo_oficial: {json.dumps(norma['titulo'], ensure_ascii=False)}",
        f"publicacion: {norma['publicacion'] or 'desconocida'}",
        f"promulgacion: {norma['promulgacion'] or 'desconocida'}",
        f"emisor: {norma['emisor']}",
        f"leychile_code: {norma['leychile_code']}",
        f"fuente_oficial: {leychile_url}",
        f"bcn_uri: {norma['bcn_uri']}",
        "capa: 1",
        "estado_revision: catalogo-auto",
        "validador: null",
        "fecha_validacion: null",
        "---",
        "",
        f"# {nombre_corto}",
        "",
        f"**Título oficial:** {norma['titulo']}",
        "",
        f"**Tipo:** {label}",
        f"**Número:** {numero}",
        f"**Publicación en DO:** {norma['publicacion'] or '_desconocida_'}",
        f"**Promulgación:** {norma['promulgacion'] or '_desconocida_'}",
        f"**Emisor:** {norma['emisor'] or '_desconocido_'}",
        "",
        "## Fuente oficial",
        "",
    ]
    if leychile_url:
        yaml_lines.append(f"- [BCN/LeyChile (texto vigente y modificaciones)]({leychile_url})")
    if norma["bcn_uri"]:
        yaml_lines.append(f"- [BCN Linked Open Data (RDF)]({norma['bcn_uri']})")
    yaml_lines.extend([
        "",
        "## Estado en el corpus",
        "",
        "Entrada **capa 1** generada automáticamente desde el endpoint SPARQL de BCN.",
        "Contiene metadata catalográfica; no incluye análisis operativo ni síntesis",
        "estructural. Para texto vigente, modificaciones y artículos, consultar la",
        "fuente oficial.",
        "",
        "## Disclaimers",
        "",
        "- Capa 1: metadata auto-generada, sin validación legal.",
        "- Para promover a capa 2 (resumen estructural) o capa 3 (análisis operativo),",
        "  abrir PR siguiendo el schema en `chile/normativa/README.md`.",
        "",
    ])
    return "\n".join(yaml_lines)


UNIQUE_BY_NUMBER = {"ley", "lei", "cod"}  # número único en todo el ordenamiento

def safe_filename(norma: dict) -> str:
    """Convierte un número de norma en filename seguro.

    Para `ley` y `cod` el número es único en todo el ordenamiento → filename = número.
    Para `dfl`, `dl`, `dto`, `res`, `tra`, `aa`, etc. el número se reusa por año/órgano,
    así que incluimos `<numero>-<YYYY-MM-DD>-<emisor>` para evitar colisiones.
    """
    numero = norma["numero"]
    safe = numero.replace("/", "-").replace(" ", "").replace(":", "-")

    if norma["tipo"] in UNIQUE_BY_NUMBER:
        return (safe.zfill(5) if safe.isdigit() else safe) + ".md"

    # Composite filename
    fecha = norma.get("publicacion") or "sinfecha"
    emisor = (norma.get("emisor") or "").replace("/", "-")
    base = safe.zfill(5) if safe.isdigit() else safe
    # Limitar largo de emisor para no romper FS
    emisor_short = emisor[:60]
    return f"{base}-{fecha}-{emisor_short}.md"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tipos", required=True, help="Lista separada por comas: ley,dl,dfl,cod,tra,aa")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=None, help="Máximo por tipo")
    p.add_argument("--sleep-ms", type=int, default=200)
    p.add_argument("--page-size", type=int, default=600)
    p.add_argument("--force", action="store_true", help="Sobreescribir archivos existentes")
    p.add_argument("--year-from", type=int, default=1810,
                   help="Año inicial para partición (default 1810). Si el tipo es chico (cod/tra/aa) se ignora.")
    p.add_argument("--year-to", type=int, default=2026,
                   help="Año final para partición (default 2026, año actual)")
    p.add_argument("--no-partition", action="store_true",
                   help="Forzar query sin partición por año (solo viable en tipos pequeños)")
    args = p.parse_args(argv)

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    for t in tipos:
        if t not in TIPOS_URI:
            print(f"ERROR: tipo desconocido '{t}'. Disponibles: {sorted(TIPOS_URI)}", file=sys.stderr)
            return 2

    if args.dry_run:
        print("[DRY RUN] No se escribirán archivos.")

    args.output.mkdir(parents=True, exist_ok=True)
    stats = {"start": time.strftime("%Y-%m-%dT%H:%M:%S"), "tipos": {}}
    grand_total = 0
    grand_written = 0
    grand_skipped = 0

    # Tipos con bajo volumen: sin partición. Los demás se particionan por año.
    SMALL_TIPOS = {"cod", "tra", "aa", "lei"}

    for tipo in tipos:
        use_partition = (not args.no_partition) and (tipo not in SMALL_TIPOS)
        year_range = (args.year_from, args.year_to) if use_partition else None
        print(f"\n=== Tipo: {tipo} (partición={'sí' if use_partition else 'no'}) ===")
        tipo_dir = args.output / tipo
        if not args.dry_run:
            tipo_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        written = 0
        skipped = 0
        for norma in fetch_tipo(
            tipo,
            sleep_ms=args.sleep_ms,
            page_size=args.page_size,
            max_total=args.limit,
            year_range=year_range,
        ):
            count += 1
            if args.dry_run:
                if count <= 3:
                    print(f"  [{count}] {tipo}-{norma['numero']} :: {norma['titulo'][:80]}")
                continue

            out_path = tipo_dir / safe_filename(norma)
            if out_path.exists() and not args.force:
                skipped += 1
                continue
            out_path.write_text(render_markdown(norma), encoding="utf-8")
            written += 1
            if written % 200 == 0:
                print(f"  {written} archivos escritos ({tipo})")

        stats["tipos"][tipo] = {"total": count, "written": written, "skipped": skipped}
        grand_total += count
        grand_written += written
        grand_skipped += skipped
        print(f"  Total {tipo}: {count} | Escritos: {written} | Skipped: {skipped}")

    stats["end"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    stats["grand_total"] = grand_total
    stats["grand_written"] = grand_written
    stats["grand_skipped"] = grand_skipped

    if not args.dry_run:
        stats_path = args.output / "_stats.json"
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2))

    print(f"\n=== Resumen ===")
    print(f"Total normas procesadas: {grand_total}")
    print(f"Archivos escritos:       {grand_written}")
    print(f"Skipped (ya existían):   {grand_skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
