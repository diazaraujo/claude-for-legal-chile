"""Cliente Dirección del Trabajo Chile — dictámenes (ORDs).

DT no tiene URL pattern por número de dictamen. En su lugar, usa CMS
con IDs internos (w3-article-NNNNN.html). El buscador acepta POST a:

  http://www.dt.gob.cl/legislacion/1624/w3-propertyvalue-22762.html

Con campos:
- palabrasand: texto requerido (todas las palabras)
- palabrasexactas: frase exacta
- titulo_hl1: búsqueda en título
- rango1_pnid_2294 / rango2_pnid_2294: fechas desde/hasta

Devuelve HTML con resultados — links tipo `w3-article-NNNNN.html`.

Conforme a no-inventar: solo retorna IDs/URLs que DT devuelve en
respuesta a la búsqueda. Sin scraping de contenido del dictamen.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
SEARCH_URL = "http://www.dt.gob.cl/legislacion/1624/w3-propertyvalue-22762.html"
ARTICLE_RE = re.compile(
    r'<a[^>]*?href=["\']([^"\']*?w3-article-(\d+)\.html)["\'][^>]*>([^<]+)</a>',
    re.IGNORECASE,
)
# Match solo dentro de resultados reales (h3 titulo aid-N)
REAL_RESULT_RE = re.compile(
    r'<h3 class="titulo aid-(\d+)[^"]*"[^>]*>\s*'
    r'<a\s+href=["\']([^"\']*?w3-article-\d+\.html)["\']'
    r'[^>]*?title=["\']([^"\']+)["\']',
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class DictamenDT:
    article_id: int
    url: str
    title: str


class DTClient:
    def __init__(self, rate_seconds: float = 1.0) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def search(
        self,
        query: str = "",
        exact: bool = False,
        title_only: bool = False,
        since: str = "",
        until: str = "",
        timeout: int = 45,
    ) -> list[DictamenDT]:
        """Busca dictámenes DT.

        - query: texto a buscar
        - exact: True para frase exacta; False para "todas las palabras"
        - title_only: limitar a título
        - since/until: rango YYYY-MM-DD (formato DT: depende — pasar tal cual)
        """
        # Allow empty query if date range provided

        data_dict: dict[str, str] = {
            "palabrasand": "" if (exact or title_only) else query,
            "palabrasexactas": query if exact else "",
            "titulo_hl1": query if title_only else "",
            "rango1_pnid_2294": since,
            "rango2_pnid_2294": until,
            "enviar": "Buscar",
        }
        data = urllib.parse.urlencode(data_dict).encode("utf-8")
        self._rate_limit()
        req = urllib.request.Request(
            SEARCH_URL, data=data, headers={"User-Agent": USER_AGENT},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, TimeoutError, OSError):
            return []

        seen: set[int] = set()
        results: list[DictamenDT] = []
        # Match solo h3 titulo aid (resultados reales, no navegación)
        for match in REAL_RESULT_RE.finditer(body):
            article_id = int(match.group(1))
            url_part = match.group(2)
            title = match.group(3).strip()
            if article_id in seen:
                continue
            seen.add(article_id)
            if not url_part.startswith("http"):
                if url_part.startswith("/"):
                    url_part = f"http://www.dt.gob.cl{url_part}"
                else:
                    url_part = (
                        f"http://www.dt.gob.cl/legislacion/1624/{url_part}"
                    )
            results.append(DictamenDT(
                article_id=article_id, url=url_part, title=title,
            ))
        return results

    def build_url(self, article_id: int) -> str:
        return (
            f"http://www.dt.gob.cl/legislacion/1624/"
            f"w3-article-{article_id}.html"
        )

    def list_by_date_range(
        self, since: str, until: str
    ) -> list[DictamenDT]:
        """Lista dictámenes DT en rango de fechas (YYYY-MM-DD).
        Sin palabra clave — devuelve TODO en ese rango.
        """
        return self.search(query="", since=since, until=until)

    def list_all_by_year(self, year: int) -> list[DictamenDT]:
        """1 query por año con rango fecha completo. El form DT pagina
        agrupado por mes — devuelve todos los del año en una sola
        respuesta (~40-60 dictámenes/año típico).
        """
        return self.list_by_date_range(f"{year}-01-01", f"{year}-12-31")
