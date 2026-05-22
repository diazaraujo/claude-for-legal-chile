"""Cliente SERNAC Chile — Circulares y Dictámenes interpretativos.

URLs descubiertas:
- Listado circulares interpretativas:
  https://www.sernac.cl/portal/618/w3-propertyvalue-21072.html
- Listado dictámenes interpretativos:
  https://www.sernac.cl/portal/618/w3-propertyvalue-66262.html
- Items en el listado:
  https://www.sernac.cl/portal/618/w3-article-NNNNN.html (HTML)
  https://www.sernac.cl/portal/618/articles-NNNNN_archivo_01.pdf (PDF)

Patrón: scrape del listado completo (HTML estático con CMS Lotus
SmartForm) y devolución de links normalizados.

Conforme a no-inventar: solo lista artículos que SERNAC publica.
"""

from __future__ import annotations

import html as html_lib
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
LISTADOS = {
    "circulares": "https://www.sernac.cl/portal/618/w3-propertyvalue-21072.html",
    "dictamenes": "https://www.sernac.cl/portal/618/w3-propertyvalue-66262.html",
}

# Item HTML: <a href="w3-article-NNNNN.html"...>Title</a>
ITEM_RE = re.compile(
    r'<a[^>]*?href=["\']([^"\']*?w3-article-(\d+)\.html)["\'][^>]*>([^<]+)</a>',
    re.IGNORECASE,
)


@dataclass
class DocSERNAC:
    article_id: int
    title: str
    html_url: str
    pdf_url: str | None = None


class SERNACClient:
    def __init__(self, rate_seconds: float = 1.0) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def _fetch(self, url: str) -> str:
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")

    def list_documentos(self, tipo: str = "circulares") -> list[DocSERNAC]:
        """tipo: 'circulares' | 'dictamenes'."""
        if tipo not in LISTADOS:
            raise ValueError(f"tipo debe ser 'circulares' o 'dictamenes'")
        body = self._fetch(LISTADOS[tipo])
        results: list[DocSERNAC] = []
        seen: set[int] = set()
        for m in ITEM_RE.finditer(body):
            url_part = m.group(1)
            article_id = int(m.group(2))
            title = html_lib.unescape(m.group(3).strip())
            if article_id in seen or len(title) < 8:
                continue
            # Filtrar headers/menús (típicamente cortos o repetitivos)
            if title.lower() in (
                "ver más", "más información", "leer más",
                "contacto", "inicio", "nosotros", "noticias",
            ):
                continue
            seen.add(article_id)
            if not url_part.startswith("http"):
                url_part = (
                    "https://www.sernac.cl/portal/618/"
                    + url_part.lstrip("/")
                )
            pdf_url = (
                f"https://www.sernac.cl/portal/618/"
                f"articles-{article_id}_archivo_01.pdf"
            )
            results.append(DocSERNAC(
                article_id=article_id, title=title,
                html_url=url_part, pdf_url=pdf_url,
            ))
        return results
