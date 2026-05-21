#!/usr/bin/env python3
# std:input rango de números de ley (default 1..22000)
# std:output archivos en chile/normativa/catalogo/ley/NNNNN.md con frontmatter capa 1
# std:deps stdlib pura
"""
Re-scrape capa 1 completo del catálogo de Leyes chilenas usando el
endpoint RDF de datos.bcn.cl.

Para cada número N en el rango:
1. GET https://datos.bcn.cl/recurso/cl/ley/{N} con Accept rdf+xml.
2. Si 200: parsear leychileCode, label, publishDate, organismo,
   promulgationDate.
3. Si 404: gap (norma no existe con ese número, skip).
4. Guardar en chile/normativa/catalogo/ley/{NNNNN}.md (padded a 5 dígitos)
   con frontmatter capa 1.
5. Idempotente: skip si el archivo ya existe (override con --force).

Conforme a regla de memoria 'no inventar IDs': solo guarda lo que el
RDF oficial devuelve. Si BCN no responde o el RDF no tiene el campo,
NO se inventa.

Rate limit: 0.5s entre requests por defecto (configurable).
Reportes parciales cada 50 iteraciones.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_DIR = REPO_ROOT / "chile/normativa/catalogo/ley"

USER_AGENT = "claude-legal-chile/0.6 (unholster.com)"

LEYCHILE_CODE_RE = re.compile(
    r'<bcnnorms:leychileCode[^>]*>(\d+)<'
)
LABEL_RE = re.compile(r"<rdfs:label[^>]*>([^<]+)<")
PUBLISH_RE = re.compile(
    r'<bcnnorms:publishDate[^>]*>(\d{4}-\d{2}-\d{2})<'
)
PROMULG_RE = re.compile(
    r'<bcnnorms:promulgationDate[^>]*>(\d{4}-\d{2}-\d{2})<'
)
ORGANISMO_RE = re.compile(
    r'<bcnnorms:createdBy rdf:resource="[^"]*?/organismo/([^"]+)"'
)
BCN_URI_RE = re.compile(
    r'<bcnnorms:versionOf rdf:resource="([^"]+)"'
)


def parse_rdf(raw: str) -> dict | None:
    """Extrae metadata del RDF/XML retornado por datos.bcn.cl."""
    m_code = LEYCHILE_CODE_RE.search(raw)
    if not m_code:
        return None
    m_label = LABEL_RE.search(raw)
    m_pub = PUBLISH_RE.search(raw)
    m_prom = PROMULG_RE.search(raw)
    m_org = ORGANISMO_RE.search(raw)
    m_uri = BCN_URI_RE.search(raw)
    return {
        "leychile_code": m_code.group(1),
        "label": m_label.group(1).strip() if m_label else "",
        "publish_date": m_pub.group(1) if m_pub else None,
        "promulgation_date": m_prom.group(1) if m_prom else None,
        "organismo": m_org.group(1) if m_org else None,
        "bcn_uri": m_uri.group(1) if m_uri else None,
    }


def fetch_ley(numero: int, timeout: int = 20) -> str | None:
    """Devuelve el RDF o None si 404 / error."""
    url = f"https://datos.bcn.cl/recurso/cl/ley/{numero}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rdf+xml",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None


def write_catalog_entry(numero: int, info: dict) -> Path:
    """Escribe el frontmatter capa 1 al archivo del catálogo."""
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    path = CATALOG_DIR / f"{numero:05d}.md"

    # Sanitizar título (escape de comillas)
    titulo = info["label"].replace('"', '\\"')

    frontmatter = (
        "---\n"
        f"norma: Ley {numero}\n"
        f"slug: ley-{numero}\n"
        "tipo: ley\n"
        f"numero: {numero}\n"
        f'titulo_oficial: "{titulo}"\n'
    )
    if info["publish_date"]:
        frontmatter += f"publicacion: {info['publish_date']}\n"
    if info["promulgation_date"]:
        frontmatter += f"promulgacion: {info['promulgation_date']}\n"
    if info["organismo"]:
        frontmatter += f"emisor: {info['organismo']}\n"
    frontmatter += (
        f"leychile_code: {info['leychile_code']}\n"
        f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={info['leychile_code']}\n"
    )
    if info["bcn_uri"]:
        frontmatter += f"bcn_uri: {info['bcn_uri']}\n"
    frontmatter += (
        "capa: 1\n"
        "estado_revision: catalogo-bcn\n"
        "---\n"
        "\n"
        f"# LEY {numero}\n"
        "\n"
        f"**Título oficial:** {info['label']}\n"
    )

    path.write_text(frontmatter, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape catálogo Leyes desde BCN RDF")
    parser.add_argument("--from", dest="start", type=int, default=1)
    parser.add_argument("--to", dest="end", type=int, default=22000)
    parser.add_argument(
        "--rate", type=float, default=0.5, help="Segundos entre requests"
    )
    parser.add_argument(
        "--force", action="store_true", help="Sobrescribir archivos existentes"
    )
    args = parser.parse_args()

    print(
        f"[INFO] Scrapeando Leyes {args.start}..{args.end} "
        f"(rate {args.rate}s, total {args.end - args.start + 1} requests)"
    )
    print(f"[INFO] Catálogo destino: {CATALOG_DIR}")
    if not args.force:
        existing = len(list(CATALOG_DIR.glob("*.md")))
        print(f"[INFO] {existing} archivos ya existentes (skip salvo --force)")

    start_ts = time.time()
    found = 0
    skipped = 0
    not_found = 0
    errors = 0

    for n in range(args.start, args.end + 1):
        # Idempotencia
        path = CATALOG_DIR / f"{n:05d}.md"
        if path.exists() and not args.force:
            skipped += 1
            continue

        raw = fetch_ley(n)
        if raw is None:
            not_found += 1
        else:
            info = parse_rdf(raw)
            if info and info["leychile_code"]:
                write_catalog_entry(n, info)
                found += 1
            else:
                errors += 1

        time.sleep(args.rate)

        # Reporte parcial cada 50
        if (n - args.start + 1) % 50 == 0:
            elapsed = time.time() - start_ts
            rate = (n - args.start + 1) / elapsed if elapsed > 0 else 0
            remain = (args.end - n) / rate if rate > 0 else 0
            print(
                f"[{n}/{args.end}] found={found} skip={skipped} "
                f"404={not_found} err={errors} elapsed={elapsed:.0f}s "
                f"eta={remain:.0f}s"
            )

    elapsed = time.time() - start_ts
    print(f"\n[DONE] {elapsed:.0f}s")
    print(f"  Found + saved: {found}")
    print(f"  Skipped (already existed): {skipped}")
    print(f"  Not found (404): {not_found}")
    print(f"  Errors: {errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
