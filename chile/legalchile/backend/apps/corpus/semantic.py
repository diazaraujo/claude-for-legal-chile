"""Búsqueda semántica (vectorial) sobre el corpus jurídico chileno.

Embeddings bge-m3 (dim 1024) precomputados en el pipeline → índice faiss IVFFlat
(coseno) en CORPUS_INDEX_DIR/new-sources.ivf.faiss + paths en .paths.txt.
La query se embeddea con el MISMO modelo vía Ollama (proxy host 172.17.0.1:11434,
que reenvía a la GPU de enigma sin reiniciar Ollama).

El índice se abre con mmap (IO_FLAG_MMAP) → las páginas se comparten entre los
workers gunicorn vía page-cache; no se cargan los ~20GB en RAM por worker.
"""
import json
import os
import urllib.request
from pathlib import Path

import faiss
import numpy as np
from django.conf import settings

_OLLAMA = os.environ.get("OLLAMA_EMBED_URL", "http://172.17.0.1:11434/api/embed")
_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
_NPROBE = int(os.environ.get("FAISS_NPROBE", "32"))

_index = None
_paths = None


def _load():
    global _index, _paths
    if _index is None:
        d = Path(settings.CORPUS_INDEX_DIR)
        idx = d / "new-sources.ivf.faiss"
        pth = d / "new-sources.paths.txt"
        if not idx.exists() or not pth.exists():
            raise FileNotFoundError(f"Índice vectorial no encontrado en {d} (¿corrió el build faiss?)")
        _index = faiss.read_index(str(idx), faiss.IO_FLAG_MMAP)
        _index.nprobe = _NPROBE
        _paths = pth.read_text().splitlines()
    return _index, _paths


def _embed(q: str) -> np.ndarray:
    body = json.dumps({"model": _MODEL, "input": [q]}).encode()
    req = urllib.request.Request(_OLLAMA, data=body, headers={"Content-Type": "application/json"})
    v = np.asarray(json.loads(urllib.request.urlopen(req, timeout=30).read())["embeddings"][0],
                   dtype="float32")[None, :]
    faiss.normalize_L2(v)
    return v


def available() -> bool:
    try:
        d = Path(settings.CORPUS_INDEX_DIR)
        return (d / "new-sources.ivf.faiss").exists() and (d / "new-sources.paths.txt").exists()
    except Exception:
        return False


def semantic_search(q: str, limit: int = 20) -> list[dict]:
    if not q or not q.strip():
        return []
    index, paths = _load()
    D, I = index.search(_embed(q), min(limit, 100))
    out = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        out.append({"path": paths[idx], "score": round(float(score), 4)})
    return out
