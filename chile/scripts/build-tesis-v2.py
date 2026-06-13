#!/usr/bin/env python3
"""Tesis v2 (quirúrgicas): clustering por artículo sobre vectores de VENTANAS de citación.

Universo completo de (id_norma, articulo) de citas_windows. k=4-12 según n.
Salida: tesis-v2/<key>.npz (chunk_rowids, assign, centroids) + labels-llm.jsonl
(qwen2.5:14b sobre las ventanas — contexto quirúrgico, mejor señal que v1).
Reanudable en ambas fases.
"""
import json, os, re, sqlite3, time, urllib.request, glob
import numpy as np
import faiss

DB = "/home/antonio/lc-index/citas_normativas.sqlite3"
V2 = "/home/antonio/lc-index/tesis-v2"
META = json.load(open("/tmp/arbol-meta.json"))

ids = np.load(f"{V2}/rowids.npy")
vecs = np.load(f"{V2}/windows.f16.npy", mmap_mode="r")
pos = {int(r): i for i, r in enumerate(ids)}
con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)

# fase 1: clustering
groups = {}
for idn, art, rowid in con.execute("SELECT id_norma, articulo, rowid FROM citas_windows"):
    groups.setdefault((idn, art), []).append(rowid)
print(f"grupos: {len(groups):,}", flush=True)
t0 = time.time(); done = 0
for (idn, art), rowids in sorted(groups.items(), key=lambda x: -len(x[1])):
    key = re.sub(r"[^0-9A-Za-z]+", "-", f"{idn}_{art}")
    f = f"{V2}/{key}.npz"
    if os.path.exists(f):
        done += 1; continue
    idx = [pos[r] for r in rowids if r in pos]
    if not idx:
        continue
    X = np.asarray(vecs[sorted(idx)], dtype="float32")
    faiss.normalize_L2(X)
    rid = np.array(sorted(idx))
    rmap = ids[rid]
    if len(idx) < 50:
        np.savez_compressed(f, rowids=rmap, assign=np.zeros(len(idx), dtype="int64"))
    else:
        K = min(12, max(4, int((len(idx) / 80) ** 0.5)))
        km = faiss.Kmeans(1024, K, niter=20, seed=42, spherical=True)
        km.train(X)
        _, A = km.index.search(X, 1)
        np.savez_compressed(f, rowids=rmap, assign=A.ravel(), centroids=km.centroids)
    done += 1
    if done % 500 == 0:
        print(f"  cluster {done}/{len(groups)} · {time.time()-t0:.0f}s", flush=True)
print(f"[F1 DONE] {done} grupos · {time.time()-t0:.0f}s", flush=True)

# fase 2: etiquetas LLM sobre ventanas
OUTL = f"{V2}/labels-llm.jsonl"
seen = set()
if os.path.exists(OUTL):
    for l in open(OUTL):
        try: seen.add(json.loads(l)["key"])
        except Exception: pass


def llm(prompt, retries=3):
    for _ in range(retries):
        try:
            p = json.dumps({"model": "qwen2.5:14b", "prompt": prompt, "stream": False,
                            "format": "json", "options": {"temperature": 0.2, "num_predict": 200}}).encode()
            r = urllib.request.urlopen(urllib.request.Request(
                "http://localhost:11434/api/generate", data=p,
                headers={"Content-Type": "application/json"}), timeout=180)
            return json.loads(json.loads(r.read())["response"])
        except Exception:
            time.sleep(5)
    return None


out = open(OUTL, "a")
files = sorted(glob.glob(f"{V2}/*.npz"), key=lambda f: -os.path.getsize(f))
t0 = time.time(); n = 0
for f in files:
    key = f.split("/")[-1][:-4]
    if key in seen or key not in META or key.startswith("rowids") or key.startswith("windows"):
        continue
    meta = META[key]
    d = np.load(f)
    rmap, A = d["rowids"], d["assign"]
    clusters = {}
    for c in sorted(set(A.tolist())):
        sel = rmap[A == c]
        if "centroids" in d.files and len(sel) > 8:
            sl = np.asarray(vecs[[pos[int(r)] for r in sel[:2000]]], dtype="float32")
            faiss.normalize_L2(sl)
            cent = d["centroids"][c:c + 1].copy(); faiss.normalize_L2(cent)
            pick = sel[:2000][np.argsort(-(sl @ cent.T).ravel())[:8]]
        else:
            pick = sel[:8]
        qq = ",".join(str(int(r)) for r in pick)
        texts = [t for (t,) in con.execute(f"SELECT window FROM citas_windows WHERE rowid IN ({qq})")]
        ej = "\n---\n".join(t[:500] for t in texts)
        prompt = ("Eres un jurista chileno experto. Estos pasajes de sentencias citan el "
                  f"articulo {meta['articulo']} de {meta['norma']} ({meta['titulo'][:100]}).\n\n{ej}\n\n"
                  "Nombra la tesis o linea interpretativa comun sobre ESE articulo. "
                  'Responde SOLO JSON: {"nombre": "<max 8 palabras>", "descripcion": "<1 frase>"}')
        r = llm(prompt)
        clusters[str(int(c))] = {"n": int(len(sel)),
                                 **(r if isinstance(r, dict) else {"nombre": None, "descripcion": None})}
    out.write(json.dumps({"key": key, "norma": meta["norma"], "articulo": meta["articulo"],
                          "clusters": clusters}, ensure_ascii=False) + "\n")
    out.flush(); n += 1
    if n % 200 == 0:
        print(f"  label {n} · {(time.time()-t0)/60:.0f}min", flush=True)
print(f"[F2 DONE] {n} articulos etiquetados en {(time.time()-t0)/60:.0f}min", flush=True)
