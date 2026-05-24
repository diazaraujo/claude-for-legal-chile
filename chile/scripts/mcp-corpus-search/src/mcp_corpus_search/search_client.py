"""Cliente FTS5 sobre el corpus legal chileno.

Usa el índice SQLite construido por `chile/scripts/build-fts-index.py`.
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import struct
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .citation import Citation, from_path as cite_from_path

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "bge-m3"


def _leychile_code_from_path(path: str) -> int | None:
    """Extrae idNorma desde path .../leychile/{tipo}/{N}.xml.txt"""
    m = re.search(r"/leychile/[^/]+/(\d+)\.xml(\.txt)?$", path)
    return int(m.group(1)) if m else None

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
        self._norma_meta_cache: dict[int, dict] | None = None

    def _load_norma_meta(self, conn: sqlite3.Connection) -> dict[int, dict]:
        if self._norma_meta_cache is not None:
            return self._norma_meta_cache
        try:
            rows = conn.execute(
                "SELECT leychile_code, numero, tipo, titulo, derogado, "
                "es_modificadora, es_codigo FROM docs_norma"
            ).fetchall()
        except sqlite3.OperationalError:
            self._norma_meta_cache = {}
            return self._norma_meta_cache
        self._norma_meta_cache = {
            r[0]: {
                "numero": r[1], "tipo": r[2], "titulo": r[3],
                "derogado": r[4], "es_modificadora": bool(r[5]),
                "es_codigo": bool(r[6]),
            } for r in rows
        }
        return self._norma_meta_cache

    def search(
        self,
        query: str,
        source: str = "",
        sources: list[str] | None = None,
        year: str = "",
        year_from: str = "",
        year_to: str = "",
        exclude_sources: list[str] | None = None,
        exclude_modificadoras: bool = False,
        vigentes_only: bool = False,
        limit: int = 10,
        snippet_len: int = 240,
    ) -> list[SearchHit]:
        if not query.strip():
            return []
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            # If user wants vigencia filters, need JOIN to docs_norma.
            # Extract leychile_code from path: /leychile/{tipo}/{N}.xml.txt
            use_norma_filter = exclude_modificadoras or vigentes_only
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
            # Over-fetch 4x when filtering por vigencia para tener buffer.
            fetch_n = (limit * 4) if use_norma_filter else limit
            sql = (
                f"SELECT source, year, path, "
                f"snippet(docs, 3, '«', '»', '…', 32) as snip, "
                f"bm25(docs) as score "
                f"FROM docs WHERE {where} "
                f"ORDER BY bm25(docs) LIMIT ?"
            )
            params.append(fetch_n)
            rows = conn.execute(sql, params).fetchall()

            # Apply vigencia filter post-query (in Python — más simple que SQL).
            if use_norma_filter:
                norma_meta = self._load_norma_meta(conn)
                filtered = []
                for row in rows:
                    src, yr, path, snip, score = row
                    code = _leychile_code_from_path(path)
                    if code is None:
                        filtered.append(row)
                        continue
                    meta = norma_meta.get(code)
                    if meta is None:
                        filtered.append(row)
                        continue
                    if exclude_modificadoras and meta.get("es_modificadora"):
                        continue
                    if vigentes_only:
                        d = meta.get("derogado", "sin_dato")
                        if d not in ("no derogado", "sin_dato", "", None):
                            continue
                    filtered.append(row)
                    if len(filtered) >= limit:
                        break
                rows = filtered[:limit]
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

    def cite(self, path: str) -> Citation:
        """Genera cita formal desde el path."""
        return cite_from_path(path)

    def _ollama_embed(self, text: str, timeout: int = 60) -> list[float] | None:
        if len(text) > 8000:
            text = text[:8000]
        payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode()
        req = urllib.request.Request(
            OLLAMA_EMBED_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            embs = data.get("embeddings") or []
            return embs[0] if embs else None
        except Exception:
            return None

    def _get_embedding(
        self, path: str, compute_if_missing: bool = True
    ) -> list[float] | None:
        """Lee embedding del índice. Si no existe, lo computa via Ollama."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            row = conn.execute(
                "SELECT vec FROM embeddings WHERE path = ? AND model = ?",
                (path, EMBED_MODEL),
            ).fetchone()
        except sqlite3.OperationalError:
            conn.close()
            return None
        if row:
            blob = row[0]
            n = len(blob) // 4
            return list(struct.unpack(f"<{n}f", blob))
        conn.close()
        if not compute_if_missing:
            return None
        # Compute on-the-fly
        text = self.get_full_text(path, max_chars=8000)
        if not text or len(text) < 50:
            return None
        return self._ollama_embed(text)

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        s = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return s / (na * nb) if na and nb else 0.0

    def related(
        self,
        path: str,
        limit: int = 5,
        same_source_only: bool = False,
        min_score: float = 0.5,
    ) -> list[SearchHit]:
        """Encuentra los N documentos más similares al dado, vía embeddings
        bge-m3 (Ollama local). Compara contra embeddings ya indexados;
        si el embedding del query no existe, se computa on-the-fly.
        """
        q_emb = self._get_embedding(path, compute_if_missing=True)
        if not q_emb:
            return []
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        try:
            sql = (
                "SELECT e.path, d.source, d.year, e.vec "
                "FROM embeddings e JOIN docs d ON e.path = d.path "
                "WHERE e.model = ? AND e.path != ?"
            )
            params: list = [EMBED_MODEL, path]
            if same_source_only:
                # Detect source of query path
                q_src_row = conn.execute(
                    "SELECT source FROM docs WHERE path = ?", (path,)
                ).fetchone()
                if q_src_row:
                    sql += " AND d.source = ?"
                    params.append(q_src_row[0])
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()

        scored: list[tuple[float, str, str, str]] = []
        for p, src, yr, blob in rows:
            n = len(blob) // 4
            v = list(struct.unpack(f"<{n}f", blob))
            sim = self._cosine(q_emb, v)
            if sim >= min_score:
                scored.append((sim, p, src, yr))
        scored.sort(reverse=True, key=lambda x: x[0])

        results: list[SearchHit] = []
        for i, (sim, p, src, yr) in enumerate(scored[:limit], 1):
            snip = self.get_full_text(p, max_chars=240).strip()
            snip = re.sub(r"\s+", " ", snip)[:240]
            results.append(SearchHit(
                rank=i, source=src, year=yr or "",
                path=p, pdf_path=p.replace(".pdf.txt", ".pdf"),
                snippet=snip, score=sim,
            ))
        return results

    def embeddings_status(self) -> dict:
        """Reporta cobertura del índice de embeddings."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            try:
                total_emb = conn.execute(
                    "SELECT COUNT(*) FROM embeddings WHERE model = ?",
                    (EMBED_MODEL,)
                ).fetchone()[0]
                by_src = conn.execute(
                    "SELECT d.source, COUNT(*) FROM embeddings e "
                    "JOIN docs d ON e.path = d.path "
                    "WHERE e.model = ? "
                    "GROUP BY d.source ORDER BY 2 DESC",
                    (EMBED_MODEL,)
                ).fetchall()
            except sqlite3.OperationalError:
                return {"total": 0, "by_source": {}, "model": EMBED_MODEL,
                        "note": "tabla embeddings no existe — correr build-embeddings-index.py"}
            total_docs = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        finally:
            conn.close()
        return {
            "model": EMBED_MODEL,
            "total_embedded": total_emb,
            "total_docs": total_docs,
            "coverage_pct": round(100 * total_emb / max(total_docs, 1), 1),
            "by_source": dict(by_src),
        }
