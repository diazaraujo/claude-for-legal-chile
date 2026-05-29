#!/usr/bin/env python3
# std:input -
# std:output JSON+manifest dictámenes SUSESO + HTMLs opcionales
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download SUSESO (Superintendencia de Seguridad Social) — dictámenes.

API REAL descubierta vía Playwright capture (no el portal www.suseso.gob.cl
directo, sino el motor Newtenberg backend):

  GET https://suseso-engine.newtenberg.com/mod/find/cgi/find.cgi?
       action=jsonquery&engine=SwisheFind&rpp=20000&cid=512&iid=612
       &searchon=aid&properties=546,523,532,620,548&json=1
       &keywords=*&start=0&group=1&show_ancestors=1
       &searchmode=and&pvid_and=500:515
       &aditional_query=' cid=(512)' -s property-value.546.iso8601 desc title desc

`keywords=*` (wildcard) saca TODO el corpus: 16.021 dictámenes en una sola
call (~14 MB JSON, ~100s).

Cada item incluye:
  - aid (article ID), hl1 (número dictamen "Dictamen O-01-S-02139-2026")
  - title, property-value_546_iso8601 (fecha)
  - property-value_532 (texto resumen rico del dictamen)
  - property-value_548_name, _620_name (descriptores/temas)

Fase 1: GET único API + persiste manifest con extractos.
Fase 2 (opcional --htmls): bajar cada `/606/w3-article-{aid}.html` para texto
completo del dictamen (solo si extracto no basta).
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/suseso"

API = ("https://suseso-engine.newtenberg.com/mod/find/cgi/find.cgi"
       "?action=jsonquery&engine=SwisheFind&cid=512&iid=612"
       "&pnid_search=&searchon=aid&properties=546,523,532,620,548&json=1"
       "&pnid546_desde=&pnid546_hasta=&group=1&show_ancestors=1"
       "&searchmode=and&pvid_and=500%3A515"
       "&aditional_query=%27%20cid%3D(512)%27%20-s"
       "%20property-value.546.iso8601%20desc%20title%20desc")
ARTICLE_URL = "https://www.suseso.gob.cl/612/w3-article-{aid}.html"  # channel 512=Normativa y jurisprudencia, iid 612
UA = "claude-legal-chile/0.8 bulk-suseso"

_STATS = {"htmls_ok": 0, "htmls_err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dictamenes ("
        "aid INTEGER PRIMARY KEY, numero TEXT, fecha TEXT, ano INTEGER, "
        "tema TEXT, descriptores TEXT, "
        "destinatario_tipo TEXT, extracto TEXT, html_path TEXT, "
        "downloaded_html INTEGER DEFAULT 0)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_ano ON dictamenes(ano)")
    conn.commit()
    return conn


def fetch_corpus(rpp: int = 20000) -> list:
    url = API + f"&keywords=*&rpp={rpp}&start=0"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Referer": "https://www.suseso.gob.cl/",
    })
    with urllib.request.urlopen(req, timeout=600) as r:
        j = json.loads(r.read())
    return j.get("articles", {}).get("results", [])


def upsert_manifest(conn: sqlite3.Connection, items: list) -> int:
    n = 0
    for it in items:
        try:
            aid = int(it.get("aid") or it.get("id"))
        except (TypeError, ValueError):
            continue
        numero = it.get("hl1")
        fecha = it.get("property-value_546_iso8601")
        ano = None
        if fecha:
            try: ano = int(fecha[:4])
            except: ano = None
        tema = it.get("property-value_620_name")
        descriptores = it.get("property-value_548_name")
        destinatario = it.get("property-value_523_name")
        extracto = it.get("property-value_532")
        conn.execute(
            "INSERT OR REPLACE INTO dictamenes "
            "(aid, numero, fecha, ano, tema, descriptores, destinatario_tipo, extracto) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (aid, numero, fecha, ano, tema, descriptores, destinatario, extracto),
        )
        n += 1
    conn.commit()
    return n


def fetch_html(aid: int, out_dir: Path) -> tuple[int, bool, int]:
    bucket = (aid // 1000) * 1000
    sub = out_dir / "html" / f"{bucket:07d}"
    sub.mkdir(parents=True, exist_ok=True)
    dest = sub / f"{aid}.html"
    if dest.exists() and dest.stat().st_size > 500:
        return (aid, True, dest.stat().st_size)
    url = ARTICLE_URL.format(aid=aid)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
    except Exception:
        with _LOCK:
            _STATS["htmls_err"] += 1
        return (aid, False, 0)
    if len(body) < 500:
        with _LOCK:
            _STATS["htmls_err"] += 1
        return (aid, False, 0)
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(body)
    tmp.rename(dest)
    with _LOCK:
        _STATS["htmls_ok"] += 1
        _STATS["bytes"] += len(body)
    return (aid, True, len(body))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUTPUT_ROOT))
    ap.add_argument("--rpp", type=int, default=20000)
    ap.add_argument("--htmls", action="store_true",
                    help="Adicionalmente bajar w3-article-N.html de cada dictamen")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== SUSESO bulk ===", flush=True)
    print(f"output: {out}", flush=True)
    print(f"\nFase 1: fetching API JSON con keywords=*...", flush=True)
    t0 = time.time()
    items = fetch_corpus(rpp=args.rpp)
    print(f"  items: {len(items)} ({time.time()-t0:.1f}s)", flush=True)
    n = upsert_manifest(conn, items)
    print(f"  manifest upserts: {n}", flush=True)

    counts = conn.execute(
        "SELECT ano, COUNT(*) FROM dictamenes WHERE ano IS NOT NULL "
        "GROUP BY ano ORDER BY ano"
    ).fetchall()
    print("Por año:")
    for a, c in counts:
        print(f"  {a}: {c}")

    if args.htmls:
        print(f"\nFase 2: bajando HTML de cada dictamen...", flush=True)
        rows = conn.execute(
            "SELECT aid FROM dictamenes WHERE downloaded_html=0 ORDER BY aid"
        ).fetchall()
        print(f"  a procesar: {len(rows)}", flush=True)
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(fetch_html, r[0], out): r[0] for r in rows}
            done = 0
            for fut in as_completed(futs):
                aid, ok, size = fut.result()
                if ok:
                    conn.execute("UPDATE dictamenes SET downloaded_html=1 WHERE aid=?", (aid,))
                done += 1
                if done % 100 == 0:
                    conn.commit()
                    with _LOCK:
                        s = dict(_STATS)
                    el = time.time() - t0
                    rate = done / el if el > 0 else 0
                    eta = (len(rows) - done) / rate / 60 if rate > 0 else 0
                    print(f"  done={done}/{len(rows)} {s} rate={rate:.1f}/s ETA={eta:.0f}min",
                          flush=True)
        conn.commit()
        print(f"\n[FASE 2 DONE] {time.time()-t0:.0f}s | {dict(_STATS)}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
