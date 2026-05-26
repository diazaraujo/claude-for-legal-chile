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
        rerank: bool = False,
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
        # Si rerank=True, traer 4x para que Haiku ordene
        keep_n = limit * 4 if rerank else limit
        for i, (src, yr, path, snip, score) in enumerate(rows[:keep_n], 1):
            snip_clean = re.sub(r"\s+", " ", snip).strip()
            if len(snip_clean) > snippet_len:
                snip_clean = snip_clean[:snippet_len] + "…"
            pdf_path = path.replace(".pdf.txt", ".pdf")
            results.append(SearchHit(
                rank=i, source=src, year=yr or "",
                path=path, pdf_path=pdf_path,
                snippet=snip_clean, score=float(score),
            ))
        if rerank and len(results) > 1:
            results = self.rerank_with_haiku(query, results, top_k=limit)
        return results[:limit]

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

    def expand_query(
        self,
        natural_query: str,
        max_terms: int = 8,
        model: str = "claude-haiku-4-5-20251001",
    ) -> dict:
        """Reformula query natural a términos legales chilenos precisos.

        Usa Claude Haiku para traducir lenguaje coloquial → keywords
        técnicos. Ej:
          'puede despedir embarazada' → ['fuero maternal', 'despido
          embarazada', 'artículo 174', 'causal despido']
          'que pasa si chocan mi auto sin licencia' → ['daños emergente',
          'lucro cesante', 'culpa', 'Ley 18.290', 'responsabilidad civil']

        Returns: dict con keys 'fts_query' (string FTS5 lista a usar),
        'terms' (list expandida), 'rationale' (explicación corta).

        Requiere ANTHROPIC_API_KEY. Costo ~$0.0001 por expansion.
        """
        if not natural_query.strip():
            return {"fts_query": "", "terms": [], "rationale": "query vacía"}
        try:
            from anthropic import Anthropic
        except ImportError:
            return {"fts_query": natural_query, "terms": [natural_query],
                    "rationale": "anthropic SDK no disponible"}
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return {"fts_query": natural_query, "terms": [natural_query],
                    "rationale": "ANTHROPIC_API_KEY no seteado"}

        prompt = (
            f"Query del usuario (lenguaje natural): {natural_query!r}\n\n"
            f"Reformula a términos legales chilenos para búsqueda FTS5 sobre "
            f"corpus de leyes/sentencias/dictámenes. Identifica:\n"
            f"- Términos técnicos legales\n"
            f"- Números de ley o artículo si son obvios\n"
            f"- Sinónimos relevantes en jerga jurídica chilena\n\n"
            f"Responde SOLO un JSON con shape exacta:\n"
            f'{{"fts_query": "term1 OR term2 OR \\"frase exacta\\"", '
            f'"terms": ["term1","term2"], "rationale": "explicación 1 línea"}}\n\n'
            f"Máx {max_terms} términos. FTS5 syntax (OR, NEAR, frases entre comillas)."
        )
        try:
            client = Anthropic()
            resp = client.messages.create(
                model=model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
        except Exception as e:
            return {"fts_query": natural_query, "terms": [natural_query],
                    "rationale": f"err Haiku: {type(e).__name__}"}

        # Parse JSON output (Haiku puede agregar prosa antes/después)
        import json as _json
        m = re.search(r"\{[^{}]*\"fts_query\"[^{}]*\}", text, re.DOTALL)
        if m:
            try:
                data = _json.loads(m.group(0))
                if "fts_query" in data:
                    return {
                        "fts_query": data.get("fts_query", natural_query),
                        "terms": data.get("terms", []),
                        "rationale": data.get("rationale", ""),
                    }
            except _json.JSONDecodeError:
                pass
        # Fallback
        return {"fts_query": natural_query, "terms": [natural_query],
                "rationale": f"parse_failed: {text[:100]}"}

    def rerank_with_haiku(
        self,
        query: str,
        hits: list["SearchHit"],
        top_k: int = 5,
        model: str = "claude-haiku-4-5-20251001",
    ) -> list["SearchHit"]:
        """Re-rankea hits con Claude Haiku.

        Toma los top-N de BM25 + sus snippets, le pide a Haiku que
        ordene por relevancia semántica real al query. Retorna top-K.
        Requiere ANTHROPIC_API_KEY en env.

        Costo aprox: input ~500 tokens (query + N snippets) × $0.25/1M
                     output ~50 tokens (lista de IDs ordenados) × $1.25/1M
                     = ~$0.0002 por rerank — negligible.
        """
        if not hits or len(hits) <= 1:
            return hits[:top_k]
        try:
            from anthropic import Anthropic
        except ImportError:
            return hits[:top_k]
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return hits[:top_k]

        # Build prompt: enumerated snippets
        items = []
        for i, h in enumerate(hits):
            cite_label = ""
            try:
                from .citation import from_path
                cite_label = from_path(h.path).citation
            except Exception:
                pass
            items.append(
                f"[{i+1}] {cite_label or h.source}: {h.snippet[:300]}"
            )
        prompt = (
            f"Query del usuario: {query!r}\n\n"
            f"Tienes {len(hits)} documentos candidatos (rankeados por BM25):\n\n"
            + "\n\n".join(items)
            + f"\n\nReordéna los top-{top_k} más relevantes SEMÁNTICAMENTE para "
            f"esa query. Responde SÓLO con los índices separados por coma, "
            f"sin explicación. Ej: '3,1,7,2,5'"
        )
        try:
            client = Anthropic()
            resp = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
        except Exception:
            return hits[:top_k]

        # Parse índices "3,1,7,2,5"
        try:
            indices = [int(x.strip()) - 1 for x in re.split(r"[,;\s]+", text) if x.strip().isdigit()]
        except Exception:
            return hits[:top_k]

        # Reorder + dedupe + cap
        seen = set()
        result: list[SearchHit] = []
        for idx in indices:
            if 0 <= idx < len(hits) and idx not in seen:
                seen.add(idx)
                # Re-rank: assign new rank + bump score to reflect order
                h = hits[idx]
                result.append(SearchHit(
                    rank=len(result) + 1, source=h.source, year=h.year,
                    path=h.path, pdf_path=h.pdf_path,
                    snippet=h.snippet, score=h.score,
                ))
            if len(result) >= top_k:
                break
        # Si Haiku no devolvió suficientes, completar con orden BM25 original
        for i, h in enumerate(hits):
            if i not in seen and len(result) < top_k:
                seen.add(i)
                result.append(h)
        return result

    def search_articulos(
        self, query: str,
        leychile_code: int | None = None,
        articulo_num: str = "",
        limit: int = 10,
        snippet_len: int = 240,
    ) -> list[dict]:
        """Búsqueda por ARTÍCULO específico (no por doc completo).
        Útil para queries tipo 'art. 161 código del trabajo causales'.

        - query: texto FTS5 (puede estar vacío si filter es por num/code)
        - leychile_code: filtrar a artículos de un idNorma específico
        - articulo_num: filtrar a un número (ej. "161", "1 bis")
        Returns: list de hits con doc_path, articulo_num, seccion, snippet, score.
        """
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            where = []
            params: list = []
            if query.strip():
                where.append("articulos MATCH ?")
                params.append(query)
            if leychile_code is not None:
                where.append("leychile_code = ?")
                params.append(leychile_code)
            if articulo_num:
                where.append("articulo_num = ?")
                params.append(articulo_num)
            if not where:
                return []
            order_by = "bm25(articulos)" if query.strip() else "rowid"
            sql = (
                f"SELECT doc_path, leychile_code, articulo_num, seccion, "
                f"snippet(articulos, 4, '«', '»', '…', 32) as snip, "
                f"{order_by if query.strip() else '0'} as score "
                f"FROM articulos WHERE {' AND '.join(where)} "
                f"ORDER BY {order_by} LIMIT ?"
            )
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        results = []
        for path, code, art_num, seccion, snip, score in rows:
            clean = re.sub(r"\s+", " ", snip).strip()[:snippet_len]
            results.append({
                "doc_path": path, "leychile_code": code,
                "articulo_num": art_num or "(sin número)",
                "seccion": seccion or "",
                "snippet": clean, "score": float(score),
            })
        return results

    def verify_quote(
        self, text: str, path: str, fuzzy: bool = True,
        context_chars: int = 200,
    ) -> dict:
        """Confirma que `text` aparece literalmente en el doc.

        - fuzzy=True: normaliza whitespace + case-insensitive antes de comparar
          (resiliente a errores OCR tipo doble espacio, saltos línea).
        - Returns: dict con found (bool), position (int o -1),
          context_before/after (str), normalized_match (str si fuzzy).

        Uso anti-hallucination: tras `corpus_search` retornar un hit,
        Claude puede llamar verify_quote para confirmar que la frase
        que va a citar existe textualmente en el doc."""
        p = Path(path)
        if not p.exists():
            return {"found": False, "error": "path no existe", "position": -1}
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"found": False, "error": str(e), "position": -1}

        if not text.strip():
            return {"found": False, "error": "text vacío", "position": -1}

        # Exact match first
        idx = content.find(text)
        if idx >= 0:
            return {
                "found": True, "position": idx,
                "match_type": "exact",
                "context_before": content[max(0, idx - context_chars):idx],
                "context_after": content[idx + len(text):idx + len(text) + context_chars],
                "normalized_match": text,
            }

        if not fuzzy:
            return {"found": False, "position": -1, "match_type": "exact_failed"}

        # Fuzzy: normalize whitespace + case
        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", s).strip().lower()

        norm_text = norm(text)
        norm_content = norm(content)
        idx = norm_content.find(norm_text)
        if idx >= 0:
            # Map back to original position (approximate)
            # Find a unique substring of the normalized match in original
            sample = re.escape(text[:50])
            sample_pattern = re.sub(r"\\\\\s", r"\\s+", sample)
            m = re.search(sample_pattern, content, re.IGNORECASE)
            orig_idx = m.start() if m else idx
            orig_end = orig_idx + len(text)
            return {
                "found": True, "position": orig_idx,
                "match_type": "fuzzy",
                "context_before": content[max(0, orig_idx - context_chars):orig_idx],
                "context_after": content[orig_end:orig_end + context_chars],
                "normalized_match": norm_text[:200],
            }

        return {"found": False, "position": -1, "match_type": "not_found"}

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
