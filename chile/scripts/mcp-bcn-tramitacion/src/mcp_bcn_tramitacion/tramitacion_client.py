"""Cliente BCN Historia de la Ley — tramitación legislativa.

URLs:
- Listado home: https://www.bcn.cl/historiadelaley/ (10 más recientes)
- Historia específica: bcn.cl/historiadelaley/nc/historia-de-la-ley/{ID}/
- Vista expandida: bcn.cl/historiadelaley/historia-de-la-ley/vista-expandida/{ID}/

NOTA: history_id es ID interno BCN, NO el número de la ley. Mapping
ley→history_id requiere navegación manual o consulta SPARQL del grafo.

Conforme a no-inventar: solo retorna IDs/URLs que BCN publica
literalmente. No infiere mappings.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.bcn.cl/historiadelaley/"

HISTORIA_RE = re.compile(
    r'<a[^>]*href="([^"]*historia-de-la-ley/(\d+)/?)"[^>]*>'
    r'(?:<span[^>]*>)?([^<]+)(?:</span>)?',
    re.IGNORECASE,
)


@dataclass
class HistoriaLey:
    history_id: int
    title: str
    standard_url: str  # nc/historia-de-la-ley/{id}/
    vista_expandida_url: str  # vista-expandida/{id}/
    fecha: str | None = None


class TramitacionClient:
    def __init__(self, rate_seconds: float = 1.0) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def build_urls(self, history_id: int) -> HistoriaLey:
        return HistoriaLey(
            history_id=history_id,
            title="",
            standard_url=f"{BASE_URL}nc/historia-de-la-ley/{history_id}/",
            vista_expandida_url=(
                f"{BASE_URL}historia-de-la-ley/vista-expandida/{history_id}/"
            ),
        )

    def list_recientes(self) -> list[HistoriaLey]:
        """Lista las historias más recientes (típicamente 10) de la home."""
        self._rate_limit()
        req = urllib.request.Request(BASE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")

        results: list[HistoriaLey] = []
        seen: set[int] = set()
        for m in HISTORIA_RE.finditer(body):
            history_id = int(m.group(2))
            title = m.group(3).strip()
            if history_id in seen or not title or len(title) < 5:
                continue
            seen.add(history_id)
            results.append(HistoriaLey(
                history_id=history_id,
                title=title,
                standard_url=f"{BASE_URL}nc/historia-de-la-ley/{history_id}/",
                vista_expandida_url=(
                    f"{BASE_URL}historia-de-la-ley/vista-expandida/{history_id}/"
                ),
            ))
        return results

    def check_historia(self, history_id: int) -> bool:
        """HEAD request — verifica que existe la historia con ese ID."""
        urls = self.build_urls(history_id)
        self._rate_limit()
        req = urllib.request.Request(
            urls.standard_url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status == 200
        except (urllib.error.HTTPError, Exception):
            return False
