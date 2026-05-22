"""Cliente del Tribunal Constitucional de Chile.

Acceso a sentencias TC vía URL pública por ROL/ID:
- Legacy (IDs ≤ ~12000): descargar_sentencia3.php?id=ID → PDF directo
- Modernas (≥ 13000): publicadas en www2.tribunalconstitucional.cl/
  wp-content/uploads/YYYY/MM/STC_Rol_N__NNNN-YY_*.pdf

El frontend principal (tramitacion.tcchile.cl) es JSF (postbacks) — no
scrapeable directo. Pero el descargador directo `descargar_sentencia3.php`
funciona sin captcha ni sesión.

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: solo devuelve
URLs que TC publica, sin inferencia.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"

DESCARGA_LEGACY = "https://www.tribunalconstitucional.cl/descargar_sentencia3.php?id={id}"
WWW2_BASE = "https://www2.tribunalconstitucional.cl/wp-content/uploads/"


@dataclass
class SentenciaURL:
    rol_id: int
    url: str
    type: str  # "legacy_pdf" | "wp_modern" | "unknown"
    pdf_size: int | None = None


class TCClient:
    def __init__(self, rate_seconds: float = 0.5) -> None:
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def try_legacy_url(self, rol_id: int) -> SentenciaURL | None:
        """Intenta descargar via legacy endpoint. Devuelve None si no es PDF."""
        url = DESCARGA_LEGACY.format(id=rol_id)
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                ctype = r.headers.get("Content-Type", "")
                length = int(r.headers.get("Content-Length", "0") or "0")
                if "pdf" in ctype.lower():
                    return SentenciaURL(
                        rol_id=rol_id, url=url, type="legacy_pdf",
                        pdf_size=length or None,
                    )
                return None
        except urllib.error.HTTPError:
            return None
        except Exception:
            return None

    def build_legacy_url(self, rol_id: int) -> str:
        """Sin red — solo construye la URL canónica del descargador."""
        return DESCARGA_LEGACY.format(id=rol_id)

    def enumerate_legacy_range(
        self, from_id: int = 1, to_id: int = 12000, verify: bool = False
    ) -> list[SentenciaURL]:
        """Enumera TODOS los rol_id en rango [from_id, to_id].

        Aplica principio 'toda la data' (Antonio 2026-05-22). TC legacy
        IDs van 1..~12000. IDs modernos (>13000) migrados a www2.

        verify=False default: solo construye URLs (instantáneo).
        verify=True: HEAD a cada URL (hasta 12k requests).
        """
        results: list[SentenciaURL] = []
        for rid in range(from_id, to_id + 1):
            if verify:
                r = self.try_legacy_url(rid)
                if r is not None:
                    results.append(r)
            else:
                results.append(SentenciaURL(
                    rol_id=rid, url=self.build_legacy_url(rid),
                    type="legacy_pdf",
                ))
        return results
