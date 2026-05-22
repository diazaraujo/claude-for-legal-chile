"""Cliente TDLC — Tribunal Defensa Libre Competencia.

API REST de WordPress en tdlc.cl:
  /wp-json/wp/v2/tdlc-sentencias
  /wp-json/wp/v2/rol-de-causa-sent
  /wp-json/wp/v2/numero-de-sentencia
  /wp-json/wp/v2/tdlc-resoluciones (otros tipos: ern, ac, sent, inf, icg)

Custom post type 'tdlc-sentencias' devuelve:
- id, slug, title, content (HTML), link
- numero-de-sentencia, rol-de-causa-sent, ano-sent, tipo-sent,
  conducta-sent, industria-sent

Conforme a no-inventar: solo retorna datos de la API.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_API = "https://www.tdlc.cl/wp-json/wp/v2/"

PDF_LINK_RE = re.compile(r'href="([^"]+\.pdf)"')


@dataclass
class SentenciaTDLC:
    id: int
    slug: str
    title: str
    link: str
    date: str
    numero_sentencia: list[int]
    rol_causa: list[int]
    pdf_urls: list[str]


class TDLCClient:
    def __init__(self, rate_seconds: float = 0.5) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def _get(self, path: str, params: dict | None = None) -> object:
        url = BASE_API + path.lstrip("/")
        if params:
            url += "?" + urllib.parse.urlencode(params)
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def _parse(self, item: dict) -> SentenciaTDLC:
        title = item.get("title", {}).get("rendered", "")
        content = item.get("content", {}).get("rendered", "")
        pdfs = PDF_LINK_RE.findall(content)
        return SentenciaTDLC(
            id=int(item.get("id", 0)),
            slug=item.get("slug", ""),
            title=title,
            link=item.get("link", ""),
            date=item.get("date", ""),
            numero_sentencia=item.get("numero-de-sentencia", []) or [],
            rol_causa=item.get("rol-de-causa-sent", []) or [],
            pdf_urls=pdfs,
        )

    def list_sentencias(
        self, per_page: int = 20, page: int = 1, search: str | None = None
    ) -> list[SentenciaTDLC]:
        params: dict = {"per_page": min(per_page, 100), "page": page}
        if search:
            params["search"] = search
        try:
            items = self._get("tdlc-sentencias", params)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return []
            raise
        if not isinstance(items, list):
            return []
        return [self._parse(it) for it in items]

    def get_sentencia(self, sentencia_id: int) -> SentenciaTDLC | None:
        try:
            item = self._get(f"tdlc-sentencias/{sentencia_id}")
        except urllib.error.HTTPError:
            return None
        if not isinstance(item, dict):
            return None
        return self._parse(item)
