#!/usr/bin/env python3
# std:input -
# std:output FichaCaso HTMLs + manifest CPLT
# std:deps stdlib + ThreadPoolExecutor
"""
Bulk download CPLT (Consejo para la Transparencia) — fichas de caso.

Portal: extranet.consejotransparencia.cl/Web_SCW2/Paginab/FichaCaso.aspx?ID=N

Los IDs son SECUENCIALES desde 1 (C1-09, ingresado 2009) hasta ~117800
(C6720-26, mayo 2026). Se enumeran en paralelo y se guarda cada ficha HTML
+ metadata extraída (rol, fecha ingreso, reclamado, tipo, estado).

Fase 1 (--enum): GET por ID, extrae metadata, guarda HTML local.
Fase 2 (post-enum): indexar HTMLs a corpus FTS.

NOTA: cada FichaCaso es un caso completo con TODOS los acuerdos/decisiones
que el Consejo ha emitido sobre ese rol. NO requiere ninguna 2da request.
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = _REPO_ROOT / "chile/data/cplt"

BASE = "https://extranet.consejotransparencia.cl/Web_SCW2/Paginab/FichaCaso.aspx"
UA = "claude-legal-chile/0.8 bulk-cplt"

_STATS = {"ok": 0, "skip": 0, "not_found": 0, "err": 0, "bytes": 0}
_LOCK = Lock()


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS casos ("
        "id INTEGER PRIMARY KEY, rol TEXT, fecha_ingreso TEXT, "
        "tipo TEXT, reclamado TEXT, estado TEXT, html_size INTEGER, "
        "downloaded INTEGER DEFAULT 0, status TEXT)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_casos_rol ON casos(rol)")
    conn.commit()
    return conn


def parse_ficha(html: str) -> dict:
    """Extrae metadata principal del HTML de FichaCaso.aspx."""
    out = {"rol": None, "fecha_ingreso": None, "tipo": None,
           "reclamado": None, "estado": None}
    m = re.search(r"\b([CRA]\d{1,5}-\d{2,4})\b", html)
    if m: out["rol"] = m.group(1)
    # Fecha ingreso típicamente "Fecha de ingreso: DD/MM/YYYY"
    m = re.search(r"Fecha\s*(?:de\s*)?[Ii]ngreso\s*[:\-]?\s*([0-9./\-]+)", html)
    if m: out["fecha_ingreso"] = m.group(1).strip()
    # Tipo
    m = re.search(r"Tipo\s*(?:de\s*)?[Cc]aso\s*[:\-]?\s*</[^>]+>\s*([^<]+)", html)
    if m: out["tipo"] = m.group(1).strip()
    # Reclamado / Organismo
    m = re.search(r"(?:Reclamado|Organismo)\s*[:\-]?\s*</[^>]+>\s*([^<]+)", html)
    if m: out["reclamado"] = m.group(1).strip()[:200]
    # Estado
    m = re.search(r"Estado\s*(?:del\s*caso)?\s*[:\-]?\s*</[^>]+>\s*([^<]+)", html)
    if m: out["estado"] = m.group(1).strip()
    return out


def fetch_one(case_id: int, out_dir: Path) -> tuple[int, str, dict]:
    """Returns (case_id, status, metadata)."""
    # Path por bucket de 1000
    bucket = (case_id // 1000) * 1000
    sub = out_dir / "html" / f"{bucket:07d}"
    sub.mkdir(parents=True, exist_ok=True)
    dest = sub / f"{case_id}.html"
    if dest.exists() and dest.stat().st_size > 1000:
        with _LOCK:
            _STATS["skip"] += 1
        return (case_id, "skip", {"html_size": dest.stat().st_size})
    url = f"{BASE}?ID={case_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        with _LOCK:
            _STATS["err"] += 1
        return (case_id, f"http-{e.code}", {})
    except Exception:
        with _LOCK:
            _STATS["err"] += 1
        return (case_id, "err", {})
    html = body.decode("utf-8", "replace")
    meta = parse_ficha(html)
    # Si rol es None y len pequeño → not found (página vacía)
    if not meta.get("rol") and len(html) < 35000:
        with _LOCK:
            _STATS["not_found"] += 1
        return (case_id, "not-found", {"html_size": len(html)})
    # Guardar HTML
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(body)
    tmp.rename(dest)
    meta["html_size"] = len(html)
    with _LOCK:
        _STATS["ok"] += 1
        _STATS["bytes"] += len(html)
    return (case_id, "ok", meta)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUTPUT_ROOT))
    ap.add_argument("--from-id", type=int, default=1)
    ap.add_argument("--to-id", type=int, default=118000)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    conn = init_manifest(out / "manifest.sqlite3")

    print(f"=== CPLT bulk ===", flush=True)
    print(f"output: {out}  workers: {args.workers}", flush=True)
    print(f"rango IDs: {args.from_id} a {args.to_id} ({args.to_id-args.from_id+1} casos)",
          flush=True)

    # IDs ya procesados (downloaded=1 o status=not-found)
    done_ids = set(
        r[0] for r in conn.execute(
            "SELECT id FROM casos WHERE downloaded=1 OR status='not-found'"
        )
    )
    print(f"ya procesados: {len(done_ids)}", flush=True)

    ids = [i for i in range(args.from_id, args.to_id + 1) if i not in done_ids]
    print(f"a procesar: {len(ids)}", flush=True)

    t0 = time.time()
    last_print = t0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, i, out): i for i in ids}
        done = 0
        for fut in as_completed(futs):
            case_id, status, meta = fut.result()
            conn.execute(
                "INSERT OR REPLACE INTO casos"
                "(id, rol, fecha_ingreso, tipo, reclamado, estado, html_size, "
                "downloaded, status) VALUES (?,?,?,?,?,?,?,?,?)",
                (case_id, meta.get("rol"), meta.get("fecha_ingreso"),
                 meta.get("tipo"), meta.get("reclamado"), meta.get("estado"),
                 meta.get("html_size"), 1 if status == "ok" else 0, status),
            )
            done += 1
            if done % 100 == 0 or time.time() - last_print > 15:
                conn.commit()
                with _LOCK:
                    s = dict(_STATS)
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                eta = (len(ids) - done) / rate / 60 if rate > 0 else 0
                print(f"  done={done}/{len(ids)} ok={s['ok']} skip={s['skip']} "
                      f"not_found={s['not_found']} err={s['err']} "
                      f"MB={s['bytes']/1e6:.0f} rate={rate:.1f}/s ETA={eta:.1f}min",
                      flush=True)
                last_print = time.time()
    conn.commit()
    print(f"\n[DONE] {time.time()-t0:.0f}s | {dict(_STATS)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
