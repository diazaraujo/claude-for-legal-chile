#!/usr/bin/env python3
"""Indexa fichas CPLT (FichaCaso.aspx) a docs FTS.

Lee data/cplt/manifest.sqlite3 (rol, fecha_ingreso, tipo, reclamado, estado)
+ HTMLs en data/cplt/html/{bucket}/{id}.html.

Cada doc = 1 ficha de caso con TODOS sus acuerdos/decisiones embedded.
Path sintético cplt/{rol}/{id}.txt.
"""
from __future__ import annotations
import re, sqlite3, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
CPLT_ROOT = _REPO_ROOT / "chile/data/cplt"
MANIFEST = CPLT_ROOT / "manifest.sqlite3"
HTML_ROOT = CPLT_ROOT / "html"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")
_NL = re.compile(r"\n{3,}")
_SCRIPT = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)


def clean_html(html: str) -> str:
    t = _SCRIPT.sub("", html)
    t = _TAG.sub("\n", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&")
         .replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#39;", "'"))
    t = _WS.sub(" ", t)
    t = _NL.sub("\n\n", t)
    return t.strip()


def main() -> int:
    if not MANIFEST.exists():
        print(f"no existe {MANIFEST}", flush=True)
        return 1
    m = sqlite3.connect(str(MANIFEST), timeout=30)
    rows = m.execute(
        "SELECT id, rol, fecha_ingreso, tipo, reclamado, estado FROM casos "
        "WHERE downloaded=1 ORDER BY id"
    ).fetchall()
    m.close()
    print(f"manifest: {len(rows)} fichas downloaded", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'cplt/%'"
        )
    )
    print(f"already indexed: {len(existing)}", flush=True)

    n_ok = n_skip = n_missing = n_empty = 0
    t0 = time.time()
    now = time.time()
    for case_id, rol, fecha, tipo, reclamado, estado in rows:
        # Año del rol C-NNNN-YY
        ano = "?"
        if rol:
            m_rol = re.match(r"[CRA]\d+-(\d+)", rol)
            if m_rol:
                yy = int(m_rol.group(1))
                ano = str(2000 + yy if yy < 50 else 1900 + yy)
        slug = rol.replace("/", "-") if rol else f"id-{case_id}"
        path = f"cplt/{ano}/{slug}-{case_id}.txt"
        if path in existing:
            n_skip += 1
            continue
        bucket = (case_id // 1000) * 1000
        html_path = HTML_ROOT / f"{bucket:07d}" / f"{case_id}.html"
        if not html_path.exists():
            n_missing += 1
            continue
        try:
            raw = html_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            n_missing += 1
            continue
        text = clean_html(raw)
        if len(text) < 200:
            n_empty += 1
            continue
        header = (
            f"CPLT — Ficha del Caso {rol or case_id}\n"
            f"ID interno: {case_id}\n"
            f"Fecha ingreso: {fecha or 'N/A'}\n"
            f"Tipo: {tipo or 'N/A'}\n"
            f"Reclamado: {reclamado or 'N/A'}\n"
            f"Estado: {estado or 'N/A'}\n\n"
        )
        content = header + text
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "cplt", ano, content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % 2000 == 0:
            corpus.commit()
            el = time.time() - t0
            rate = n_ok / el if el > 0 else 0
            print(f"  ok={n_ok} skip={n_skip} missing={n_missing} empty={n_empty} "
                  f"rate={rate:.0f}/s", flush=True)
    corpus.commit()
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} "
          f"missing={n_missing} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
