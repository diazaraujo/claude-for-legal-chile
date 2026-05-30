#!/usr/bin/env python3
"""Indexa+embebe las sentencias PJUD (data/pjud/<competencia>/*.json.gz) en el
índice local new-sources.fts. Cada batch trae ~100 sentencias con texto_sentencia
+ metadata. ~3,3M sentencias → mantiene la GPU (bge-m3 vía túnel) ocupada.

Idempotente por id de sentencia. Resume-able (salta batches ya hechos por marca).
"""
from __future__ import annotations
import argparse, gzip, json, re, sqlite3, struct, sys, time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pjud"
DB = ROOT / "data/_index/new-sources.fts.sqlite3"
OLLAMA = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
MAX_CHARS = 1500
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def embed(texts, timeout=180):
    payload = json.dumps({"model": MODEL, "input": [t[:MAX_CHARS] for t in texts]}).encode()
    req = urllib.request.Request(OLLAMA, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()).get("embeddings", [])


def init_db():
    c = sqlite3.connect(str(DB), timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS docs_meta (path TEXT PRIMARY KEY, source TEXT, chars INTEGER)")
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content)")
    c.execute("CREATE TABLE IF NOT EXISTS embeddings (path TEXT PRIMARY KEY, model TEXT, dim INTEGER, vec BLOB)")
    c.execute("CREATE TABLE IF NOT EXISTS pjud_batches (batch TEXT PRIMARY KEY, n INTEGER)")
    c.commit()
    return c


def sent_text(r):
    txt = r.get("texto_setencia") or r.get("texto_sentencia") or ""
    txt = _WS.sub(" ", _TAG.sub(" ", txt)).strip()
    head = (f"Corte: {r.get('gls_corte_s','')} · Materia: {r.get('gls_materia_s','')} · "
            f"Rol: {r.get('rol_era_ape_s') or r.get('rol_sup_i','')} · "
            f"Fecha: {(r.get('fec_sentencia_sup_dt') or '')[:10]} · {r.get('caratulado_s','')}")
    return (head + "\n" + txt).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()
    c = init_db()
    done_batches = {r[0] for r in c.execute("SELECT batch FROM pjud_batches")}
    have = {r[0] for r in c.execute("SELECT path FROM embeddings WHERE path LIKE 'pjud/%'")}
    files = sorted(DATA.rglob("*.json.gz"))
    pend = [f for f in files if str(f.relative_to(DATA)) not in done_batches]
    print(f"[pjud] {len(files):,} batches, {len(pend):,} pendientes", flush=True)
    t0, total = time.time(), 0
    for bi, f in enumerate(pend):
        try:
            d = json.loads(gzip.open(f).read())
        except Exception:
            continue
        recs = d if isinstance(d, list) else d.get("docs", d.get("response", {}).get("docs", []))
        comp = f.parent.name
        items = []
        for r in recs:
            sid = r.get("id") or r.get("id_instancia")
            if not sid:
                continue
            path = f"pjud/{comp}/{sid}"
            if path in have:
                continue
            txt = sent_text(r)
            if len(txt) < 60:
                continue
            items.append((path, txt))
        # embed en sub-batches
        for i in range(0, len(items), args.batch):
            chunk = items[i:i + args.batch]
            try:
                vecs = embed([t for _, t in chunk])
            except Exception as e:
                print(f"  embed err: {e}", flush=True); time.sleep(2); continue
            for (path, txt), v in zip(chunk, vecs):
                if v:
                    c.execute("INSERT OR IGNORE INTO docs(path, content) VALUES (?,?)", (path, txt))
                    c.execute("INSERT OR IGNORE INTO docs_meta(path, source, chars) VALUES (?,?,?)",
                              (path, f"pjud-{comp}", len(txt)))
                    c.execute("INSERT OR REPLACE INTO embeddings(path, model, dim, vec) VALUES (?,?,?,?)",
                              (path, MODEL, len(v), struct.pack(f"<{len(v)}f", *v)))
                    total += 1
        c.execute("INSERT OR REPLACE INTO pjud_batches(batch, n) VALUES (?,?)",
                  (str(f.relative_to(DATA)), len(items)))
        c.commit()
        if bi % 20 == 0:
            el = time.time() - t0
            rate = total / el if el else 0
            print(f"  batch {bi}/{len(pend)} ({comp}) · embebidas={total:,} · {rate:.0f}/s", flush=True)
    print(f"[DONE] {total:,} sentencias PJUD embebidas en {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
