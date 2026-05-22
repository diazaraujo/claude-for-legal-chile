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

    def _parse_page(self, body: str) -> list[HistoriaLey]:
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

    def list_page(self, page: int = 1) -> list[HistoriaLey]:
        """Lista historias de una página específica."""
        self._rate_limit()
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
        return self._parse_page(body)

    def list_all(self, max_pages: int = 1000) -> list[HistoriaLey]:
        """Intentaba enumerar paginando. NO funciona — el sitio devuelve
        siempre las 10 más recientes para cualquier ?page=N.

        Para enumeración completa real, usar enumerate_by_id_range(1, 8500)
        (history_id parecen secuenciales del 1 al ~8500 = más reciente
        2026-05).
        """
        all_results: list[HistoriaLey] = []
        seen_ids: set[int] = set()
        for page in range(1, max_pages + 1):
            page_results = self.list_page(page)
            if not page_results:
                break
            new = [h for h in page_results if h.history_id not in seen_ids]
            if not new:
                break
            for h in new:
                seen_ids.add(h.history_id)
                all_results.append(h)
        return all_results

    def enumerate_by_id_range(
        self, from_id: int = 1, to_id: int = 8500, check: bool = False
    ) -> list[HistoriaLey]:
        """Enumera secuencialmente history_id en rango [from_id, to_id].

        Aplica principio "toda la data" — history_id son ~secuenciales
        del 1 al ~8500 (más recientes en 2026-05).

        Si check=True, hace HEAD HTTP a cada ID para verificar
        existencia (costoso: 8500 requests con rate-limit).
        Si check=False, solo construye URLs (sin red).
        """
        results: list[HistoriaLey] = []
        for hid in range(from_id, to_id + 1):
            if check:
                if not self.check_historia(hid):
                    continue
            results.append(HistoriaLey(
                history_id=hid,
                title="",
                standard_url=f"{BASE_URL}nc/historia-de-la-ley/{hid}/",
                vista_expandida_url=(
                    f"{BASE_URL}historia-de-la-ley/vista-expandida/{hid}/"
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
