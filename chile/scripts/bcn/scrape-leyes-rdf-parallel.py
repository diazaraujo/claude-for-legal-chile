#!/usr/bin/env python3
# std:input rango de números de ley (default 1..22000)
# std:output archivos en chile/normativa/catalogo/ley/NNNNN.md (paralelo)
# std:deps stdlib pura + concurrent.futures
"""
Versión paralela del scrape de catálogo Leyes.

Usa ThreadPoolExecutor (5-10 workers) para acelerar el scrape de 60h a
~3h. Cada worker mantiene rate-limit propio.

Conforme a regla 'no inventar IDs': solo guarda lo que el RDF oficial
devuelve. Si BCN no responde con leychileCode, NO se inventa.

Idempotente: skip de archivos existentes (override con --force).

Uso:
    python3 scrape-leyes-rdf-parallel.py --from 1 --to 22000 --workers 8
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_DIR = REPO_ROOT / "chile/normativa/catalogo/ley"

USER_AGENT = "claude-legal-chile/0.6 (unholster.com)"

LEYCHILE_CODE_RE = re.compile(r'<bcnnorms:leychileCode[^>]*>(\d+)<')
LABEL_RE = re.compile(r"<rdfs:label[^>]*>([^<]+)<")
PUBLISH_RE = re.compile(r'<bcnnorms:publishDate[^>]*>(\d{4}-\d{2}-\d{2})<')
PROMULG_RE = re.compile(r'<bcnnorms:promulgationDate[^>]*>(\d{4}-\d{2}-\d{2})<')
ORGANISMO_RE = re.compile(
    r'<bcnnorms:createdBy rdf:resource="[^"]*?/organismo/([^"]+)"'
)
BCN_URI_RE = re.compile(r'<bcnnorms:versionOf rdf:resource="([^"]+)"')

_write_lock = Lock()
_stats_lock = Lock()
_stats = {"found": 0, "not_found": 0, "errors": 0, "skipped": 0, "rate_limited": 0}


def parse_rdf(raw: str) -> dict | None:
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


def fetch_one(numero: int, timeout: int = 20, max_retries: int = 4) -> tuple[int, str | None, str]:
    """Devuelve (numero, raw_rdf, status) donde status in {'ok','404','429','err'}."""
    url = f"https://datos.bcn.cl/recurso/cl/ley/{numero}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rdf+xml"},
    )
    backoff = 2.0
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return numero, resp.read().decode("utf-8", errors="replace"), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return numero, None, "404"
            if e.code == 429 or e.code >= 500:
                time.sleep(backoff)
                backoff *= 2
                continue
            return numero, None, "err"
        except Exception:
            time.sleep(backoff)
            backoff *= 2
            continue
    return numero, None, "429"


def write_entry(numero: int, info: dict) -> None:
    titulo = info["label"].replace('"', '\\"')
    fm = (
        "---\n"
        f"norma: Ley {numero}\n"
        f"slug: ley-{numero}\n"
        "tipo: ley\n"
        f"numero: {numero}\n"
        f'titulo_oficial: "{titulo}"\n'
    )
    if info["publish_date"]:
        fm += f"publicacion: {info['publish_date']}\n"
    if info["promulgation_date"]:
        fm += f"promulgacion: {info['promulgation_date']}\n"
    if info["organismo"]:
        fm += f"emisor: {info['organismo']}\n"
    fm += (
        f"leychile_code: {info['leychile_code']}\n"
        f"fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma={info['leychile_code']}\n"
    )
    if info["bcn_uri"]:
        fm += f"bcn_uri: {info['bcn_uri']}\n"
    fm += (
        "capa: 1\n"
        "estado_revision: catalogo-bcn\n"
        "---\n\n"
        f"# LEY {numero}\n\n"
        f"**Título oficial:** {info['label']}\n"
    )

    path = CATALOG_DIR / f"{numero:05d}.md"
    with _write_lock:
        path.write_text(fm, encoding="utf-8")


def process_one(numero: int, force: bool) -> str:
    """Devuelve status string ('found', 'skipped', '404', 'error', '429')."""
    path = CATALOG_DIR / f"{numero:05d}.md"
    if path.exists() and not force:
        with _stats_lock:
            _stats["skipped"] += 1
        return "skipped"
    numero, raw, status = fetch_one(numero)
    if status == "404":
        with _stats_lock:
            _stats["not_found"] += 1
        return "404"
    if status == "429":
        with _stats_lock:
            _stats["rate_limited"] += 1
        return "429"
    if raw is None:
        with _stats_lock:
            _stats["errors"] += 1
        return "error"
    info = parse_rdf(raw)
    if not info or not info["leychile_code"]:
        with _stats_lock:
            _stats["errors"] += 1
        return "error"
    write_entry(numero, info)
    with _stats_lock:
        _stats["found"] += 1
    return "found"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Leyes BCN paralelo")
    parser.add_argument("--from", dest="start", type=int, default=1)
    parser.add_argument("--to", dest="end", type=int, default=22000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    total = args.end - args.start + 1
    existing = len(list(CATALOG_DIR.glob("*.md")))

    print(
        f"[INFO] Scrapeando Leyes {args.start}..{args.end} "
        f"workers={args.workers}, total={total}, ya existentes={existing}",
        flush=True,
    )

    start_ts = time.time()
    completed = 0
    report_every = 100

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_one, n, args.force): n
            for n in range(args.start, args.end + 1)
        }
        for fut in as_completed(futures):
            completed += 1
            if completed % report_every == 0:
                elapsed = time.time() - start_ts
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total - completed) / rate if rate > 0 else 0
                print(
                    f"[{completed}/{total}] found={_stats['found']} "
                    f"skip={_stats['skipped']} 404={_stats['not_found']} "
                    f"429={_stats['rate_limited']} err={_stats['errors']} "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start_ts
    print(f"\n[DONE] {elapsed:.0f}s")
    print(f"  Found + saved: {_stats['found']}")
    print(f"  Skipped (already existed): {_stats['skipped']}")
    print(f"  Not found (404): {_stats['not_found']}")
    print(f"  Errors: {_stats['errors']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
