#!/usr/bin/env python3
"""Trae la Declaración de Patrimonio e Intereses (Ley 20.880) PÚBLICA de cada juez
desde InfoProbidad (CPLT) — fuente oficial pública, solo el funcionario.

Resumen AGREGADO (sin direcciones ni domicilio): N inmuebles + avalúo fiscal total,
N vehículos + avalúo total, N pasivos, fecha de la declaración, cargo. Esto es
publicable: es lo que el funcionario declara públicamente por ley.

Pipeline:
  1) descarga el Listado (todas las declaraciones, ~37MB) y arma juez_key→IdDeclaracion
     (cruzando por nombre con juez_perfil, solo cargos JUEZ/MINISTRO/FISCAL JUDICIAL).
  2) baja el detalle /Declaracion/Declaracion?ID= de cada juez (paralelo) y agrega.
Escribe tabla juez_declaracion en jueces_enriched.sqlite3.

Uso: python3 scripts/perfiles/fetch-declaraciones-patrimonio.py [--workers 8] [--limit N]
"""
import argparse, json, re, sqlite3, unicodedata, html as H
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import requests

PERF = "data/_index/perfiles.sqlite3"
OUT = "data/_index/jueces_enriched.sqlite3"
LISTADO = "https://www.infoprobidad.cl/Home/Listado"
DETALLE = "https://www.infoprobidad.cl/Declaracion/Declaracion?ID="
JCARGOS = {"JUEZ", "MINISTRO", "FISCAL JUDICIAL"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS juez_declaracion(
  juez_key TEXT PRIMARY KEY,
  id_declaracion INTEGER, fecha_declaracion TEXT, cargo TEXT,
  n_inmuebles INTEGER, avaluo_inmuebles INTEGER,
  n_vehiculos INTEGER, avaluo_vehiculos INTEGER,
  n_valores INTEGER, n_pasivos INTEGER, fetched_at TEXT
);
"""

SCHEMA_HIST = """
CREATE TABLE IF NOT EXISTS juez_declaracion_hist(
  id_declaracion INTEGER PRIMARY KEY, juez_key TEXT, fecha_declaracion TEXT,
  tipo TEXT, cargo TEXT, n_inmuebles INTEGER, avaluo_inmuebles INTEGER,
  n_vehiculos INTEGER, avaluo_vehiculos INTEGER, n_valores INTEGER, n_pasivos INTEGER, fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_jdh_juez ON juez_declaracion_hist(juez_key);
"""


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper()).strip()


def money(s):
    m = re.search(r"[\d.]+", s or "")
    return int(m.group(0).replace(".", "")) if m else 0


def build_map():
    print("# descargando Listado InfoProbidad (~37MB)...", flush=True)
    r = requests.get(LISTADO, headers=HEADERS, timeout=120)
    r.raise_for_status()
    big = next(l for l in r.text.splitlines() if "IdDeclaracion" in l and len(l) > 100000)
    arr, _ = json.JSONDecoder().raw_decode(big[big.find("[{"):])
    from collections import defaultdict
    idx = defaultdict(list)
    for d in arr:
        if (d.get("ServicioEntidad") or "") != "PODER JUDICIAL":
            continue
        if (d.get("Cargo") or "") not in JCARGOS:
            continue
        nom = norm(f"{d.get('Nombres','')} {d.get('ApellidoPaterno','')} {d.get('ApellidoMaterno','')}")
        idx[nom].append((d["IdDeclaracion"], d.get("FechaDeclaracion", ""),
                         d.get("TipoDeclaracion", ""), d.get("Cargo")))
    for nom in idx:
        idx[nom].sort(key=lambda x: x[1], reverse=True)  # más reciente primero
    pc = sqlite3.connect(f"file:{PERF}?mode=ro", uri=True)
    mp = {}
    for k, n in pc.execute("SELECT juez_key,juez FROM juez_perfil WHERE juez IS NOT NULL AND n_causas>=1"):
        if norm(n) in idx:
            mp[k] = idx[norm(n)]
    pc.close()
    tot = sum(len(v) for v in mp.values())
    print(f"# jueces con declaración: {len(mp)} · total declaraciones (histórico): {tot}", flush=True)
    return mp


def parse_detalle(text):
    tables = re.findall(r"<table.*?</table>", text, re.S)
    n_inm = av_inm = n_veh = av_veh = n_val = n_pas = 0
    for t in tables:
        d = {}
        for row in re.findall(r"<tr.*?</tr>", t, re.S):
            c = [H.unescape(re.sub(r"<[^>]+>", "", x)).replace("\xa0", " ").strip()
                 for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if len(c) >= 2 and c[0] and c[0] not in d:
                d[c[0]] = c[1]
        if "Región" in d and "Avalúo Fiscal" in d:
            n_inm += 1; av_inm += money(d.get("Avalúo Fiscal"))
        elif "Tipo de vehículo" in d:
            n_veh += 1; av_veh += money(d.get("Avalúo fiscal"))
        elif any(k.startswith("Título") for k in d):
            n_val += 1
        elif any(k.startswith("Tipo de obligación") for k in d):
            n_pas += 1
    return n_inm, av_inm, n_veh, av_veh, n_val, n_pas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--history", action="store_true", help="baja TODAS las declaraciones (timeline), no solo la última")
    args = ap.parse_args()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    mp = build_map()  # juez_key -> [(id, fecha, tipo, cargo), ...] desc por fecha

    if args.history:
        tasks = [(k, idd, fecha, tipo, cargo) for k, lst in mp.items() for (idd, fecha, tipo, cargo) in lst]
    else:
        tasks = [(k, lst[0][0], lst[0][1], lst[0][2], lst[0][3]) for k, lst in mp.items() if lst]
    if args.limit:
        tasks = tasks[:args.limit]

    out = sqlite3.connect(OUT, timeout=120)
    out.execute("PRAGMA busy_timeout=120000")
    out.execute("PRAGMA journal_mode=WAL")
    out.executescript(SCHEMA_HIST if args.history else SCHEMA)
    lock = Lock()
    ok = err = 0
    n_total = len(tasks)
    sess = requests.Session()
    sess.headers.update(HEADERS)

    def fetch(t):
        key, idd, fecha, tipo, cargo = t
        try:
            r = sess.get(DETALLE + str(idd), timeout=30)
            r.raise_for_status()
            return key, idd, fecha, tipo, cargo, parse_detalle(r.text), None
        except Exception as e:
            return key, idd, fecha, tipo, cargo, None, e

    seen = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(fetch, t) for t in tasks]
        for f in as_completed(futs):
            key, idd, fecha, tipo, cargo, res, exc = f.result()
            seen += 1
            if exc is not None or res is None:
                err += 1
                if err <= 3:
                    print(f"  ! error ({idd}): {exc}")
                continue
            n_inm, av_inm, n_veh, av_veh, n_val, n_pas = res
            with lock:
                if args.history:
                    out.execute("INSERT OR REPLACE INTO juez_declaracion_hist VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                                (idd, key, fecha, tipo, cargo, n_inm, av_inm, n_veh, av_veh, n_val, n_pas, now))
                else:
                    out.execute(
                        "INSERT INTO juez_declaracion VALUES(?,?,?,?,?,?,?,?,?,?,?) "
                        "ON CONFLICT(juez_key) DO UPDATE SET id_declaracion=excluded.id_declaracion,"
                        "fecha_declaracion=excluded.fecha_declaracion,cargo=excluded.cargo,"
                        "n_inmuebles=excluded.n_inmuebles,avaluo_inmuebles=excluded.avaluo_inmuebles,"
                        "n_vehiculos=excluded.n_vehiculos,avaluo_vehiculos=excluded.avaluo_vehiculos,"
                        "n_valores=excluded.n_valores,n_pasivos=excluded.n_pasivos,fetched_at=excluded.fetched_at",
                        (key, idd, fecha, cargo, n_inm, av_inm, n_veh, av_veh, n_val, n_pas, now))
                ok += 1
                if seen % 100 == 0:
                    out.commit()
                    print(f"  [{seen}/{n_total}] ok={ok} err={err}", flush=True)
    out.commit()
    out.close()
    print(f"\nDECLARACIONES OK · {n_total} {'declaraciones histórico' if args.history else 'jueces'} · cargados={ok} err={err}")


if __name__ == "__main__":
    main()
