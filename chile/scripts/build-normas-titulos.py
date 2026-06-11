#!/usr/bin/env python3
"""Construye normas_titulos en citas_normativas.sqlite3 desde los XML leychile.

Lee solo el encabezado (~4KB) de cada XML: id_norma, tipo, numero, titulo,
derogado. Base para resolver citas textuales ("Código Civil", "ley 19.496")
a id_norma. DB separada de corpus.fts para no contender con el embed-loop.
"""
import re, sqlite3, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
OUT = ROOT / "data/_index/citas_normativas.sqlite3"

RX_ID = re.compile(r'normaId="(\d+)"')
RX_DEROG = re.compile(r'<Norma [^>]*derogado="([^"]+)"')
RX_TIPO = re.compile(r"<Tipo>([^<]+)</Tipo>")
RX_NUM = re.compile(r"<Numero>([^<]+)</Numero>")
RX_TIT = re.compile(r"<TituloNorma>([^<]*)</TituloNorma>")


def parse_one(path: str):
    try:
        with open(path, "rb") as f:
            head = f.read(6000).decode("utf-8", "replace")
        mid = RX_ID.search(head)
        if not mid:
            return None
        tit = RX_TIT.search(head)
        return (
            int(mid.group(1)),
            (RX_TIPO.search(head) or [None, ""])[1].strip(),
            (RX_NUM.search(head) or [None, ""])[1].strip(),
            (tit.group(1).strip() if tit else ""),
            (RX_DEROG.search(head) or [None, ""])[1],
            path,
        )
    except Exception:
        return None


def main():
    files = [str(p) for p in (ROOT / "data/leychile").rglob("*.xml")]
    print(f"XMLs: {len(files)}", flush=True)
    conn = sqlite3.connect(str(OUT))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS normas_titulos ("
        "id_norma INTEGER PRIMARY KEY, tipo TEXT, numero TEXT, titulo TEXT,"
        "derogado TEXT, path TEXT)"
    )
    n = 0
    with ProcessPoolExecutor(max_workers=6) as pool:
        batch = []
        for r in pool.map(parse_one, files, chunksize=500):
            if r:
                batch.append(r)
            if len(batch) >= 5000:
                conn.executemany(
                    "INSERT OR REPLACE INTO normas_titulos VALUES (?,?,?,?,?,?)", batch
                )
                conn.commit()
                n += len(batch)
                print(f"  {n} títulos…", flush=True)
                batch = []
        if batch:
            conn.executemany(
                "INSERT OR REPLACE INTO normas_titulos VALUES (?,?,?,?,?,?)", batch
            )
            conn.commit()
            n += len(batch)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_titulos_tipo_num ON normas_titulos(tipo, numero)"
    )
    conn.commit()
    print(f"[DONE] {n} normas_titulos en {OUT}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
