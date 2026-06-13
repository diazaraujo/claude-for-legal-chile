#!/usr/bin/env python3
"""Tesis v2: ventana de texto alrededor de cada cita normativa.

Para cada cita resuelta (id_norma + articulo) toma ±WINDOW chars alrededor de la
posición del match (campo raw) dentro del chunk → el contexto interpretativo
quirúrgico, en vez del considerando completo. Salida: tabla citas_windows en
citas_normativas.sqlite3 (cita_key, chunk_rowid, window). Dedupe por
(chunk_rowid, id_norma, articulo). Reanudable por rangos de chunk_rowid.
"""
import re, sqlite3, sys, time
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
DB = ROOT / "data/_index/citas_normativas.sqlite3"
CORPUS = ROOT / "data/_index/corpus.fts.sqlite3"
WINDOW = 260
RANGE = 100_000


def main():
    out = sqlite3.connect(str(DB), timeout=120)
    out.execute("PRAGMA journal_mode=WAL")
    out.execute("CREATE TABLE IF NOT EXISTS citas_windows ("
                "id_norma INTEGER, articulo TEXT, chunk_rowid INTEGER, window TEXT, "
                "PRIMARY KEY (id_norma, articulo, chunk_rowid))")
    out.execute("CREATE TABLE IF NOT EXISTS citas_windows_progreso (lo INTEGER PRIMARY KEY, n INTEGER)")
    done = {r[0] for r in out.execute("SELECT lo FROM citas_windows_progreso")}

    cor = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True, timeout=120)
    top = out.execute("SELECT max(chunk_rowid) FROM citas").fetchone()[0]
    ranges = [lo for lo in range(0, top + 1, RANGE) if lo not in done]
    print(f"rangos pendientes: {len(ranges)} (top rowid {top})", flush=True)

    t0, total = time.time(), 0
    for lo in ranges:
        hi = lo + RANGE - 1
        citas = out.execute(
            "SELECT chunk_rowid, id_norma, articulo, min(raw) FROM citas "
            "WHERE id_norma IS NOT NULL AND articulo != '' AND chunk_rowid BETWEEN ? AND ? "
            "GROUP BY chunk_rowid, id_norma, articulo", (lo, hi)).fetchall()
        if not citas:
            out.execute("INSERT OR REPLACE INTO citas_windows_progreso VALUES (?,0)", (lo,))
            out.commit()
            continue
        rowids = sorted({c[0] for c in citas})
        texts = {}
        for k in range(0, len(rowids), 5000):
            q = ",".join(map(str, rowids[k:k + 5000]))
            texts.update(dict(cor.execute(
                f"SELECT rowid, content FROM considerandos_chunks WHERE rowid IN ({q})")))
        rows = []
        for rowid, idn, art, raw in citas:
            t = texts.get(rowid) or ""
            pos = t.find(raw[:60]) if raw else -1
            if pos < 0:
                w = t[:2 * WINDOW]
            else:
                w = t[max(0, pos - WINDOW):pos + len(raw) + WINDOW]
            w = re.sub(r"\s+", " ", w).strip()
            if len(w) >= 40:
                rows.append((idn, art, rowid, w))
        out.executemany("INSERT OR REPLACE INTO citas_windows VALUES (?,?,?,?)", rows)
        out.execute("INSERT OR REPLACE INTO citas_windows_progreso VALUES (?,?)", (lo, len(rows)))
        out.commit()
        total += len(rows)
        el = time.time() - t0
        print(f"  [{lo}] ventanas={total} · {total/el:.0f}/s", flush=True)
    print(f"[DONE] {total} ventanas en {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
