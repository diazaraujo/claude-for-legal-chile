"""Cliente Contraloría General de la República — dictámenes.

URL pattern descubierto:
  https://www.contraloria.cl/pdfbuscador/dictamenes/{NUMERO:06d}N{YY:02d}/html
  https://www.contraloria.cl/pdfbuscador/dictamenes/{NUMERO:06d}N{YY:02d}/pdf

Donde:
- NUMERO: número del dictamen, padded a 6 dígitos
- YY: año en 2 dígitos (10 = 2010)

Ejemplo: 066847N10 = dictamen 66.847 de 2010.

Conforme a no-inventar: solo construye URLs canónicas. NO descarga PDFs
(devuelve URL para que el cliente fetch).
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.contraloria.cl/pdfbuscador/dictamenes/"


def format_dictamen_id(numero: int, year: int) -> str:
    """Genera ID canonical: 066847N10 (6 dígitos número + N + 2 dígitos año)."""
    yy = year % 100
    return f"{numero:06d}N{yy:02d}"


@dataclass
class DictamenURLs:
    numero: int
    year: int
    dictamen_id: str
    html_url: str
    pdf_url: str


class CGRClient:
    def __init__(self, rate_seconds: float = 0.5) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def build_urls(self, numero: int, year: int) -> DictamenURLs:
        dictamen_id = format_dictamen_id(numero, year)
        return DictamenURLs(
            numero=numero, year=year, dictamen_id=dictamen_id,
            html_url=f"{BASE_URL}{dictamen_id}/html",
            pdf_url=f"{BASE_URL}{dictamen_id}/pdf",
        )

    def check_exists(self, numero: int, year: int) -> bool:
        """HEAD request al HTML para verificar existencia."""
        urls = self.build_urls(numero, year)
        self._rate_limit()
        req = urllib.request.Request(
            urls.html_url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status == 200
        except (urllib.error.HTTPError, Exception):
            return False
