#!/usr/bin/env python3
# std:input chile/normativa/catalogo/{tipo}/*.md + chile/normativa/grafo/relaciones-bcn.jsonl
# std:output chile/normativa/index/catalogo.sqlite3
# std:deps stdlib pura (sqlite3 + re)
"""
Indexa el catálogo capa 1 + grafo de relaciones en SQLite.

Lee:
- chile/normativa/catalogo/{tipo}/*.md (frontmatter YAML simple)
- chile/normativa/grafo/relaciones-bcn.jsonl (si existe)

Escribe SQLite en chile/normativa/index/catalogo.sqlite3 con tablas:
- normas(slug, tipo, numero, titulo, publicacion, promulgacion, organismo,
         leychile_code, bcn_uri, capa, md_path)
- relaciones(src_uri, rel, dst_uri)
- normas_fts(slug, titulo) [FTS5 si está disponible]

Re-construye desde cero cada vez (idempotente). Conforme a
[[feedback-no-inventar-ids-urls-referencias]]: sólo persiste lo que
está en los .md fuente.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "chile/normativa/catalogo"
GRAFO_FILE = REPO_ROOT / "chile/normativa/grafo/relaciones-bcn.jsonl"
DB_DIR = REPO_ROOT / "chile/normativa/index"
DB_PATH = DB_DIR / "catalogo.sqlite3"


FM_FIELDS = {
    "slug", "tipo", "numero", "titulo_oficial", "publicacion",
    "promulgacion", "emisor", "leychile_code", "bcn_uri", "capa",
    "fuente_oficial", "estado_revision",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    raw = text[4:end]
    out: dict[str, str] = {}
    for line in raw.split("\n"):
        if not line or line.startswith("  ") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        # Quitar comillas si las tiene
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1].replace('\\"', '"')
        if k in FM_FIELDS:
            out[k] = v
    return out


def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS normas;
        DROP TABLE IF EXISTS relaciones;
        DROP TABLE IF EXISTS normas_fts;

        CREATE TABLE normas (
            slug TEXT PRIMARY KEY,
            tipo TEXT,
            numero TEXT,
            titulo TEXT,
            publicacion TEXT,
            promulgacion TEXT,
            organismo TEXT,
            leychile_code TEXT,
            bcn_uri TEXT,
            capa INTEGER,
            md_path TEXT
        );
        CREATE INDEX idx_normas_tipo ON normas(tipo);
        CREATE INDEX idx_normas_leychile ON normas(leychile_code);
        CREATE INDEX idx_normas_uri ON normas(bcn_uri);
        CREATE INDEX idx_normas_numero ON normas(tipo, numero);

        CREATE TABLE relaciones (
            src_uri TEXT,
            rel TEXT,
            dst_uri TEXT
        );
        CREATE INDEX idx_rel_src ON relaciones(src_uri, rel);
        CREATE INDEX idx_rel_dst ON relaciones(dst_uri, rel);
        """
    )
    # FTS5 opcional
    try:
        cur.execute(
            "CREATE VIRTUAL TABLE normas_fts USING fts5(slug, titulo, tipo, content='')"
        )
        cur.execute("INSERT INTO normas_fts(normas_fts) VALUES('rebuild')")
        has_fts = True
    except sqlite3.OperationalError:
        has_fts = False
    conn.commit()
    if not has_fts:
        print("[WARN] FTS5 no disponible, búsqueda por LIKE solamente")


def index_catalog(conn: sqlite3.Connection) -> tuple[int, dict[str, int]]:
    cur = conn.cursor()
    total = 0
    by_tipo: dict[str, int] = {}
    if not CATALOG_ROOT.exists():
        return 0, {}

    for tipo_dir in sorted(CATALOG_ROOT.iterdir()):
        if not tipo_dir.is_dir():
            continue
        for f in tipo_dir.glob("*.md"):
            try:
                fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  [SKIP] {f}: {e}")
                continue
            slug = fm.get("slug") or f.stem
            tipo = fm.get("tipo") or tipo_dir.name
            try:
                capa = int(fm.get("capa", "1"))
            except ValueError:
                capa = 1
            cur.execute(
                "INSERT OR REPLACE INTO normas("
                "slug, tipo, numero, titulo, publicacion, promulgacion, "
                "organismo, leychile_code, bcn_uri, capa, md_path"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    slug,
                    tipo,
                    fm.get("numero"),
                    fm.get("titulo_oficial"),
                    fm.get("publicacion"),
                    fm.get("promulgacion"),
                    fm.get("emisor"),
                    fm.get("leychile_code"),
                    fm.get("bcn_uri"),
                    capa,
                    str(f.relative_to(REPO_ROOT)),
                ),
            )
            total += 1
            by_tipo[tipo] = by_tipo.get(tipo, 0) + 1
        conn.commit()

    # Rebuild FTS si existe
    try:
        cur.execute(
            "INSERT INTO normas_fts(slug, titulo, tipo) "
            "SELECT slug, titulo, tipo FROM normas WHERE titulo IS NOT NULL"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    return total, by_tipo


def index_relaciones(conn: sqlite3.Connection) -> int:
    if not GRAFO_FILE.exists():
        return 0
    cur = conn.cursor()
    n = 0
    batch: list[tuple] = []
    with open(GRAFO_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            batch.append((row["src"], row["rel"], row["dst"]))
            if len(batch) >= 5000:
                cur.executemany(
                    "INSERT INTO relaciones(src_uri, rel, dst_uri) VALUES (?, ?, ?)",
                    batch,
                )
                n += len(batch)
                batch.clear()
        if batch:
            cur.executemany(
                "INSERT INTO relaciones(src_uri, rel, dst_uri) VALUES (?, ?, ?)",
                batch,
            )
            n += len(batch)
    conn.commit()
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SQLite catalog index")
    parser.parse_args()

    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    start = time.time()
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    print(f"[INFO] Indexando catálogo desde {CATALOG_ROOT}...")
    total, by_tipo = index_catalog(conn)
    print(f"  Normas indexadas: {total}")
    for tipo, n in sorted(by_tipo.items(), key=lambda x: -x[1]):
        print(f"    {tipo}: {n}")

    print(f"\n[INFO] Indexando relaciones desde {GRAFO_FILE}...")
    rel_count = index_relaciones(conn)
    print(f"  Edges indexados: {rel_count}")

    conn.close()
    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s. DB en {DB_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
