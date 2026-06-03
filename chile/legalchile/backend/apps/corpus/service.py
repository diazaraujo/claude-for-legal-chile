"""Búsqueda sobre el corpus jurídico chileno (índices FTS5 SQLite ya construidos
por el pipeline en chile/data/_index/). Solo lectura — NO mueve los 367GB de data.
Path configurable vía settings.CORPUS_INDEX_DIR / env CORPUS_INDEX_DIR.
"""
import re
import sqlite3
from pathlib import Path

from django.conf import settings

_INDEX = {"new-sources": "new-sources.fts.sqlite3", "corpus": "corpus.fts.sqlite3"}


def _conn(db_name: str) -> sqlite3.Connection:
    p = Path(settings.CORPUS_INDEX_DIR) / db_name
    if not p.exists():
        raise FileNotFoundError(f"Índice no encontrado: {p}")
    return sqlite3.connect(f"file:{p}?immutable=1", uri=True, timeout=30)


def _fts_query(q: str) -> str:
    # tokens → frase FTS5 entre comillas (evita errores de sintaxis del usuario)
    toks = [t for t in re.findall(r"[\wáéíóúñ]+", q.lower()) if len(t) > 1]
    return " ".join(f'"{t}"' for t in toks)


def search(q: str, limit: int = 20, source: str = "new-sources") -> list[dict]:
    db = _INDEX.get(source, _INDEX["new-sources"])
    fq = _fts_query(q)
    if not fq:
        return []
    con = _conn(db)
    try:
        rows = con.execute(
            "SELECT path, snippet(docs, 1, '«', '»', '…', 16) AS snip "
            "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (fq, min(limit, 100)),
        ).fetchall()
        return [{"path": r[0], "snippet": r[1]} for r in rows]
    finally:
        con.close()


def stats() -> dict:
    out = {}
    for key, db in _INDEX.items():
        try:
            con = _conn(db)
            try:
                n = con.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            finally:
                con.close()
            out[key] = n
        except FileNotFoundError:
            out[key] = None
    return {"indices": out}
