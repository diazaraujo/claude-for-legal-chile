#!/usr/bin/env python3
"""Extracción estructurada de sentencias chilenas usando Claude Haiku.

Para cada sentencia (TC, TC-moderno, TDLC, TDPI, tribunales-ambientales),
pide a Haiku que devuelva JSON con:
  - partes (recurrente, recurrido, otros)
  - rol
  - fecha
  - materia (qué se discute)
  - considerandos (lista numerada con texto resumido)
  - decision (parte resolutiva)
  - votos_disidentes (lista de {miembro, fundamento})
  - holding (regla jurídica establecida, 1-2 frases)
  - normas_citadas (lista de citas literales detectadas en el texto)

Output: tabla `sentencias_estructura(doc_path, json, model, ts, error)`.
Idempotente: skip si doc_path ya procesado.

Usage:
  python3 extract-sentencias-structure.py --sources tc --max 5  # smoke
  python3 extract-sentencias-structure.py --sources tc,tdlc,tdpi,tc-moderno,tribunales-ambientales
"""
from __future__ import annotations
import argparse, json, os, re, sqlite3, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_STATS = {"ok": 0, "skip": 0, "err": 0, "empty": 0}
_LOCK = Lock()

PROMPT_TEMPLATE = """Eres un asistente legal chileno experto. Recibes el texto de una sentencia o resolución de tribunal chileno. Extrae los siguientes campos en JSON estricto (sin prosa antes ni después).

Reglas:
- NO inventes datos. Si un campo no aparece en el texto, deja "" o [].
- Usa español chileno formal (NO rioplatense, NO portugués).
- Cita LITERAL las normas citadas (ej. "Constitución Política, artículo 19 N° 2"). Si no se cita ninguna norma específica, deja [].
- holding = regla jurídica establecida por el tribunal, 1-2 frases.
- considerandos: ítems con num (string, ej "1°" o "Décimo") y resumen ≤2 frases por considerando.

Schema JSON exacto:
{{
  "rol": "string",
  "fecha": "string YYYY-MM-DD",
  "tribunal": "string",
  "partes": {{
    "recurrente": "string",
    "recurrido": "string",
    "otros": ["string"]
  }},
  "materia": "string",
  "considerandos": [
    {{"num": "string", "resumen": "string"}}
  ],
  "decision": "string",
  "votos_disidentes": [
    {{"miembro": "string", "fundamento": "string"}}
  ],
  "holding": "string",
  "normas_citadas": ["string"]
}}

Texto de la sentencia ({fuente}):
---
{texto}
---

Responde SOLO el JSON, sin markdown fences ni comentarios."""


def init_table(db: Path) -> None:
    conn = sqlite3.connect(str(db), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sentencias_estructura (
            doc_path TEXT PRIMARY KEY,
            source TEXT,
            json TEXT,
            model TEXT,
            ts REAL,
            error TEXT,
            input_chars INTEGER,
            output_chars INTEGER
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sentest_source ON sentencias_estructura(source)"
    )
    conn.commit()
    conn.close()


def extract_one(
    doc_path: str, source: str, db_path: str, model: str,
    max_input_chars: int = 30000
) -> str:
    try:
        text = Path(doc_path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        with _LOCK: _STATS["err"] += 1
        return "err_read"
    if len(text) < 200:
        with _LOCK: _STATS["empty"] += 1
        return "too_small"

    text_truncated = text[:max_input_chars]
    prompt = PROMPT_TEMPLATE.format(fuente=source, texto=text_truncated)

    try:
        from anthropic import Anthropic
    except ImportError:
        with _LOCK: _STATS["err"] += 1
        return "no_anthropic"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        with _LOCK: _STATS["err"] += 1
        return "no_key"

    try:
        client = Anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        output = resp.content[0].text.strip()
    except Exception as e:
        with _LOCK: _STATS["err"] += 1
        msg = f"haiku_err:{type(e).__name__}"
        _persist_error(db_path, doc_path, source, model, msg)
        return msg

    if output.startswith("```"):
        output = re.sub(r"^```(?:json)?\n?", "", output)
        output = re.sub(r"\n?```\s*$", "", output)
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as e:
        with _LOCK: _STATS["err"] += 1
        _persist_error(db_path, doc_path, source, model, f"json_decode:{e}")
        return "json_invalid"

    _persist_ok(db_path, doc_path, source, model, parsed,
                len(text_truncated), len(output))
    with _LOCK: _STATS["ok"] += 1
    return "ok"


def _persist_ok(
    db_path: str, doc_path: str, source: str, model: str,
    parsed: dict, input_chars: int, output_chars: int,
) -> None:
    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.execute(
            "INSERT OR REPLACE INTO sentencias_estructura("
            "doc_path, source, json, model, ts, error, input_chars, output_chars"
            ") VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
            (doc_path, source, json.dumps(parsed, ensure_ascii=False),
             model, time.time(), input_chars, output_chars),
        )
        c.commit()
    finally:
        c.close()


def _persist_error(
    db_path: str, doc_path: str, source: str, model: str, error: str
) -> None:
    c = sqlite3.connect(db_path, timeout=60)
    try:
        c.execute(
            "INSERT OR REPLACE INTO sentencias_estructura("
            "doc_path, source, json, model, ts, error, input_chars, output_chars"
            ") VALUES (?, ?, NULL, ?, ?, ?, NULL, NULL)",
            (doc_path, source, model, time.time(), error),
        )
        c.commit()
    finally:
        c.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--sources", default="tc,tc-moderno,tdlc,tdpi,tribunales-ambientales")
    parser.add_argument("--max", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--smoke", action="store_true",
                        help="Smoke test: print JSON output of each OK doc")
    args = parser.parse_args()

    init_table(Path(args.db))

    sources = [s.strip() for s in args.sources.split(",")]

    conn = sqlite3.connect(args.db, timeout=60)
    placeholders = ",".join("?" * len(sources))
    rows = conn.execute(
        f"SELECT d.path, d.source FROM docs d "
        f"WHERE d.source IN ({placeholders}) "
        f"AND d.path NOT IN ("
        f"  SELECT doc_path FROM sentencias_estructura WHERE error IS NULL"
        f") "
        f"ORDER BY RANDOM() ",
        sources,
    ).fetchall()
    conn.close()

    if args.max > 0:
        rows = rows[:args.max]

    print(f"Sentencias pendientes: {len(rows)} | sources={sources}", flush=True)
    print(f"Workers: {args.workers} | model={args.model}", flush=True)
    if not rows:
        return 0

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(extract_one, p, s, args.db, args.model): (p, s)
            for p, s in rows
        }
        for i, fut in enumerate(as_completed(futures), 1):
            try: result = fut.result()
            except Exception: result = "exception"
            if args.smoke and result == "ok":
                p, s = futures[fut]
                c = sqlite3.connect(args.db, timeout=60)
                row = c.execute(
                    "SELECT json FROM sentencias_estructura WHERE doc_path = ?",
                    (p,),
                ).fetchone()
                c.close()
                if row:
                    parsed = json.loads(row[0])
                    print(f"\n=== {s} | {Path(p).name} ===", flush=True)
                    print(json.dumps(parsed, ensure_ascii=False, indent=2)[:1800],
                          flush=True)
            if i % 50 == 0 or i == len(rows):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(rows) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(rows)}] "
                    f"ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"err={_STATS['err']} empty={_STATS['empty']} "
                    f"| {rate:.2f}/s eta={eta/60:.0f}min",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | {_STATS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
