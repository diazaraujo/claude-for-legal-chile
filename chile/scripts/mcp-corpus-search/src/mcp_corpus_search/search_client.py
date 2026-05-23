"""Cliente FTS5 sobre el corpus legal chileno.

Usa el índice SQLite construido por `chile/scripts/build-fts-index.py`.
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB = (
    Path(__file__).resolve().parents[5]
    / "chile/data/_index/corpus.fts.sqlite3"
)


@dataclass
class SearchHit:
    rank: int
    source: str
    year: str
    path: str
    pdf_path: str
    snippet: str
    score: float


class CorpusSearchClient:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Corpus FTS index no existe: {self.db_path}. "
                f"Correr 'python3 chile/scripts/build-fts-index.py' primero."
            )

    def search(
        self,
        query: str,
        source: str = "",
        sources: list[str] | None = None,
        year: str = "",
        year_from: str = "",
        year_to: str = "",
        exclude_sources: list[str] | None = None,
        limit: int = 10,
        snippet_len: int = 240,
    ) -> list[SearchHit]:
        if not query.strip():
            return []
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            where_clauses = ["docs MATCH ?"]
            params: list = [query]
            # source = single, sources = list (OR)
            if source:
                where_clauses.append("source = ?")
                params.append(source)
            elif sources:
                placeholders = ",".join("?" * len(sources))
                where_clauses.append(f"source IN ({placeholders})")
                params.extend(sources)
            if exclude_sources:
                placeholders = ",".join("?" * len(exclude_sources))
                where_clauses.append(f"source NOT IN ({placeholders})")
                params.extend(exclude_sources)
            # year = exact, year_from/year_to = range. Cast as INT for ordering.
            if year:
                where_clauses.append("year = ?")
                params.append(year)
            else:
                if year_from:
                    where_clauses.append(
                        "year != '' AND CAST(year AS INTEGER) >= ?"
                    )
                    params.append(int(year_from))
                if year_to:
                    where_clauses.append(
                        "year != '' AND CAST(year AS INTEGER) <= ?"
                    )
                    params.append(int(year_to))
            where = " AND ".join(where_clauses)
            sql = (
                f"SELECT source, year, path, "
                f"snippet(docs, 3, '«', '»', '…', 32) as snip, "
                f"bm25(docs) as score "
                f"FROM docs WHERE {where} "
                f"ORDER BY bm25(docs) LIMIT ?"
            )
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as e:
            conn.close()
            raise ValueError(f"Error en query FTS5: {e}") from e
        finally:
            try:
                conn.close()
            except Exception:
                pass

        results: list[SearchHit] = []
        for i, (src, yr, path, snip, score) in enumerate(rows, 1):
            snip_clean = re.sub(r"\s+", " ", snip).strip()
            if len(snip_clean) > snippet_len:
                snip_clean = snip_clean[:snippet_len] + "…"
            pdf_path = path.replace(".pdf.txt", ".pdf")
            results.append(SearchHit(
                rank=i, source=src, year=yr or "",
                path=path, pdf_path=pdf_path,
                snippet=snip_clean, score=float(score),
            ))
        return results

    def recent(
        self,
        source: str = "",
        sources: list[str] | None = None,
        year_from: str = "",
        limit: int = 10,
    ) -> list[SearchHit]:
        """Últimos N documentos por path (orden inverso). Útil para ver
        lo más reciente de una fuente sin query específica."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            where_clauses = ["1=1"]
            params: list = []
            if source:
                where_clauses.append("source = ?")
                params.append(source)
            elif sources:
                placeholders = ",".join("?" * len(sources))
                where_clauses.append(f"source IN ({placeholders})")
                params.extend(sources)
            if year_from:
                where_clauses.append(
                    "year != '' AND CAST(year AS INTEGER) >= ?"
                )
                params.append(int(year_from))
            where = " AND ".join(where_clauses)
            sql = (
                f"SELECT source, year, path, "
                f"substr(content, 1, 240) as snip "
                f"FROM docs WHERE {where} "
                f"ORDER BY year DESC, path DESC LIMIT ?"
            )
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        results: list[SearchHit] = []
        for i, (src, yr, path, snip) in enumerate(rows, 1):
            snip_clean = re.sub(r"\s+", " ", snip or "").strip()[:240]
            results.append(SearchHit(
                rank=i, source=src, year=yr or "",
                path=path, pdf_path=path.replace(".pdf.txt", ".pdf"),
                snippet=snip_clean, score=0.0,
            ))
        return results

    def list_sources(self) -> dict:
        """Listado de fuentes disponibles con conteos + año min/max."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            rows = conn.execute(
                "SELECT source, COUNT(*), "
                "MIN(CASE WHEN year != '' THEN year END), "
                "MAX(CASE WHEN year != '' THEN year END) "
                "FROM docs GROUP BY source ORDER BY 2 DESC"
            ).fetchall()
        finally:
            conn.close()
        return {
            "sources": [
                {"source": s, "n_docs": n, "year_min": ymin, "year_max": ymax}
                for s, n, ymin, ymax in rows
            ]
        }

    def stats(self) -> dict:
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            total = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            by_src = conn.execute(
                "SELECT source, COUNT(*) FROM docs GROUP BY source "
                "ORDER BY 2 DESC"
            ).fetchall()
        finally:
            conn.close()
        db_size = self.db_path.stat().st_size
        return {
            "total_docs": total,
            "by_source": dict(by_src),
            "index_size_bytes": db_size,
            "index_path": str(self.db_path),
        }

    def get_full_text(self, path: str, max_chars: int = 5000) -> str:
        """Lee texto completo de un .pdf.txt path. Returns hasta max_chars."""
        p = Path(path)
        if not p.exists():
            return ""
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[…truncado, total {len(content)} chars]"
        return content
