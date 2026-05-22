"""Cliente del Diario Oficial chileno.

Scrapea la edición electrónica diaria. NO hay API pública —
construido sobre el HTML de:

  https://www.diariooficial.interior.gob.cl/edicionelectronica/

URL pattern:
  ?date=DD-MM-YYYY&edition=NNNNN

PDFs:
  publicaciones/YYYY/MM/DD/EDITION/01/{CVE-N}.pdf
  publicaciones/YYYY/MM/DD/sumarios/EDITION.pdf

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: solo persiste
lo que el sitio devuelve.
"""

from __future__ import annotations

import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.diariooficial.interior.gob.cl/edicionelectronica/"

CVE_RE = re.compile(r"CVE[-_](\d+)")
PUB_PDF_RE = re.compile(
    r'publicaciones/(\d{4}/\d{2}/\d{2})/(\d+)/(\d+)/(\d+)\.pdf'
)
# Publicación: <tr class="content"><td>TITULO</td><td><a href="...pdf"...>Ver PDF (CVE-N)</a>
ROW_RE = re.compile(
    r'<tr class="content">\s*<td>([^<]+)\s*<span[^>]*></span>\s*</td>\s*'
    r'<td><a[^>]*href="([^"]+\.pdf)"[^>]*>[^<]*\(CVE-(\d+)\)</a>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class Publicacion:
    cve: str
    title: str
    pdf_url: str
    edition: str
    date: str


class DiarioOficialClient:
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
            "CREATE TABLE IF NOT EXISTS edicion_html ("
            "edition TEXT, date TEXT, html TEXT, fetched_at INTEGER, "
            "PRIMARY KEY(edition))"
        )
        conn.commit()
        conn.close()

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def fetch_edition_html(self, date: str, edition: str,
                           force: bool = False) -> str:
        """date: DD-MM-YYYY, edition: NNNNN."""
        if self.cache_db and not force:
            conn = sqlite3.connect(str(self.cache_db))
            row = conn.execute(
                "SELECT html FROM edicion_html WHERE edition = ?", (edition,)
            ).fetchone()
            conn.close()
            if row:
                return row[0]

        self._rate_limit()
        url = f"{BASE_URL}index.php?date={date}&edition={edition}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")

        if self.cache_db:
            conn = sqlite3.connect(str(self.cache_db))
            conn.execute(
                "INSERT OR REPLACE INTO edicion_html VALUES (?, ?, ?, ?)",
                (edition, date, html, int(time.time())),
            )
            conn.commit()
            conn.close()
        return html

    def parse_publicaciones(self, html: str, edition: str,
                            date: str) -> list[Publicacion]:
        """Extrae lista de Publicaciones del HTML de la edición."""
        # Normalizar date a YYYY/MM/DD para construir URL
        if "-" in date and len(date) == 10:  # DD-MM-YYYY
            d, m, y = date.split("-")
            date_path = f"{y}/{m}/{d}"
        else:
            date_path = date.replace("-", "/")

        # Match rows: <tr class="content"><td>title</td><td><a href="pdf">Ver PDF (CVE-N)</a>
        publicaciones: list[Publicacion] = []
        seen: set[str] = set()
        for match in ROW_RE.finditer(html):
            title = match.group(1).strip()
            pdf_url = match.group(2).strip()
            cve = match.group(3)
            if cve in seen or not title:
                continue
            seen.add(cve)
            publicaciones.append(Publicacion(
                cve=cve, title=title, pdf_url=pdf_url,
                edition=edition, date=date,
            ))
        return publicaciones

    def list_today(self) -> tuple[str, str, list[Publicacion]]:
        """Edición de hoy. Devuelve (date, edition, publicaciones).

        Estrategia: pedir el index principal sin args para que devuelva
        la edición actual.
        """
        self._rate_limit()
        req = urllib.request.Request(BASE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
        # Buscar la edición y fecha actual
        date_m = re.search(r"date=(\d{2}-\d{2}-\d{4})", html)
        edition_m = re.search(r"edition=(\d+)", html)
        if not (date_m and edition_m):
            raise RuntimeError("No se pudo detectar edición actual")
        date = date_m.group(1)
        edition = edition_m.group(1)
        pubs = self.parse_publicaciones(html, edition, date)
        return date, edition, pubs

    def get_publicacion_pdf_url(
        self, cve: str, date: str, edition: str
    ) -> str:
        if "-" in date and len(date) == 10:
            d, m, y = date.split("-")
            date_path = f"{y}/{m}/{d}"
        else:
            date_path = date.replace("-", "/")
        return (
            f"{BASE_URL}publicaciones/{date_path}/"
            f"{edition}/01/{cve}.pdf"
        )

    def get_sumario_pdf_url(self, date: str, edition: str) -> str:
        if "-" in date and len(date) == 10:
            d, m, y = date.split("-")
            date_path = f"{y}/{m}/{d}"
        else:
            date_path = date.replace("-", "/")
        return f"{BASE_URL}publicaciones/{date_path}/sumarios/{edition}.pdf"

    def fetch_by_date(self, date: str) -> tuple[str, str, list[Publicacion]]:
        """date: DD-MM-YYYY. Resuelve la edición de ese día sin
        conocerla previamente. Devuelve (date, edition, publicaciones).
        """
        self._rate_limit()
        url = f"{BASE_URL}?date={date}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")

        edition_m = re.search(r"edition=(\d+)", html)
        if not edition_m:
            return date, "", []
        edition = edition_m.group(1)
        return date, edition, self.parse_publicaciones(html, edition, date)

    def enumerate_date_range(
        self, from_date: str, to_date: str
    ) -> list[tuple[str, str, list[Publicacion]]]:
        """Enumera todas las ediciones del Diario Oficial entre dos
        fechas (DD-MM-YYYY). Aplica principio 'toda la data' — recorre
        día por día.

        Skip fines de semana y festivos (no hay edición).
        """
        import datetime
        def parse(d: str) -> datetime.date:
            day, mon, yr = d.split("-")
            return datetime.date(int(yr), int(mon), int(day))

        start = parse(from_date)
        end = parse(to_date)
        if start > end:
            return []

        results: list[tuple[str, str, list[Publicacion]]] = []
        current = start
        while current <= end:
            # DO publica L-V; weekends sin edición
            if current.weekday() < 5:
                d_str = current.strftime("%d-%m-%Y")
                try:
                    date, edition, pubs = self.fetch_by_date(d_str)
                    if edition:
                        results.append((date, edition, pubs))
                except (urllib.error.HTTPError, urllib.error.URLError):
                    pass
            current += datetime.timedelta(days=1)
        return results
