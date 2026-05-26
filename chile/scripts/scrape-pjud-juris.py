#!/usr/bin/env python3
"""Scrape juris.pjud.cl — Solr-backed Buscador Unificado de Fallos.

Descubierto 2026-05-26: el endpoint `/busqueda/buscar_sentencias` retorna
Solr JSON con 90 fields por sentencia, INCLUYENDO:
  - texto_sentencia (fulltext)
  - cita_bibliografica
  - caratulado_s, rol_sup_s, era_sup_i, fec_sentencia_sup_dt
  - gls_sala_sup_s, gls_ministro_ss, gls_redactor_s, gls_relator_s
  - gls_tip_recurso_sup_s, resultado_recurso_sup_s
  - gls_titulonorma_ss, id_descriptor_ss
  - url_acceso_sentencia
  - TEXTO_ETIQUETADO_t (XML estructurado)

NO necesitamos bajar PDFs aparte.

Pagination: numero_filas_paginacion=100 + offset_paginacion=0,100,200,...
Throughput verificado: 100 docs / 12.6s = ~8 docs/s. CS (287k) ~9h single-thread.

Buscadores conocidos (id_buscador_activo):
  Corte_Suprema       → 528
  Corte_de_Apelaciones → (verificar)
  Laborales            → ...
  Penales              → ...
  Familia              → ...
  Cobranza             → ...
  Civiles              → ...

Output: 1 page.json.gz por petición:
  chile/data/pjud/{buscador}/page-{offset:08d}.json.gz

Idempotente: skip si archivo ya existe.
CSRF se refresca al inicio + cada 500 requests + después de cualquier 4xx/419.

Usage:
  python3 scrape-pjud-juris.py --buscador Corte_Suprema
  python3 scrape-pjud-juris.py --buscador Corte_Suprema --fec-desde 01-01-2026
  python3 scrape-pjud-juris.py --buscador Corte_Suprema --max 1000
"""
from __future__ import annotations
import argparse, gzip, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "chile/data/pjud"
BASE = "https://juris.pjud.cl"
BUSCADOR_URL_TEMPLATE = f"{BASE}/busqueda?{{buscador}}"
ENDPOINT = f"{BASE}/busqueda/buscar_sentencias"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)


class PjudSession:
    """Mantiene cookies + CSRF + id_buscador para un buscador específico."""

    def __init__(self, buscador: str):
        self.buscador = buscador  # e.g. "Corte_Suprema"
        self.cj = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self.csrf = ""
        self.id_buscador = 0
        self.refresh()

    def refresh(self) -> None:
        """Recarga página del buscador, extrae CSRF + id_buscador."""
        url = BUSCADOR_URL_TEMPLATE.format(buscador=self.buscador)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with self.opener.open(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
        m_csrf = re.search(r'csrf-token"\s+content="([^"]+)"', html)
        m_id = re.search(r'id_buscador_activo\s*=\s*(\d+)', html)
        if not m_csrf or not m_id:
            raise RuntimeError(f"No pude extraer CSRF/id_buscador de {url}")
        self.csrf = m_csrf.group(1)
        self.id_buscador = int(m_id.group(1))
        print(f"  [session] buscador={self.buscador} id={self.id_buscador} csrf={self.csrf[:12]}...", flush=True)

    def buscar(
        self, offset: int, filtros: dict, num_filas: int = 100,
        orden: str = "", timeout: int = 60,
    ) -> bytes:
        """POST a /buscar_sentencias. Returns raw response bytes."""
        body = urllib.parse.urlencode([
            ("_token", self.csrf),
            ("id_buscador", str(self.id_buscador)),
            ("filtros", json.dumps(filtros, ensure_ascii=False)),
            ("numero_filas_paginacion", str(num_filas)),
            ("offset_paginacion", str(offset)),
            ("orden", orden),
            ("personalizacion", "false"),
        ]).encode("utf-8")
        req = urllib.request.Request(
            ENDPOINT, data=body,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": BUSCADOR_URL_TEMPLATE.format(buscador=self.buscador),
                "Origin": BASE,
            },
        )
        with self.opener.open(req, timeout=timeout) as r:
            return r.read()


def empty_filtros() -> dict:
    """Filtros mínimo aceptados por handler Laravel + Solr.

    Nota empírica 2026-05-26: si se ponen fec_desde/fec_hasta el handler
    los manda mal a Solr (DD-MM-YYYY sin convertir → DateTimeParseException;
    YYYY-MM-DD → numFound=0). Solución: filtros={} y aprovechar orden
    default por fec_sentencia_sup_dt desc (reverse cronológica natural).
    """
    return {}


def scrape(
    buscador: str, fec_desde: str = "", fec_hasta: str = "",
    max_offset: int = 0, page_size: int = 100,
    rate: float = 0.5, output_root: Path = OUTPUT_ROOT,
) -> int:
    """Itera páginas hasta agotar resultados.

    Args:
      fec_desde/fec_hasta: formato DD-MM-YYYY (lo que espera el form web)
      max_offset: si >0, detenerse cuando offset >= max_offset
      page_size: docs por página
      rate: sleep entre requests
    """
    session = PjudSession(buscador)

    # Output dir
    sub = buscador
    if fec_desde or fec_hasta:
        sub = f"{buscador}/{fec_desde or 'inicio'}_{fec_hasta or 'fin'}"
    out_dir = output_root / sub
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[output] {out_dir}", flush=True)

    filtros = empty_filtros()
    if fec_desde: filtros["fec_desde"] = fec_desde
    if fec_hasta: filtros["fec_hasta"] = fec_hasta

    offset = 0
    consecutive_errors = 0
    total_written = 0
    total_skipped = 0
    num_found: int | None = None
    start = time.time()
    page_count = 0

    while True:
        out_path = out_dir / f"page-{offset:08d}.json.gz"
        if out_path.exists() and out_path.stat().st_size > 100:
            total_skipped += 1
            offset += page_size
            if max_offset > 0 and offset >= max_offset:
                break
            if num_found is not None and offset >= num_found:
                break
            continue

        page_count += 1
        try:
            raw = session.buscar(offset, filtros, num_filas=page_size)
        except urllib.error.HTTPError as e:
            if e.code in (419, 401, 403):  # CSRF expired or session
                print(f"  [{offset}] HTTP {e.code}, refresh session", flush=True)
                session.refresh()
                consecutive_errors += 1
                if consecutive_errors > 5:
                    print(f"  [{offset}] too many errors, abort", flush=True)
                    break
                time.sleep(2)
                continue
            print(f"  [{offset}] HTTP {e.code}: {e.reason}", flush=True)
            consecutive_errors += 1
            if consecutive_errors > 5: break
            time.sleep(5 * consecutive_errors)
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [{offset}] {type(e).__name__}: {e}", flush=True)
            consecutive_errors += 1
            if consecutive_errors > 5: break
            time.sleep(5 * consecutive_errors)
            continue

        # Validar JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"  [{offset}] JSON decode err: {e}", flush=True)
            consecutive_errors += 1
            if consecutive_errors > 5: break
            time.sleep(5)
            continue

        if "error" in data:
            print(f"  [{offset}] Solr error: {data.get('error', {}).get('msg', '?')}", flush=True)
            break

        if num_found is None:
            num_found = data.get("response", {}).get("numFound", 0)
            print(f"  [numFound] {num_found} sentencias en {buscador}", flush=True)

        docs = data.get("response", {}).get("docs", [])
        if not docs:
            print(f"  [{offset}] sin docs, fin", flush=True)
            break

        # Write
        tmp = out_path.with_suffix(".tmp")
        with gzip.open(tmp, "wb") as f:
            f.write(raw)
        tmp.rename(out_path)
        total_written += 1
        consecutive_errors = 0

        elapsed = time.time() - start
        rate_pages = page_count / elapsed if elapsed > 0 else 0
        eta = ((num_found - offset) / page_size) / rate_pages if rate_pages > 0 else 0
        if page_count % 10 == 0 or page_count == 1:
            print(
                f"  [{offset+page_size}/{num_found}] docs={len(docs)} "
                f"| pages={page_count} written={total_written} skipped={total_skipped} "
                f"| {rate_pages:.2f}page/s eta={eta/60:.0f}min",
                flush=True,
            )

        offset += page_size
        if max_offset > 0 and offset >= max_offset:
            print(f"  [{offset}] --max alcanzado", flush=True)
            break
        if num_found is not None and offset >= num_found:
            print(f"  [{offset}] llegó a numFound={num_found}", flush=True)
            break
        time.sleep(rate)

        # Refresh CSRF cada 500 pages como medida preventiva
        if page_count > 0 and page_count % 500 == 0:
            print(f"  [maintenance] refresh CSRF after {page_count} pages", flush=True)
            session.refresh()

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | offset_final={offset} "
          f"written={total_written} skipped={total_skipped}", flush=True)
    return total_written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buscador", default="Corte_Suprema",
                        help="Corte_Suprema | Corte_de_Apelaciones | Laborales "
                             "| Cobranza | Penales | Familia | Civiles")
    parser.add_argument("--fec-desde", default="",
                        help="DD-MM-YYYY (vacío = sin límite)")
    parser.add_argument("--fec-hasta", default="",
                        help="DD-MM-YYYY")
    parser.add_argument("--max", type=int, default=0,
                        help="max offset (0 = todo)")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--rate", type=float, default=0.5)
    args = parser.parse_args()

    return 0 if scrape(
        args.buscador,
        fec_desde=args.fec_desde, fec_hasta=args.fec_hasta,
        max_offset=args.max, page_size=args.page_size, rate=args.rate,
    ) >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
