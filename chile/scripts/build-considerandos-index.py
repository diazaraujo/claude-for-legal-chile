#!/usr/bin/env python3
"""Particiona texto de sentencias en CHUNKS por considerando.

Cada sentencia chilena se divide en considerandos numerados (PRIMERO,
SEGUNDO, ..., VIGÉSIMO PRIMERO, ...). Permite responder queries tipo
"qué sentencia tiene un considerando que dice X" con granularidad fina.

Patrones detectados:
  - "PRIMERO:" / "Primero:" / "PRIMERO.-"
  - "1°" / "1.-" / "1°.-"
  - "Considerando 1°:" / "Considerando primero:"

Tabla nueva:
  considerandos_chunks(id, doc_path, num_orden, num_label, content)
  Indexada FTS5 sobre content + UNINDEXED metadata.

Sources típicos: tc, tc-moderno, tdlc, tdpi, tribunales-ambientales,
y ahora también pjud (Corte Suprema etc.) cuando los integremos.

Usage:
  python3 build-considerandos-index.py --sources tc,tc-moderno --max 50
  python3 build-considerandos-index.py --sources tc,tdlc,tdpi
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"

# Patterns ordenados por prioridad. Cada match es inicio de un nuevo
# considerando. Usamos lookbehind + multiline.
# Ordinales completos hasta 30 (cubre 99% de sentencias TC/CS)
ORDINALES_PALABRA = [
    "primero", "segundo", "tercero", "cuarto", "quinto", "sexto", "séptimo",
    "octavo", "noveno", "décimo", "undécimo", "duodécimo",
    "decimotercero", "decimocuarto", "decimoquinto", "decimosexto",
    "decimoséptimo", "decimoctavo", "decimonoveno",
    "vigésimo", "vigesimoprimero", "vigesimosegundo", "vigesimotercero",
    "vigesimocuarto", "vigesimoquinto", "vigesimosexto",
    "trigésimo", "cuadragésimo", "quincuagésimo",
]
ORDINALES_RE = "|".join(ORDINALES_PALABRA + [o + "o" for o in ORDINALES_PALABRA])

# Patrones inicio de considerando:
#   PRIMERO: / PRIMERO.- / Primero:
#   1°. / 1°: / 1.-
#   CONSIDERANDO PRIMERO: / Considerando 1°:
PATTERN_CONSIDERANDO = re.compile(
    r"(?:^|<br\s*/?>|\n)\s*"  # inicio de línea, o tras <br/> del HTML
    r"(?:"
        r"(?:considerando[s]?|que\s+:?)\s*"  # opcional prefijo "Considerando"
    r")?"
    r"(?P<num>"
        rf"(?:{ORDINALES_RE})"  # palabra (PRIMERO, etc)
        r"|"
        r"(?:\d{1,3}\s*(?:°|º|\.))"  # número con sufijo (1°, 1°.-, 1.)
    r")"
    r"\s*[:\.\-]+\s+",  # separador : .- etc
    re.IGNORECASE | re.MULTILINE,
)


def split_considerandos(text: str) -> list[tuple[str, str]]:
    """Returns list of (num_label, content) tuples."""
    if not text or len(text) < 100:
        return []
    # Normalizar <br/> a \n para que multiline funcione
    norm = re.sub(r"<br\s*/?>", "\n", text)

    matches = list(PATTERN_CONSIDERANDO.finditer(norm))
    if len(matches) < 2:  # menos de 2 considerandos no vale la pena chunkear
        return []

    chunks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(norm)
        content = norm[start:end].strip()
        if len(content) < 30:
            continue
        # Truncar muy largos (>10k chars indica que no se detectó próximo)
        if len(content) > 10000:
            content = content[:10000]
        num_label = m.group("num").strip().upper()
        chunks.append((num_label, content))
    return chunks


def init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS considerandos_chunks USING fts5(
            doc_path UNINDEXED,
            source UNINDEXED,
            num_orden UNINDEXED,
            num_label UNINDEXED,
            content,
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS considerandos_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_path TEXT,
            source TEXT,
            num_orden INTEGER,
            num_label TEXT,
            chars INTEGER,
            mtime REAL,
            UNIQUE(doc_path, num_orden)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_consid_meta_doc "
        "ON considerandos_meta(doc_path)"
    )
    conn.commit()
    return conn


def index_doc(
    conn: sqlite3.Connection, doc_path: str, source: str, text: str, mtime: float,
) -> tuple[int, int]:
    """Returns (inserted, skipped)."""
    existing_orden = set(
        row[0] for row in conn.execute(
            "SELECT num_orden FROM considerandos_meta WHERE doc_path = ?",
            (doc_path,),
        )
    )
    chunks = split_considerandos(text)
    inserted, skipped = 0, 0
    for orden, (num_label, content) in enumerate(chunks, 1):
        if orden in existing_orden:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO considerandos_chunks("
            "doc_path, source, num_orden, num_label, content"
            ") VALUES (?, ?, ?, ?, ?)",
            (doc_path, source, orden, num_label, content),
        )
        conn.execute(
            "INSERT OR IGNORE INTO considerandos_meta("
            "doc_path, source, num_orden, num_label, chars, mtime"
            ") VALUES (?, ?, ?, ?, ?, ?)",
            (doc_path, source, orden, num_label, len(content), mtime),
        )
        inserted += 1
    return inserted, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--sources", default="tc,tc-moderno,tdlc,tdpi,tribunales-ambientales")
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    placeholders = ",".join("?" * len(sources))

    conn = init_db(Path(args.db))
    rows = conn.execute(
        f"SELECT d.path, d.source, dm.mtime FROM docs d "
        f"JOIN docs_meta dm ON d.path = dm.path "
        f"WHERE d.source IN ({placeholders}) "
        f"ORDER BY dm.mtime DESC",
        sources,
    ).fetchall()
    if args.max > 0:
        rows = rows[:args.max]
    print(f"Docs a procesar: {len(rows)} | sources={sources}", flush=True)

    start = time.time()
    n_docs, n_chunks, n_skip = 0, 0, 0
    for i, (path, source, mtime) in enumerate(rows, 1):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        ins, skp = index_doc(conn, path, source, text, mtime)
        n_chunks += ins
        n_skip += skp
        if ins > 0:
            n_docs += 1
        if i % 200 == 0 or i == len(rows):
            conn.commit()
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0
            avg_chunks = n_chunks / n_docs if n_docs else 0
            print(
                f"  [{i}/{len(rows)}] docs_con_consid={n_docs} "
                f"chunks={n_chunks} skip={n_skip} | "
                f"{rate:.0f}docs/s avg={avg_chunks:.1f}chunks/doc",
                flush=True,
            )
    conn.commit()

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | {n_docs} docs procesados, "
          f"{n_chunks} chunks nuevos, {n_skip} skip", flush=True)

    total_chunks = conn.execute(
        "SELECT COUNT(*) FROM considerandos_meta"
    ).fetchone()[0]
    avg_chars = conn.execute(
        "SELECT AVG(chars) FROM considerandos_meta"
    ).fetchone()[0] or 0
    print(f"\nÍndice total: {total_chunks} chunks "
          f"(avg {avg_chars:.0f} chars/chunk)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
