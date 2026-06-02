#!/usr/bin/env python3
"""
CHEQUEO DE FRESCURA — operacionaliza "no declarar actualizado sin evidencia".
Para cada fuente calcula cuándo entró data nueva por última vez (mtime del archivo
más reciente, o max fecha del manifest/tabla) y la compara con su cadencia esperada.
Alerta (🔴) las fuentes vencidas. CPU/solo lectura. Va en refresh-downstream §5.

Cuenta días HÁBILES para las diarias (no falso-positivo por finde/feriado; ver
reference_chile_fiestas_patrias_semana).

Uso: python3 scripts/refresh/check-frescura.py [--json]
"""
import argparse, json, os, sqlite3, time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# cadencia esperada por fuente (de refresh.py) + umbral de alerta en días corridos
CADENCE = {
 "daily":   dict(umbral=4,  fuentes=["diario-oficial","boletin-concursal","pjud"]),
 "weekly":  dict(umbral=10, fuentes=["leychile","cgr-dictamenes","cplt","suseso","dt","tta",
                                     "tdlc","fne","sii-oficios","tribunal-ambiental","recursos-administrativos"]),
 "monthly": dict(umbral=40, fuentes=["doctrina","tc","cmf","sii-normativa","historia-ley","tribunales-ambientales",
                                     "sec","subtel","sernac","dga","subtrans","cde","servel","sag-normativa",
                                     "indh","dpp","cam-santiago","tcp","tricel","tdpi","tc-moderno","sii","sii-oficios","spensiones","siss","uaf","superdesalud","supereduc","scj"]),
 "static":  dict(umbral=10**6, fuentes=["diario-oficial-historico"]),
 "manual":  dict(umbral=60, fuentes=["aduanas"]),
}
SRC_CAD = {f:cad for cad,d in CADENCE.items() for f in d["fuentes"]}
UMBRAL  = {cad:d["umbral"] for cad,d in CADENCE.items()}

CONTENT_EXT = {".txt",".pdf",".xml",".html",".htm",".json",".gz",".csv","PDF"}
def newest_mtime(d: Path):
    """mtime (epoch) del archivo de CONTENIDO más reciente (no wal/shm/lock/.DS_Store)."""
    newest = 0
    try:
        for p in d.rglob("*"):
            if not p.is_file(): continue
            n = p.name
            if n.startswith(".") or n.endswith(("-wal","-shm","-journal",".part",".tmp")): continue
            if p.suffix not in CONTENT_EXT and not n.endswith(".json.gz"): continue
            m = p.stat().st_mtime
            if m > newest: newest = m
    except Exception:
        return None
    return newest or None

def business_days_since(epoch):
    """días hábiles (excluye sáb/dom) entre el mtime y hoy."""
    d0 = datetime.fromtimestamp(epoch).date(); d1 = date.today()
    if d1 <= d0: return 0
    n = 0; cur = d0
    while cur < d1:
        cur += timedelta(days=1)
        if cur.weekday() < 5: n += 1
    return n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    rows = []
    for d in sorted(DATA.iterdir()):
        if not d.is_dir() or d.name == "_index": continue
        name = d.name
        mt = newest_mtime(d)
        if mt is None: continue
        cad = SRC_CAD.get(name, "monthly")
        dias_corridos = (date.today() - datetime.fromtimestamp(mt).date()).days
        dias_habiles = business_days_since(mt)
        umbral = UMBRAL.get(cad, 40)
        # diarias: usar días hábiles (no penalizar finde/feriado)
        medida = dias_habiles if cad == "daily" else dias_corridos
        vencida = medida > umbral and cad not in ("static","manual")
        rows.append(dict(fuente=name, cadencia=cad, ultima=datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M"),
                         dias=dias_corridos, dias_habiles=dias_habiles, umbral=umbral, vencida=vencida))
    rows.sort(key=lambda r:(not r["vencida"], r["cadencia"], -r["dias"]))
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    vencidas = [r for r in rows if r["vencida"]]
    print(f"FRESCURA · {len(rows)} fuentes · {len(vencidas)} 🔴 vencidas · {date.today()}\n")
    print(f"{'FUENTE':<26}{'cadencia':>9}{'últ.update':>18}{'días':>6}{'umbral':>7}  estado")
    for r in rows:
        flag = "🔴 VENCIDA" if r["vencida"] else "🟢"
        print(f"{r['fuente']:<26}{r['cadencia']:>9}{r['ultima']:>18}{r['dias']:>6}{r['umbral']:>7}  {flag}")
    if vencidas:
        print(f"\n⚠ {len(vencidas)} fuentes vencidas → correr su refresh: " + ", ".join(r["fuente"] for r in vencidas))
    else:
        print("\n✓ Todas las fuentes dentro de su cadencia.")

if __name__ == "__main__":
    main()
