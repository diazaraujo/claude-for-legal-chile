#!/usr/bin/env python3
"""Re-cluster + re-label SOLO las keys afectadas por el fix de resolución código→oficial.
Reusa los embeddings de ventanas ya calculados (windows.f16.npy) — solo cambia el
agrupamiento por (id_norma, articulo) tras el re-mapeo de citas_windows.id_norma.
Idempotente: sobrescribe los npz y reescribe las líneas del jsonl de esas keys.
"""
import json, os, re, sqlite3, time, urllib.request
import numpy as np
import faiss

DB = "/home/antonio/lc-index/citas_normativas.sqlite3"
V2 = "/home/antonio/lc-index/tesis-v2"
META = json.load(open("/tmp/arbol-meta.json"))
KEYS = set(json.load(open("/tmp/keys-recluster.json")))

ids = np.load(f"{V2}/rowids.npy")
vecs = np.load(f"{V2}/windows.f16.npy", mmap_mode="r")
pos = {int(r): i for i, r in enumerate(ids)}
con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)

print(f"keys a re-procesar: {len(KEYS)}", flush=True)
# agrupar rowids de ventanas por key afectada
groups = {}
for idn, art, rowid in con.execute("SELECT id_norma, articulo, rowid FROM citas_windows"):
    k = re.sub(r"[^0-9A-Za-z]+", "-", f"{idn}_{art}")
    if k in KEYS:
        groups.setdefault(k, []).append(rowid)
print(f"keys con ventanas: {len(groups)}", flush=True)

# fase 1: re-cluster
t0 = time.time(); done = 0
for k, rowids in groups.items():
    idx = [pos[r] for r in rowids if r in pos]
    f = f"{V2}/{k}.npz"
    if not idx:
        if os.path.exists(f):
            os.remove(f)
        continue
    rid = np.array(sorted(idx))
    X = np.asarray(vecs[rid], dtype="float32"); faiss.normalize_L2(X)
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
print(f"[F1] {done} re-clusterizadas · {time.time()-t0:.0f}s", flush=True)


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


# fase 2: re-label esas keys, reescribiendo el jsonl (drop líneas viejas de esas keys + append nuevas)
OUTL = f"{V2}/labels-llm.jsonl"
kept = [l for l in open(OUTL) if json.loads(l)["key"] not in KEYS]
open(OUTL, "w").writelines(kept)
out = open(OUTL, "a")
t0 = time.time(); n = 0
for k in groups:
    if k not in META:
        continue
    meta = META[k]
    f = f"{V2}/{k}.npz"
    if not os.path.exists(f):
        continue
    d = np.load(f)
    rmap, A = d["rowids"], d["assign"]
    clusters = {}
    for c in sorted(set(A.tolist())):
        sel = rmap[A == c]
        if "centroids" in d.files and len(sel) > 8:
            sl = np.asarray(vecs[[pos[int(r)] for r in sel[:2000]]], dtype="float32"); faiss.normalize_L2(sl)
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
    out.write(json.dumps({"key": k, "norma": meta["norma"], "articulo": meta["articulo"],
                          "clusters": clusters}, ensure_ascii=False) + "\n")
    out.flush(); n += 1
    if n % 200 == 0:
        print(f"  label {n}/{len(groups)} · {(time.time()-t0)/60:.0f}min", flush=True)
print(f"[F2] {n} re-etiquetadas · {(time.time()-t0)/60:.0f}min", flush=True)
print("[DONE]", flush=True)
