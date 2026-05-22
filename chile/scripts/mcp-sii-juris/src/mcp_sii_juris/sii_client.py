"""Cliente del SII Chile — circulares, oficios, resoluciones.

URLs:
- Circulares: https://www.sii.cl/normativa_legislacion/circulares/YYYY/indcirYYYY.htm
- PDFs: https://www.sii.cl/normativa_legislacion/circulares/YYYY/circuNN.pdf
- Estructura HTML: <h5><a href='circuNN.pdf'>Circular N° NN del FECHA</a></h5>
                   <p>RESUMEN</p>

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: solo persiste
lo que SII devuelve.
"""

from __future__ import annotations

import html as html_lib
import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.sii.cl/normativa_legislacion/circulares/"

CIRCULAR_RE = re.compile(
    r"<h5[^>]*><a\s+href='circu(\d+)\.pdf'[^>]*>([^<]+)</a></h5>\s*"
    r"<p[^>]*>([^<]+)</p>",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class Circular:
    number: int
    year: int
    title: str
    summary: str
    pdf_url: str


class SIIJurisClient:
    def __init__(self, cache_db: Path | None = None,
                 rate_seconds: float = 1.0) -> None:
        self.cache_db = cache_db
        self.rate_seconds = rate_seconds
        self._last_request = 0.0
        if cache_db:
            cache_db.parent.mkdir(parents=True, exist_ok=True)
            self._init_cache()

    def _init_cache(self) -> None:
        conn = sqlite3.connect(str(self.cache_db))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS indice_html ("
            "year INTEGER PRIMARY KEY, html TEXT, fetched_at INTEGER)"
        )
        conn.commit()
        conn.close()

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def fetch_indice_year(self, year: int, force: bool = False) -> str:
        if self.cache_db and not force:
            conn = sqlite3.connect(str(self.cache_db))
            row = conn.execute(
                "SELECT html FROM indice_html WHERE year = ?", (year,)
            ).fetchone()
            conn.close()
            if row:
                return row[0]

        self._rate_limit()
        url = f"{BASE_URL}{year}/indcir{year}.htm"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")

        if self.cache_db:
            conn = sqlite3.connect(str(self.cache_db))
            conn.execute(
                "INSERT OR REPLACE INTO indice_html VALUES (?, ?, ?)",
                (year, html, int(time.time())),
            )
            conn.commit()
            conn.close()
        return html

    def parse_circulares(self, html: str, year: int) -> list[Circular]:
        circulares: list[Circular] = []
        seen: set[int] = set()
        for match in CIRCULAR_RE.finditer(html):
            num = int(match.group(1))
            title = html_lib.unescape(match.group(2).strip())
            summary = html_lib.unescape(match.group(3).strip())
            if num in seen:
                continue
            seen.add(num)
            circulares.append(Circular(
                number=num,
                year=year,
                title=title,
                summary=summary,
                pdf_url=f"{BASE_URL}{year}/circu{num}.pdf",
            ))
        return sorted(circulares, key=lambda c: c.number)

    def list_circulares(self, year: int) -> list[Circular]:
        html = self.fetch_indice_year(year)
        return self.parse_circulares(html, year)

    def get_circular_pdf_url(self, year: int, number: int) -> str:
        return f"{BASE_URL}{year}/circu{number}.pdf"

    def search_circulares(self, query: str, year: int) -> list[Circular]:
        """Búsqueda LIKE en title + summary del año."""
        circulares = self.list_circulares(year)
        q = query.lower()
        return [
            c for c in circulares
            if q in c.title.lower() or q in c.summary.lower()
        ]
