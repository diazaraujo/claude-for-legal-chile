#!/usr/bin/env python3
"""Indexa dictámenes SUSESO a docs FTS.

Pass 1: extractos del manifest (property-value_532 = resumen rico) cuando existen.
Pass 2 (cuando --htmls): HTMLs bajados en data/suseso/html/{bucket}/{aid}.html.

Idempotente.
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
SUSESO_ROOT = _REPO_ROOT / "chile/data/suseso"
MANIFEST = SUSESO_ROOT / "manifest.sqlite3"
HTML_ROOT = SUSESO_ROOT / "html"
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-htmls", action="store_true",
                    help="Preferir HTML completo sobre extracto cuando exista")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"no existe {MANIFEST}", flush=True)
        return 1
    m = sqlite3.connect(str(MANIFEST), timeout=30)
    rows = m.execute(
        "SELECT aid, numero, fecha, ano, tema, descriptores, extracto FROM dictamenes"
    ).fetchall()
    m.close()
    print(f"manifest: {len(rows)} dictámenes", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'suseso/%'"
        )
    )

    n_ok = n_skip = n_empty = 0
    t0 = time.time()
    now = time.time()
    for aid, numero, fecha, ano, tema, descriptores, extracto in rows:
        path = f"suseso/{ano or 'sin'}/{aid}.txt"
        if path in existing:
            n_skip += 1
            continue
        body_text = None
        # Pass 1: extracto si existe
        if extracto and len(extracto) > 50:
            body_text = extracto.strip()
        # Pass 2: si --use-htmls y hay HTML local, usar eso
        if args.use_htmls:
            bucket = (aid // 1000) * 1000
            html_path = HTML_ROOT / f"{bucket:07d}" / f"{aid}.html"
            if html_path.exists():
                try:
                    raw = html_path.read_text(encoding="utf-8", errors="replace")
                    cleaned = clean_html(raw)
                    # Reemplazar si HTML tiene MÁS texto
                    if not body_text or len(cleaned) > len(body_text) * 2:
                        body_text = cleaned
                except Exception:
                    pass
        if not body_text or len(body_text) < 100:
            n_empty += 1
            continue
        header = (
            f"SUSESO — Dictamen {numero or aid}\n"
            f"Fecha: {fecha or 'N/A'}\n"
            f"Tema: {tema or 'N/A'}\n"
            f"Descriptores: {descriptores or 'N/A'}\n\n"
        )
        content = header + body_text
        corpus.execute(
            "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
            (path, "suseso", str(ano) if ano else "?", content),
        )
        corpus.execute(
            "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
            (path, now, len(content)),
        )
        n_ok += 1
        if n_ok % 500 == 0:
            corpus.commit()
            print(f"  ok={n_ok} skip={n_skip} empty={n_empty}", flush=True)
    corpus.commit()
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
