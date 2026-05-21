"""Cliente local del catálogo BCN indexado en SQLite.

Diseñado para servir queries rápidas desde el MCP sin hit a BCN. Si el
SQLite no está poblado, devuelve resultados vacíos sin error: el MCP
puede caer a `bcn_get_norma` (remoto) como fallback.

Conforme a [[feedback-no-inventar-ids-urls-referencias]]: nunca inventa
datos. Si el catálogo no tiene la norma, devuelve None.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path


# Por default busca en el repo. Override con env var.
DEFAULT_DB = (
    Path(__file__).resolve().parents[4]
    / "normativa/index/catalogo.sqlite3"
)


@dataclass
class NormaLocal:
    slug: str
    tipo: str
    numero: str | None
    titulo: str | None
    publicacion: str | None
    promulgacion: str | None
    organismo: str | None
    leychile_code: str | None
    bcn_uri: str | None
    capa: int
    md_path: str | None

    @property
    def fuente_oficial(self) -> str | None:
        if self.leychile_code:
            return f"https://www.bcn.cl/leychile/navegar?idNorma={self.leychile_code}"
        return None


@dataclass
class Relacion:
    src_uri: str
    rel: str
    dst_uri: str


class LocalCatalog:
    """Lectura-solo. Thread-safe via check_same_thread=False."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = os.environ.get("MCP_BCN_DB", DEFAULT_DB)
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def available(self) -> bool:
        return self.db_path.exists()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _row_to_norma(self, row: sqlite3.Row) -> NormaLocal:
        return NormaLocal(
            slug=row["slug"],
            tipo=row["tipo"],
            numero=row["numero"],
            titulo=row["titulo"],
            publicacion=row["publicacion"],
            promulgacion=row["promulgacion"],
            organismo=row["organismo"],
            leychile_code=row["leychile_code"],
            bcn_uri=row["bcn_uri"],
            capa=row["capa"] or 1,
            md_path=row["md_path"],
        )

    # ----- queries -----

    def lookup_by_slug(self, slug: str) -> NormaLocal | None:
        if not self.available:
            return None
        cur = self._connect().cursor()
        row = cur.execute(
            "SELECT * FROM normas WHERE slug = ?", (slug,)
        ).fetchone()
        return self._row_to_norma(row) if row else None

    def lookup_by_leychile_code(self, code: str) -> NormaLocal | None:
        if not self.available:
            return None
        cur = self._connect().cursor()
        row = cur.execute(
            "SELECT * FROM normas WHERE leychile_code = ? "
            "ORDER BY capa DESC LIMIT 1",
            (str(code),),
        ).fetchone()
        return self._row_to_norma(row) if row else None

    def lookup_by_numero(
        self, tipo: str, numero: str | int
    ) -> NormaLocal | None:
        if not self.available:
            return None
        cur = self._connect().cursor()
        # Preferir el de mayor capa (3 > 2 > 1) — más curado
        row = cur.execute(
            "SELECT * FROM normas WHERE tipo = ? AND numero = ? "
            "ORDER BY capa DESC LIMIT 1",
            (tipo, str(numero)),
        ).fetchone()
        return self._row_to_norma(row) if row else None

    def search(
        self, q: str, limit: int = 20, tipo: str | None = None
    ) -> list[NormaLocal]:
        if not self.available:
            return []
        cur = self._connect().cursor()
        like = f"%{q}%"
        if tipo:
            rows = cur.execute(
                "SELECT * FROM normas WHERE titulo LIKE ? AND tipo = ? "
                "ORDER BY capa DESC, publicacion DESC LIMIT ?",
                (like, tipo, limit),
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT * FROM normas WHERE titulo LIKE ? "
                "ORDER BY capa DESC, publicacion DESC LIMIT ?",
                (like, limit),
            ).fetchall()
        return [self._row_to_norma(r) for r in rows]

    def relaciones(
        self, bcn_uri: str, direction: str = "outgoing"
    ) -> list[Relacion]:
        if not self.available:
            return []
        cur = self._connect().cursor()
        if direction == "outgoing":
            rows = cur.execute(
                "SELECT src_uri, rel, dst_uri FROM relaciones "
                "WHERE src_uri = ?",
                (bcn_uri,),
            ).fetchall()
        elif direction == "incoming":
            rows = cur.execute(
                "SELECT src_uri, rel, dst_uri FROM relaciones "
                "WHERE dst_uri = ?",
                (bcn_uri,),
            ).fetchall()
        else:  # both
            rows = cur.execute(
                "SELECT src_uri, rel, dst_uri FROM relaciones "
                "WHERE src_uri = ? OR dst_uri = ?",
                (bcn_uri, bcn_uri),
            ).fetchall()
        return [Relacion(r["src_uri"], r["rel"], r["dst_uri"]) for r in rows]

    def stats(self) -> dict[str, int]:
        if not self.available:
            return {"available": 0}
        cur = self._connect().cursor()
        total = cur.execute("SELECT COUNT(*) FROM normas").fetchone()[0]
        edges = cur.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0]
        by_tipo = {
            row[0]: row[1]
            for row in cur.execute(
                "SELECT tipo, COUNT(*) FROM normas GROUP BY tipo"
            )
        }
        return {"total_normas": total, "total_edges": edges, "by_tipo": by_tipo}

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
