"""Cliente FNE Chile — Fiscalía Nacional Económica.

FNE expone WP REST API en https://www.fne.gob.cl/wp-json/wp/v2/

Categorías relevantes para corpus legal (catálogo verificado 2026-05-22):
  98: Defensa de la Libre Competencia (4655 posts)
 106: Jurisprudencia                  (2372)
 151: Dictamen                        (1298)
 159: Resoluciones de archivo         (1028)
 150: Resolucion                       (742)
 158: Resolución inicio de invest.     (463)
 197: Informes de Archivo / Término    (497)
 226: Res. Art 54 a)                   (281)
 119: Decisiones Comisiones Antimon.  (2039)
 120: Decisiones TDLC                  (229)
 152: Sentencia del TDLC               (185)
 149: Informes al TDLC                 (182)
 110: Sentencias Corte Suprema         (105)
 180: Requerimientos                   (104)

Total estimado posts categorías legales: ~14.500 (con overlap).

Conforme a no-inventar: el cliente no construye IDs sintéticos. Todos
los URLs y metadata vienen del WP REST API en respuesta a queries.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE = "https://www.fne.gob.cl/wp-json/wp/v2"

# Categorías legal-relevantes (no-noticias, no-eventos).
LEGAL_CATEGORIES = {
    98:  "Defensa de la Libre Competencia",
    106: "Jurisprudencia",
    151: "Dictamen",
    159: "Resoluciones de archivo",
    150: "Resolución",
    158: "Resolución inicio investigación de concentración",
    197: "Informe de Archivo/Término FNE",
    226: "Resolución Art 54 a)",
    119: "Decisiones Comisiones Antimonopolio",
    120: "Decisiones TDLC",
    152: "Sentencia del TDLC",
    149: "Informe al TDLC",
    110: "Sentencia Corte Suprema",
    180: "Requerimiento",
    227: "Informe aprobación FASE 1",
}


@dataclass
class FNEPost:
    post_id: int
    date: str
    slug: str
    title: str
    link: str
    categorias: list[int]
    excerpt: str
    content_html: str


class FNEClient:
    def __init__(self, rate_seconds: float = 0.3) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def _fetch_json(self, path: str) -> tuple[dict, dict]:
        url = f"{BASE}{path}"
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
            headers = dict(r.headers.items())
        return json.loads(body), headers

    def list_posts_by_category(
        self,
        category_id: int,
        page: int = 1,
        per_page: int = 100,
    ) -> tuple[list[FNEPost], int]:
        """Lista posts de una categoría con paginación. Returns
        (lista_de_posts, total_pages).
        """
        path = (
            f"/posts?categories={category_id}&page={page}&"
            f"per_page={per_page}&_fields=id,date,slug,title,link,"
            f"categories,excerpt,content"
        )
        data, headers = self._fetch_json(path)
        total_pages = int(headers.get("X-WP-TotalPages", "1"))
        posts: list[FNEPost] = []
        for p in data:
            posts.append(FNEPost(
                post_id=p["id"],
                date=p["date"],
                slug=p["slug"],
                title=p.get("title", {}).get("rendered", ""),
                link=p.get("link", ""),
                categorias=p.get("categories", []),
                excerpt=p.get("excerpt", {}).get("rendered", ""),
                content_html=p.get("content", {}).get("rendered", ""),
            ))
        return posts, total_pages

    def get_post(self, post_id: int) -> FNEPost | None:
        """Fetcha un post por ID."""
        try:
            data, _ = self._fetch_json(f"/posts/{post_id}")
        except urllib.error.HTTPError:
            return None
        return FNEPost(
            post_id=data["id"],
            date=data["date"],
            slug=data["slug"],
            title=data.get("title", {}).get("rendered", ""),
            link=data.get("link", ""),
            categorias=data.get("categories", []),
            excerpt=data.get("excerpt", {}).get("rendered", ""),
            content_html=data.get("content", {}).get("rendered", ""),
        )

    def extract_pdf_urls(self, html: str) -> list[str]:
        """Extrae URLs de PDFs embedded en el HTML del post.
        Útil porque FNE típicamente referencia el documento real
        (resolución, dictamen, sentencia) como link wp-content/uploads/.
        """
        import re
        urls = set()
        for m in re.finditer(r'href=["\']([^"\']+\.pdf)["\']', html, re.IGNORECASE):
            u = m.group(1)
            if u.startswith("//"):
                u = "https:" + u
            elif u.startswith("/"):
                u = "https://www.fne.gob.cl" + u
            urls.add(u)
        return sorted(urls)
