"""Cliente CMF Chile — Normas de Carácter General (NCG) + Circulares.

URL patterns descubiertos:
- NCG: https://www.cmfchile.cl/normativa/ncg_NNN_YYYY.pdf
- Circ: https://www.cmfchile.cl/normativa/cir_NNNN_YYYY.pdf

Consulta de listado completa en:
  https://www.cmfchile.cl/institucional/legislacion_normativa/normativa.php

Conforme a no-inventar-ids-urls-referencias: solo construye URLs
canónicas + verifica con HEAD.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.cmfchile.cl/normativa/"


@dataclass
class NormaURL:
    tipo: str  # "ncg" | "cir"
    numero: int
    year: int
    url: str
    available: bool | None = None
    pdf_size: int | None = None


class CMFClient:
    def __init__(self, rate_seconds: float = 0.5) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def build_url(self, tipo: str, numero: int, year: int) -> str:
        if tipo not in ("ncg", "cir"):
            raise ValueError(f"tipo debe ser 'ncg' o 'cir', no '{tipo}'")
        return f"{BASE_URL}{tipo}_{numero}_{year}.pdf"

    def get_norma_url(self, tipo: str, numero: int, year: int) -> NormaURL:
        url = self.build_url(tipo, numero, year)
        return NormaURL(tipo=tipo, numero=numero, year=year, url=url)

    def check_norma(self, tipo: str, numero: int, year: int) -> NormaURL:
        url = self.build_url(tipo, numero, year)
        self._rate_limit()
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                ctype = r.headers.get("Content-Type", "")
                length = int(r.headers.get("Content-Length", "0") or "0")
                if "pdf" in ctype.lower():
                    return NormaURL(
                        tipo=tipo, numero=numero, year=year, url=url,
                        available=True, pdf_size=length or None,
                    )
        except urllib.error.HTTPError:
            pass
        except Exception:
            pass
        return NormaURL(
            tipo=tipo, numero=numero, year=year, url=url,
            available=False,
        )

    def enumerate(
        self,
        tipo: str,
        from_year: int = 1990,
        to_year: int | None = None,
        from_numero: int = 1,
        to_numero: int = 3000,
        verify: bool = False,
    ) -> list[NormaURL]:
        """Enumera URLs candidatas CMF para tipo + rango años/números.

        Sin red por default (URLs sintéticas). verify=True hace HEAD a
        cada URL (costoso). Aplica principio 'toda la data'.

        NCG van ~1..600+, Circ van ~1..2400+. Total normas CMF
        históricas estimado ~5000.
        """
        import datetime
        if to_year is None:
            to_year = datetime.date.today().year
        results: list[NormaURL] = []
        for year in range(from_year, to_year + 1):
            for n in range(from_numero, to_numero + 1):
                if verify:
                    r = self.check_norma(tipo, n, year)
                    if r.available:
                        results.append(r)
                else:
                    results.append(self.get_norma_url(tipo, n, year))
        return results
