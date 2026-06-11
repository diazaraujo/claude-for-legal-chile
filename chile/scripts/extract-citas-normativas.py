#!/usr/bin/env python3
"""Extrae citas normativas de los considerandos → citas_normativas.sqlite3.

Detecta en cada chunk de considerandos_chunks referencias del estilo:
  - "artículo 1545 del Código Civil" / "art. 477 del Código del Trabajo"
  - "artículos 19 y 20 de la ley N° 19.496" / "de la ley 18.045"
  - "artículo 19 N° 3 de la Constitución Política"
  - "decreto ley N° 3.500" / "DL 211" / "DFL N° 1"
Guarda la cita cruda + campos parseados; la resolución a id_norma es un paso
posterior (resolve-citas-normativas.py) vía normas_titulos. NO se inventan IDs.

Lee corpus.fts en -readonly (WAL, convive con el embed-loop que escribe);
escribe en DB separada para no contender. Reanudable: tabla progreso por rango.

Usage: python3 extract-citas-normativas.py [--max-rowid N] [--workers 6]
"""
import argparse, re, sqlite3, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
CORPUS = ROOT / "data/_index/corpus.fts.sqlite3"
OUT = ROOT / "data/_index/citas_normativas.sqlite3"
RANGE = 50_000  # chunks por tarea

ART = r"art[íi]culos?\.?|arts?\."
NUM = r"\d{1,4}(?:\s*(?:bis|ter|qu[áa]ter|quinquies))?(?:\s*[°º])?(?:\s+(?:transitorio|permanente))?"
NUMLIST = rf"{NUM}(?:\s*(?:,|y|e)\s*{NUM})*"
LEY = r"[Ll]ey(?:\s*N\s*[°º\.]*)?\s*([\d][\d\.]{2,8})"
CPR = r"Constituci[óo]n\s+Pol[íi]tica(?:\s+de\s+la\s+Rep[úu]blica)?(?:\s+de\s+Chile)?"
CODIGO = r"C[óo]digo\s+(?:de\s+|del\s+|de\s+la\s+)?[A-ZÁÉÍÓÚ][A-Za-zÁÉÍÓÚáéíóúñ]+(?:\s+(?:de|del|de\s+la|y)\s+[A-Za-zÁÉÍÓÚáéíóúñ]+){0,3}"
DLDFL = r"(?:[Dd]ecreto\s+[Ll]ey|D\.?L\.?)(?:\s*N\s*[°º\.]*)?\s*([\d][\d\.]{0,6})"
DFL = r"(?:[Dd]ecreto\s+con\s+[Ff]uerza\s+de\s+[Ll]ey|D\.?F\.?L\.?)(?:\s*N\s*[°º\.]*)?\s*([\d][\d\.]{0,6})"

PATTERNS = [
    # artículo(s) X del <cuerpo>
    ("art_codigo", re.compile(rf"(?:{ART})\s+({NUMLIST})\s+(?:N\s*[°º]\s*\d+\s+)?(?:de\s+la|del|de)\s+({CODIGO})", re.I)),
    ("art_ley", re.compile(rf"(?:{ART})\s+({NUMLIST})\s+(?:N\s*[°º]\s*\d+\s+)?(?:de\s+la|del|de)\s+{LEY}", re.I)),
    ("art_cpr", re.compile(rf"(?:{ART})\s+({NUMLIST})(?:\s+N\s*[°º]\s*(\d+))?\s+(?:de\s+la|del|de)\s+(?:{CPR})", re.I)),
    ("art_dfl", re.compile(rf"(?:{ART})\s+({NUMLIST})\s+(?:de\s+la|del|de)\s+{DFL}", re.I)),
    ("art_dl", re.compile(rf"(?:{ART})\s+({NUMLIST})\s+(?:de\s+la|del|de)\s+{DLDFL}", re.I)),
    # cuerpo sin artículo (cita a nivel norma)
    ("ley", re.compile(LEY)),
    ("dfl", re.compile(DFL)),
    ("dl", re.compile(DLDFL)),
    ("codigo", re.compile(rf"({CODIGO})")),
    ("cpr", re.compile(CPR, re.I)),
]
RX_ARTSPLIT = re.compile(r"\d{1,4}(?:\s*(?:bis|ter|qu[áa]ter|quinquies))?", re.I)


def extract(text: str):
    """Devuelve [(tipo_cita, articulo, cuerpo, raw)] dedupeado; las citas con
    artículo enmascaran su span para que los patrones nivel-norma no dupliquen."""
    out, seen, masked = [], set(), text
    for tipo, rx in PATTERNS:
        src = masked if not tipo.startswith("art_") else text
        for m in rx.finditer(src):
            raw = re.sub(r"\s+", " ", m.group(0))[:200]
            if tipo.startswith("art_"):
                arts, cuerpo = m.group(1), (m.group(2) if m.lastindex and m.lastindex >= 2 else "")
                if tipo == "art_cpr":
                    cuerpo = "CPR" + (f" 19-{m.group(2)}" if m.group(2) else "")
                for a in RX_ARTSPLIT.findall(arts):
                    key = (tipo, a.strip(), cuerpo.strip().lower())
                    if key not in seen:
                        seen.add(key)
                        out.append((tipo, a.strip(), cuerpo.strip(), raw))
                masked = masked.replace(m.group(0), " " * len(m.group(0)), 1)
            else:
                cuerpo = m.group(1) if m.lastindex else ("CPR" if tipo == "cpr" else "")
                key = (tipo, "", cuerpo.strip().lower())
                if key not in seen:
                    seen.add(key)
                    out.append((tipo, "", cuerpo.strip(), raw))
    return out


def work(rng):
    lo, hi = rng
    src = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True, timeout=120)
    rows = src.execute(
        "SELECT rowid, doc_path, source, num_orden, content FROM considerandos_chunks "
        "WHERE rowid BETWEEN ? AND ?", (lo, hi)).fetchall()
    src.close()
    res = []
    for rowid, doc, source, num, content in rows:
        for tipo, art, cuerpo, raw in extract(content or ""):
            res.append((rowid, doc, source, num, tipo, art, cuerpo, raw))
    return lo, hi, len(rows), res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-rowid", type=int, default=0)
    args = ap.parse_args()

    src = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True, timeout=120)
    top = src.execute("SELECT max(rowid) FROM considerandos_chunks").fetchone()[0]
    src.close()
    if args.max_rowid:
        top = min(top, args.max_rowid)

    out = sqlite3.connect(str(OUT), timeout=120)
    out.execute("PRAGMA journal_mode=WAL")
    out.execute(
        "CREATE TABLE IF NOT EXISTS citas ("
        "chunk_rowid INTEGER, doc_path TEXT, source TEXT, num_orden INTEGER,"
        "tipo_cita TEXT, articulo TEXT, cuerpo TEXT, raw TEXT)")
    out.execute(
        "CREATE TABLE IF NOT EXISTS citas_progreso (lo INTEGER PRIMARY KEY, hi INTEGER, n_chunks INTEGER, n_citas INTEGER)")
    done = {r[0] for r in out.execute("SELECT lo FROM citas_progreso")}
    ranges = [(lo, min(lo + RANGE - 1, top)) for lo in range(1, top + 1, RANGE) if lo not in done]
    print(f"chunks hasta rowid {top} · rangos pendientes: {len(ranges)} (de {top//RANGE+1})", flush=True)

    t0, nc, nch = time.time(), 0, 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for lo, hi, n, res in pool.map(work, ranges):
            if res:
                out.executemany("INSERT INTO citas VALUES (?,?,?,?,?,?,?,?)", res)
            out.execute("INSERT OR REPLACE INTO citas_progreso VALUES (?,?,?,?)", (lo, hi, n, len(res)))
            out.commit()
            nc += len(res); nch += n
            el = time.time() - t0
            print(f"  [{lo}-{hi}] chunks={nch} citas={nc} | {nch/el:.0f} chunks/s", flush=True)
    print(f"[DONE] {nch} chunks → {nc} citas en {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
