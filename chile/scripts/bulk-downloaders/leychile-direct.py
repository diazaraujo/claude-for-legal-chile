#!/usr/bin/env python3
"""Downloader DIRECTO de leychile desde la IP del Mac (sin Zyte, gratis), EN PARALELO
al de Zyte. Toma pendientes ORDER BY id_norma ASC (Zyte va DESC) → se cruzan al medio.
Conservador (pocos workers + rate) + circuit-breaker: si N fallos/blocks seguidos,
pausa para no quemar la IP. ADITIVO: solo marca downloaded/ok; nunca marca terminal
(dead/ban) → si algo falla queda NULL y lo toma Zyte. Coordina vía dest.exists()+manifest.
"""
import sqlite3, urllib.request, threading, time, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma="
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16 Safari/605.1.15"
DB = "data/leychile/manifest.sqlite3"
OUT = Path("data/leychile")
RATE = 0.4          # sleep por request por worker
WORKERS = 4
CB_THRESH = 12      # fallos/blocks seguidos => probable WAF
CB_PAUSE = 600      # pausa 10 min y reintenta

lock = threading.Lock()
S = {"ok": 0, "dead": 0, "miss": 0, "err": 0}
CB = {"consec": 0, "until": 0.0}

def _maybe_pause():
    if CB["consec"] >= CB_THRESH:
        CB["until"] = time.time() + CB_PAUSE; CB["consec"] = 0
        print(f"[CB] {CB_THRESH} fallos seguidos → pausa {CB_PAUSE}s · {time.strftime('%H:%M:%S')}", flush=True)

def fetch(nid, timeout=12):
    req = urllib.request.Request(BASE + str(nid), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def mark_ok(nid, size):
    c = sqlite3.connect(DB, timeout=60); c.execute("PRAGMA busy_timeout=60000")
    c.execute("UPDATE normas SET downloaded=1, size=?, status='ok' WHERE id_norma=?", (size, nid))
    c.commit(); c.close()

def mark_stub(nid, size):
    # respuesta vacía = norma muerta (consistente con la lógica Zyte del proyecto).
    # Limpia el muro de IDs viejas-vacías que Zyte (DESC) nunca alcanza.
    c = sqlite3.connect(DB, timeout=60); c.execute("PRAGMA busy_timeout=60000")
    c.execute("UPDATE normas SET downloaded=0, size=?, status='stub' WHERE id_norma=?", (size, nid))
    c.commit(); c.close()

def worker(row):
    nid, tipo = row
    while time.time() < CB["until"]:
        time.sleep(5)
    dest = OUT / tipo / f"{nid}.xml"
    if dest.exists() and dest.stat().st_size > 500:
        mark_ok(nid, dest.stat().st_size)
        with lock: S["ok"] += 1
        return
    time.sleep(RATE)
    try:
        body = fetch(nid)
    except Exception:
        with lock: S["err"] += 1; CB["consec"] += 1; _maybe_pause()
        return
    if body and b"<Norma" in body[:300]:
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(body)
        mark_ok(nid, len(body))
        with lock: S["ok"] += 1; CB["consec"] = 0
    elif body is not None and len(body) < 120:
        # vacío/stub → norma muerta (no es bloqueo): marca terminal y NO cuenta para CB
        mark_stub(nid, len(body or b""))
        with lock: S["dead"] += 1; CB["consec"] = 0
    else:
        # HTML/no-Norma no-vacío → posible bloqueo WAF: deja NULL y cuenta para CB
        with lock: S["miss"] += 1; CB["consec"] += 1; _maybe_pause()

def one_pass():
    c = sqlite3.connect(DB)
    pend = [(r[0], r[1]) for r in c.execute(
        "SELECT id_norma,tipo FROM normas WHERE downloaded=0 AND status IS NULL ORDER BY id_norma ASC")]
    c.close()
    if not pend:
        return 0, 0
    before = S["ok"]
    t0 = time.time(); done = 0
    print(f"[direct] pasada · pending={len(pend)} ASC · {time.strftime('%H:%M:%S')}", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for _ in ex.map(worker, pend):
            done += 1
            if done % 300 == 0:
                el = max(time.time() - t0, 0.1)
                print(f"  {done}/{len(pend)} ok={S['ok']} dead={S['dead']} miss={S['miss']} err={S['err']} · {done/el:.2f}/s · {time.strftime('%H:%M:%S')}", flush=True)
    return len(pend), S["ok"] - before

def main():
    print(f"[direct] arranque · workers={WORKERS} rate={RATE}s · {time.strftime('%H:%M:%S')}", flush=True)
    while True:
        pend, got = one_pass()
        if pend == 0:
            print("[direct] sin pendientes NULL → nada que hacer (Zyte cierra la cola)", flush=True); break
        if got == 0:
            print(f"[direct] pasada sin descargas (bloqueo/cola Zyte) → sleep 300s · {time.strftime('%H:%M:%S')}", flush=True)
            time.sleep(300)
    print(f"[direct] FIN ok={S['ok']} dead={S['dead']} miss={S['miss']} err={S['err']}", flush=True)

if __name__ == "__main__":
    main()
