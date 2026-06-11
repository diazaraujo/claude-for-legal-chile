"""Árbol normativo de interpretaciones — Ley → artículo → año → tesis → sentencias.

Datos en CORPUS_INDEX_DIR (/index, ro):
  - citas_normativas.sqlite3: citas (4,4M resueltas), normas_titulos, doc_fechas,
    tablas materializadas arbol_mat / arbol_temporal_mat (norma×artículo[×año]).
  - tesis/<norma>-<articulo>.npz: clustering (ids, assign, centroids, cohesion).
  - tesis/labels-llm.jsonl: nombres de tesis por cluster (crece overnight; se relee
    si cambia el mtime). labels.json: fallback TF-IDF.
  - corpus.fts.sqlite3: texto de considerandos_chunks.
  - considerandos.ivf.faiss + .ids.npy: búsqueda semántica granular (mmap).
"""
import json
import os
import re
import sqlite3
import urllib.request
from pathlib import Path

import faiss
import numpy as np
from django.conf import settings

_OLLAMA = os.environ.get("OLLAMA_EMBED_URL", "http://172.17.0.1:11434/api/embed")
_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
_NPROBE = int(os.environ.get("FAISS_NPROBE", "32"))

_cidx = None
_cids = None
_labels = {"mtime": 0, "data": {}}
_tfidf = {"mtime": 0, "data": {}}


def _d() -> Path:
    return Path(settings.CORPUS_INDEX_DIR)


def _citas():
    return sqlite3.connect(f"file:{_d()/'citas_normativas.sqlite3'}?immutable=1", uri=True, timeout=30)


def _corpus():
    return sqlite3.connect(f"file:{_d()/'corpus.fts.sqlite3'}?immutable=1", uri=True, timeout=30)


def _key(id_norma, articulo) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", f"{id_norma}_{articulo}")


def _load_jsonl_labels(cache: dict, path) -> dict:
    """labels-llm.jsonl crece durante el etiquetado → recarga por mtime."""
    if not path.exists():
        return {}
    mt = path.stat().st_mtime
    if mt != cache["mtime"]:
        data = {}
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
                data[r["key"]] = r["clusters"]
            except Exception:
                continue
        cache.update(mtime=mt, data=data)
    return cache["data"]


def _llm_labels() -> dict:
    return _load_jsonl_labels(_labels, _d() / "tesis" / "labels-llm.jsonl")


_labels_v2 = {"mtime": 0, "data": {}}


def _llm_labels_v2() -> dict:
    return _load_jsonl_labels(_labels_v2, _d() / "tesis-v2" / "labels-llm.jsonl")


def _tfidf_labels() -> dict:
    f = _d() / "tesis" / "labels.json"
    if not f.exists():
        return {}
    mt = f.stat().st_mtime
    if mt != _tfidf["mtime"]:
        _tfidf.update(mtime=mt, data=json.loads(f.read_text()))
    return _tfidf["data"]


def available() -> bool:
    try:
        return (_d() / "citas_normativas.sqlite3").exists()
    except Exception:
        return False


def normas(q: str = "", limit: int = 50) -> list[dict]:
    con = _citas()
    sql = ("SELECT m.id_norma, t.tipo, t.numero, t.titulo, t.derogado, "
           "count(*) AS n_articulos, sum(m.n_sentencias) AS n_sentencias "
           "FROM arbol_mat m JOIN normas_titulos t USING(id_norma) ")
    args: list = []
    if q.strip():
        sql += "WHERE t.titulo LIKE ? OR t.numero = ? "
        args += [f"%{q.strip().upper()}%", q.strip()]
    sql += "GROUP BY m.id_norma ORDER BY n_sentencias DESC LIMIT ?"
    args.append(min(limit, 200))
    out = [dict(zip(("id_norma", "tipo", "numero", "titulo", "derogado", "n_articulos", "n_sentencias"), r))
           for r in con.execute(sql, args)]
    con.close()
    return out


def articulos(id_norma: int) -> dict:
    con = _citas()
    t = con.execute("SELECT tipo, numero, titulo, derogado FROM normas_titulos WHERE id_norma=?",
                    (id_norma,)).fetchone()
    arts = [dict(zip(("articulo", "n_sentencias", "n_citas"), r)) for r in con.execute(
        "SELECT articulo, n_sentencias, n_citas FROM arbol_mat WHERE id_norma=? "
        "AND articulo != '' ORDER BY n_sentencias DESC", (id_norma,))]
    con.close()
    if not t:
        return {}
    return {"id_norma": id_norma, "tipo": t[0], "numero": t[1], "titulo": t[2],
            "derogado": t[3], "articulos": arts}


def articulo_detalle(id_norma: int, articulo: str, muestras: int = 3) -> dict:
    key = _key(id_norma, articulo)
    con = _citas()
    anios = [dict(zip(("anio", "n_sentencias"), r)) for r in con.execute(
        "SELECT anio, n_sentencias FROM arbol_temporal_mat "
        "WHERE id_norma=? AND articulo=? ORDER BY anio", (id_norma, articulo))]

    # capa administrativa: dictámenes/oficios que citan el mismo artículo
    admin = []
    try:
        admin = [dict(zip(("source", "n_docs", "n_citas"), r)) for r in con.execute(
            "SELECT source, n_docs, n_citas FROM arbol_admin_mat "
            "WHERE id_norma=? AND articulo=? ORDER BY n_docs DESC", (id_norma, articulo))]
    except sqlite3.OperationalError:
        pass  # DB sin capa admin aún

    tesis = []
    # v2 (quirúrgico: clustering sobre la ventana de cita) tiene prioridad por artículo
    # apenas su etiquetado exista; fallback a v1 (considerando completo).
    llm_v2 = _llm_labels_v2().get(key)
    npz_v2 = _d() / "tesis-v2" / f"{key}.npz"
    if llm_v2 and npz_v2.exists():
        d = np.load(npz_v2)
        wrids, A = d["rowids"], d["assign"]
        for c in sorted(set(A.tolist()), key=lambda c: -(A == c).sum()):
            sel = wrids[A == c]
            lab = llm_v2.get(str(int(c))) or {}
            ej = []
            qq = ",".join(str(int(r)) for r in sel[:muestras])
            for chunk_rowid, win in con.execute(
                    f"SELECT chunk_rowid, substr(window, 1, 240) FROM citas_windows "
                    f"WHERE rowid IN ({qq})"):
                doc = con.execute("SELECT doc_path FROM citas WHERE chunk_rowid=? LIMIT 1",
                                  (chunk_rowid,)).fetchone()
                doc = doc[0] if doc else None
                fe = con.execute("SELECT fecha, rol, caratulado, tribunal FROM doc_fechas "
                                 "WHERE doc_path=?", (doc,)).fetchone() if doc else None
                ej.append({"doc_path": doc, "extracto": win,
                           "fecha": fe[0] if fe else None, "rol": fe[1] if fe else None,
                           "caratulado": fe[2] if fe else None, "tribunal": fe[3] if fe else None})
            tesis.append({"cluster": int(c), "n": int(len(sel)),
                          "nombre": lab.get("nombre"), "descripcion": lab.get("descripcion"),
                          "terminos": [], "ejemplos": ej, "v": 2})
        con.close()
        return {"id_norma": id_norma, "articulo": articulo, "anios": anios,
                "tesis": tesis, "administrativa": admin}

    llm = _llm_labels().get(key) or {}
    tf = (_tfidf_labels().get(key) or {}).get("clusters", {})
    npz = _d() / "tesis" / f"{key}.npz"
    if npz.exists():
        d = np.load(npz)
        ids, A = d["ids"], d["assign"]
        cor = _corpus()
        for c in sorted(set(A.tolist()), key=lambda c: -(A == c).sum()):
            sel = ids[A == c]
            lab = llm.get(str(int(c))) or {}
            ej = []
            qq = ",".join(map(str, sel[:muestras].tolist()))
            for doc, txt in cor.execute(
                    f"SELECT doc_path, substr(replace(content, char(10), ' '), 1, 220) "
                    f"FROM considerandos_chunks WHERE rowid IN ({qq})"):
                fe = con.execute("SELECT fecha, rol, caratulado, tribunal FROM doc_fechas "
                                 "WHERE doc_path=?", (doc,)).fetchone()
                ej.append({"doc_path": doc, "extracto": txt,
                           "fecha": fe[0] if fe else None, "rol": fe[1] if fe else None,
                           "caratulado": fe[2] if fe else None, "tribunal": fe[3] if fe else None})
            tesis.append({"cluster": int(c), "n": int(len(sel)),
                          "nombre": lab.get("nombre"),
                          "descripcion": lab.get("descripcion"),
                          "terminos": (tf.get(str(int(c))) or {}).get("terms", []),
                          "ejemplos": ej})
        cor.close()
    con.close()
    return {"id_norma": id_norma, "articulo": articulo, "anios": anios,
            "tesis": tesis, "administrativa": admin}


def _load_considerandos_index():
    global _cidx, _cids
    if _cidx is None:
        _cidx = faiss.read_index(str(_d() / "considerandos.ivf.faiss"), faiss.IO_FLAG_MMAP)
        _cidx.nprobe = _NPROBE
        _cids = np.load(_d() / "considerandos.ids.npy")
    return _cidx, _cids


def considerandos_semantic(q: str, limit: int = 20) -> list[dict]:
    if not q or not q.strip():
        return []
    index, ids = _load_considerandos_index()
    body = json.dumps({"model": _MODEL, "input": [q]}).encode()
    req = urllib.request.Request(_OLLAMA, data=body, headers={"Content-Type": "application/json"})
    v = np.asarray(json.loads(urllib.request.urlopen(req, timeout=30).read())["embeddings"][0],
                   dtype="float32")[None, :]
    faiss.normalize_L2(v)
    D, I = index.search(v, min(limit, 100))
    metas = [int(ids[i]) for i in I[0] if i >= 0]
    scores = {int(ids[i]): round(float(s), 4) for s, i in zip(D[0], I[0]) if i >= 0}
    out = []
    if metas:
        cor = _corpus()
        cit = _citas()
        qq = ",".join(map(str, metas))
        rows = {r[0]: r for r in cor.execute(
            f"SELECT rowid, doc_path, substr(replace(content, char(10), ' '), 1, 300) "
            f"FROM considerandos_chunks WHERE rowid IN ({qq})")}
        for m in metas:
            r = rows.get(m)
            if not r:
                continue
            fe = cit.execute("SELECT fecha, rol, caratulado, tribunal FROM doc_fechas "
                             "WHERE doc_path=?", (r[1],)).fetchone()
            out.append({"chunk_id": m, "score": scores[m], "doc_path": r[1], "extracto": r[2],
                        "fecha": fe[0] if fe else None, "rol": fe[1] if fe else None,
                        "caratulado": fe[2] if fe else None, "tribunal": fe[3] if fe else None})
        cor.close()
        cit.close()
    return out
