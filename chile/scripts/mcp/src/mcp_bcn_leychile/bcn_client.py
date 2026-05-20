"""Cliente HTTP de BCN/LeyChile con caching SQLite + rate limiting."""

from __future__ import annotations

import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

USER_AGENT = "claude-legal-chile-mcp/0.1 (unholster.com)"
BCN_BASE = "https://www.leychile.cl/Consulta"
BCN_NAVEGAR = "https://www.bcn.cl/leychile/navegar"
RATE_LIMIT_SECONDS = 1.0  # mínimo entre requests
DEFAULT_TIMEOUT = 30
CACHE_DEFAULT_PATH = Path.home() / ".cache" / "mcp-bcn-leychile" / "cache.db"

NS = {"lc": "http://www.leychile.cl/esquemas"}


@dataclass
class NormaMetadata:
    """Metadata básica de una norma BCN."""

    id_norma: str
    tipo: Optional[str]
    numero: Optional[str]
    titulo: Optional[str]
    fecha_publicacion: Optional[str]
    organismo: Optional[str]
    vigencia: Optional[str]
    url_consulta: str


@dataclass
class EstructuraParte:
    """Parte estructural de una norma (artículo, título, libro, etc.)."""

    tipo_parte: str
    numero: Optional[str]
    titulo: Optional[str]
    texto: str
    hijos: list["EstructuraParte"]


class BCNClient:
    """Cliente con caching local + rate limiting respetuoso."""

    def __init__(
        self,
        cache_path: Path | None = None,
        rate_limit_seconds: float = RATE_LIMIT_SECONDS,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.cache_path = cache_path or CACHE_DEFAULT_PATH
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit_seconds
        self.timeout = timeout
        self._last_request_ts = 0.0
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS xml_cache (
                    id_norma TEXT PRIMARY KEY,
                    xml_content TEXT NOT NULL,
                    fetched_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    id_norma TEXT PRIMARY KEY,
                    tipo TEXT,
                    numero TEXT,
                    titulo TEXT,
                    fecha_publicacion TEXT,
                    organismo TEXT,
                    vigencia TEXT,
                    fetched_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _throttle(self) -> None:
        """Asegura RATE_LIMIT_SECONDS entre requests."""
        elapsed = time.time() - self._last_request_ts
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_ts = time.time()

    def _fetch_url(self, url: str) -> bytes:
        """HTTP GET con throttling + UA."""
        self._throttle()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def _ttl_seconds_xml(self) -> int:
        return 7 * 24 * 3600  # 7 días

    def _cached_xml(self, id_norma: str) -> Optional[str]:
        conn = sqlite3.connect(self.cache_path)
        try:
            cur = conn.execute(
                "SELECT xml_content, fetched_at FROM xml_cache WHERE id_norma = ?",
                (id_norma,),
            )
            row = cur.fetchone()
            if not row:
                return None
            xml_content, fetched_at = row
            if time.time() - fetched_at > self._ttl_seconds_xml():
                return None  # expirado
            return xml_content
        finally:
            conn.close()

    def _cache_xml(self, id_norma: str, xml_content: str) -> None:
        conn = sqlite3.connect(self.cache_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO xml_cache (id_norma, xml_content, fetched_at)
                VALUES (?, ?, ?)
                """,
                (id_norma, xml_content, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

    def fetch_xml(self, id_norma: str, force_refresh: bool = False) -> str:
        """Recupera el XML estructurado de una norma desde BCN.

        Args:
            id_norma: ID numérico BCN (ej. "1075210" para Ley 21.400).
            force_refresh: ignora cache si True.

        Returns:
            XML como string.

        Raises:
            urllib.error.HTTPError, urllib.error.URLError si BCN no responde.
        """
        if not force_refresh:
            cached = self._cached_xml(id_norma)
            if cached:
                return cached

        url = f"{BCN_BASE}/obtxml?opt=7&idNorma={urllib.parse.quote(id_norma)}"
        raw = self._fetch_url(url)
        xml_content = raw.decode("utf-8")

        # Cache only if response looks like valid XML
        if xml_content.strip().startswith("<?xml") or xml_content.strip().startswith(
            "<Norma"
        ):
            self._cache_xml(id_norma, xml_content)

        return xml_content

    def parse_metadata(self, xml_content: str) -> NormaMetadata:
        """Extrae metadata del XML."""
        root = ET.fromstring(xml_content)

        def find_text(path: str) -> Optional[str]:
            el = root.find(path, NS)
            if el is None or el.text is None:
                return None
            return el.text.strip()

        # Identificadores varían según versión del XML BCN
        id_norma = find_text("lc:Identificador/lc:IdNorma") or ""
        tipo = find_text("lc:Identificador/lc:TipoNorma")
        numero = find_text("lc:Identificador/lc:Numero")
        titulo = find_text("lc:Identificador/lc:Titulo")
        fecha = find_text("lc:Identificador/lc:FechaPublicacion")
        organismo = find_text("lc:Identificador/lc:Organismo")
        vigencia = find_text("lc:Identificador/lc:Vigencia") or "vigente"

        url = f"{BCN_NAVEGAR}?idNorma={id_norma}"

        return NormaMetadata(
            id_norma=id_norma,
            tipo=tipo,
            numero=numero,
            titulo=titulo,
            fecha_publicacion=fecha,
            organismo=organismo,
            vigencia=vigencia,
            url_consulta=url,
        )

    def parse_estructura(self, xml_content: str) -> list[EstructuraParte]:
        """Parsea la estructura jerárquica (libro/título/parte/artículo)."""
        root = ET.fromstring(xml_content)
        contenedor = root.find("lc:EstructurasFuncionales", NS)
        if contenedor is None:
            return []

        def walk(el: ET.Element) -> EstructuraParte:
            tipo_parte = el.get("tipoParte", "Parte")
            numero = el.findtext("lc:NumeroParte", default=None, namespaces=NS)
            titulo = el.findtext("lc:TituloParte", default=None, namespaces=NS)
            texto_el = el.find("lc:Texto", NS)
            texto = (
                "".join(texto_el.itertext()).strip() if texto_el is not None else ""
            )
            hijos = [
                walk(child)
                for child in el.findall("lc:EstructuraFuncional", NS)
            ]
            return EstructuraParte(
                tipo_parte=tipo_parte,
                numero=numero,
                titulo=titulo,
                texto=texto,
                hijos=hijos,
            )

        return [walk(child) for child in contenedor.findall("lc:EstructuraFuncional", NS)]

    def check_vigencia(self, id_norma: str) -> dict:
        """Verifica si una norma está vigente al día de hoy.

        Returns:
            dict con id_norma, vigente (bool), fecha_consulta, fuente.
        """
        try:
            xml = self.fetch_xml(id_norma)
            meta = self.parse_metadata(xml)
            return {
                "id_norma": id_norma,
                "titulo": meta.titulo,
                "vigencia_declarada": meta.vigencia,
                "vigente": (meta.vigencia or "").lower().startswith("vigente"),
                "fecha_consulta": time.strftime("%Y-%m-%d"),
                "fuente": meta.url_consulta,
            }
        except (urllib.error.URLError, ET.ParseError) as e:
            return {
                "id_norma": id_norma,
                "vigente": None,
                "error": f"No se pudo verificar contra BCN: {type(e).__name__}",
                "fecha_consulta": time.strftime("%Y-%m-%d"),
            }
