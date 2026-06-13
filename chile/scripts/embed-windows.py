#!/usr/bin/env python3
"""Embeddings v2: ventanas de citación → bge-m3 vía TEI :8002 (float16 memmap).

Lee citas_windows de citas_normativas.sqlite3 (orden rowid), embebe en batches
y escribe /home/antonio/lc-index/tesis-v2/windows.f16.npy (memmap N×1024) +
rowids.npy. Reanudable: guarda progreso en progress.txt (índice del próximo batch).
"""
import json, sqlite3, time, urllib.request, os, sys
import numpy as np

DB = "/home/antonio/lc-index/citas_normativas.sqlite3"
OUT = "/home/antonio/lc-index/tesis-v2"
TEI = "http://localhost:8002/embed"
BATCH = 64
WORKERS = 8

os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)
n = con.execute("SELECT count(*) FROM citas_windows").fetchone()[0]
print(f"ventanas: {n:,}", flush=True)

rowids_f = f"{OUT}/rowids.npy"
vecs_f = f"{OUT}/windows.f16.npy"
if not os.path.exists(rowids_f):
    ids = np.array([r[0] for r in con.execute("SELECT rowid FROM citas_windows ORDER BY rowid")], dtype="int64")
    np.save(rowids_f, ids)
ids = np.load(rowids_f)
vecs = np.lib.format.open_memmap(vecs_f, mode=("r+" if os.path.exists(vecs_f) else "w+"),
                                 dtype="float16", shape=(len(ids), 1024))
start = 0
pf = f"{OUT}/progress.txt"
if os.path.exists(pf):
    start = int(open(pf).read().strip() or 0)
print(f"reanudando desde fila {start:,}", flush=True)


def embed(texts, retries=4):
    for r in range(retries):
        try:
            p = json.dumps({"inputs": [t[:1200] for t in texts]}).encode()
            req = urllib.request.Request(TEI, data=p, headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception:
            time.sleep(3 * (r + 1))
    return None


from concurrent.futures import ThreadPoolExecutor

t0 = time.time(); done = start
cur = con.execute("SELECT rowid, window FROM citas_windows WHERE rowid > ? ORDER BY rowid",
                  (int(ids[start - 1]) if start else -1,))


def take(k):
    out = []
    for _ in range(k):
        r = cur.fetchone()
        if r is None:
            break
        out.append(r)
    return out


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    while True:
        batches = []
        for _ in range(WORKERS):
            b = take(BATCH)
            if b:
                batches.append(b)
        if not batches:
            break
        results = list(ex.map(lambda b: (b, embed([w for _, w in b])), batches))
        for b, vs in results:
            if vs is None or len(vs) != len(b):
                print(f"ERROR batch en fila {done} — abortando para reanudar", flush=True)
                sys.exit(2)
            vecs[done:done + len(b)] = np.asarray(vs, dtype="float16")
            done += len(b)
        open(pf, "w").write(str(done))
        if done % 51200 < BATCH * WORKERS:
            el = time.time() - t0
            print(f"  {done:,}/{len(ids):,} · {(done-start)/el:.0f}/s · ETA {((len(ids)-done)/max(1,(done-start)/el))/60:.0f}min", flush=True)
vecs.flush()
print(f"[DONE] {done:,} vectores en {(time.time()-t0)/60:.0f}min", flush=True)
