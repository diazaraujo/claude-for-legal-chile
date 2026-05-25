#!/usr/bin/env python3
"""Indexa artículos individuales de los XMLs LeyChile en FTS5.

Tabla `articulos` paralela a `docs`:
- Cada <EstructuraFuncional> = 1 chunk (típicamente 1 artículo)
- Schema: leychile_code, articulo_num, titulo_seccion, content
- FTS5 para search específico por artículo
- Sirve para queries tipo "art. 161 Código del Trabajo causales"

Idempotente: skip si articulo ya en la tabla.
"""
from __future__ import annotations
import argparse, re, sqlite3, sys
import xml.etree.ElementTree as ET
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
LEYCHILE_DIR = _REPO_ROOT / "chile/data/leychile"
DB_PATH = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"

NS = "{http://www.leychile.cl/esquemas}"
ART_RE = re.compile(r"^\s*Art[íi]?culo\s+(\d+[ºo°]?(?:\s*bis|\s*ter|\s*quater)?)", re.IGNORECASE)
TITULO_RE = re.compile(r"^\s*(T[íi]tulo|Cap[íi]tulo|Libro|Pre[a-z]*mbulo)\b", re.IGNORECASE)


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    # FTS5 sobre articulos: content text, metadata UNINDEXED
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS articulos USING fts5(
            doc_path UNINDEXED,
            leychile_code UNINDEXED,
            articulo_num UNINDEXED,
            seccion UNINDEXED,
            content,
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articulos_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_path TEXT,
            leychile_code INTEGER,
            articulo_num TEXT,
            seccion TEXT,
            chars INTEGER,
            mtime REAL,
            UNIQUE(doc_path, articulo_num)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_art_code ON articulos_meta(leychile_code)"
    )
    conn.commit()
    return conn


def extract_articulos(xml_path: Path) -> list[dict]:
    """Returns list of dicts: {articulo_num, seccion, content}.
    Cada <EstructuraFuncional> es un chunk independiente."""
    try:
        tree = ET.parse(str(xml_path))
    except ET.ParseError:
        return []
    root = tree.getroot()
    blocks = root.findall(f".//{NS}EstructuraFuncional")
    results: list[dict] = []
    current_seccion = ""
    for ef in blocks:
        texto_el = ef.find(f".//{NS}Texto")
        if texto_el is None:
            continue
        text = "".join(texto_el.itertext()).strip()
        if not text or len(text) < 20:
            continue

        # Detectar tipo: titulo seccional vs artículo
        first_line = text.split("\n", 1)[0].strip()
        m_titulo = TITULO_RE.match(first_line)
        if m_titulo and len(text) < 200:
            # Es sección/título — actualizar context, no indexar
            current_seccion = text.replace("\n", " — ").strip()[:200]
            continue

        # Detectar número artículo
        m_art = ART_RE.match(first_line)
        articulo_num = m_art.group(1).strip() if m_art else ""
        # Normalizar (1º → 1, 1° → 1)
        articulo_num_norm = re.sub(r"[ºo°]$", "", articulo_num).strip()

        results.append({
            "articulo_num": articulo_num_norm,
            "seccion": current_seccion,
            "content": text,
        })
    return results


def index_file(conn: sqlite3.Connection, xml_path: Path) -> tuple[int, int]:
    """Returns (n_inserted, n_skipped)."""
    m = re.search(r"/leychile/[^/]+/(\d+)\.xml$", str(xml_path))
    if not m:
        return 0, 0
    code = int(m.group(1))
    try:
        mtime = xml_path.stat().st_mtime
    except OSError:
        return 0, 0

    existing = set(
        row[0] for row in conn.execute(
            "SELECT articulo_num FROM articulos_meta WHERE doc_path = ?",
            (str(xml_path),),
        )
    )

    articulos = extract_articulos(xml_path)
    if not articulos:
        return 0, 0
    inserted, skipped = 0, 0
    for art in articulos:
        if art["articulo_num"] in existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO articulos(doc_path, leychile_code, articulo_num, "
            "seccion, content) VALUES (?, ?, ?, ?, ?)",
            (str(xml_path), code, art["articulo_num"],
             art["seccion"], art["content"]),
        )
        conn.execute(
            "INSERT OR IGNORE INTO articulos_meta("
            "doc_path, leychile_code, articulo_num, seccion, chars, mtime"
            ") VALUES (?, ?, ?, ?, ?, ?)",
            (str(xml_path), code, art["articulo_num"], art["seccion"],
             len(art["content"]), mtime),
        )
        inserted += 1
    return inserted, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--root", default=str(LEYCHILE_DIR))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    conn = init_db(Path(args.db))
    root = Path(args.root)
    xmls = list(root.rglob("*.xml"))
    if args.limit > 0:
        xmls = xmls[:args.limit]
    print(f"XMLs LeyChile: {len(xmls)}", flush=True)

    import time
    start = time.time()
    n_docs, n_articulos, n_skipped = 0, 0, 0
    for i, xml in enumerate(xmls, 1):
        ins, skp = index_file(conn, xml)
        n_articulos += ins
        n_skipped += skp
        if ins or skp:
            n_docs += 1
        if i % 500 == 0:
            conn.commit()
            elapsed = time.time() - start
            rate = i / elapsed
            print(f"  [{i}/{len(xmls)}] docs={n_docs} articulos={n_articulos} "
                  f"skip={n_skipped} | {rate:.0f} XMLs/s",
                  flush=True)
    conn.commit()
    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | {n_docs} docs, {n_articulos} artículos "
          f"nuevos, {n_skipped} skip")

    # Stats finales
    total_art = conn.execute("SELECT COUNT(*) FROM articulos_meta").fetchone()[0]
    total_docs = conn.execute(
        "SELECT COUNT(DISTINCT doc_path) FROM articulos_meta"
    ).fetchone()[0]
    avg_chars = conn.execute(
        "SELECT AVG(chars) FROM articulos_meta"
    ).fetchone()[0]
    print(f"\nÍndice total: {total_art} artículos / {total_docs} docs")
    print(f"  Avg chars/artículo: {avg_chars:.0f}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
