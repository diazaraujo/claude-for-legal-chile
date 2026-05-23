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
        year: str = "",
        limit: int = 10,
        snippet_len: int = 240,
    ) -> list[SearchHit]:
        if not query.strip():
            return []
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            where_clauses = ["docs MATCH ?"]
            params: list = [query]
            if source:
                where_clauses.append("source = ?")
                params.append(source)
            if year:
                where_clauses.append("year = ?")
                params.append(year)
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
