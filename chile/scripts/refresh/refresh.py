#!/usr/bin/env python3
"""
Orquestador de REFRESH incremental del corpus claude-for-legal-chile.
Ver REFRESH-PLAN.md. Corre el scraper de cada fuente (incremental/idempotente),
verifica el delta REAL (conteo subió, no error), y registra. Cómputo pesado
(embed/LLM) va aparte en refresh-downstream.sh (enigma).

Uso:
  python3 scripts/refresh/refresh.py --source diario-oficial      # una fuente
  python3 scripts/refresh/refresh.py --cadence daily              # todas las diarias
  python3 scripts/refresh/refresh.py --list                       # ver config
Reglas: incremental (cursor), reverse-cronológico, idempotente, verificar-data-real.
"""
import argparse, json, os, sqlite3, subprocess, sys, time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # chile/
os.chdir(ROOT)

def manifest_downloaded(rel_manifest, where="downloaded>=1"):  # >=1 sirve p/ flag 0/1 y p/ pub-count
    p = ROOT / rel_manifest
    if not p.exists(): return None
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=20)
        t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if not r[0].startswith("sqlite")][0]
        n = c.execute(f"SELECT COUNT(*) FROM {t} WHERE {where}").fetchone()[0]
        c.close(); return n
    except Exception:
        return None

def last_date_do():
    """última fecha en el manifest del Diario Oficial (electrónica)."""
    p = ROOT / "data/diario-oficial/manifest.sqlite3"
    if not p.exists(): return None
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=20)
        # date guardada como DD-MM-YYYY (PK). tomar la máxima por orden YYYYMMDD
        rows = [r[0] for r in c.execute("SELECT date FROM descargas")]
        c.close()
        def key(d):
            dd,mm,yy = d.split("-"); return yy+mm+dd
        return max(rows, key=key) if rows else None
    except Exception:
        return None

# CONFIG por fuente: cadence, cómo correr (cmd builder), manifest p/ delta.
# cmd: función(env)->list[str] o lista fija. Idempotente = re-run baja solo lo nuevo.
def _do_cmd():
    last = last_date_do()
    frm = "01-01-2016"
    if last:
        dd,mm,yy = last.split("-"); d = date(int(yy),int(mm),int(dd)) + timedelta(days=1)
        frm = d.strftime("%d-%m-%Y")
    today = date.today().strftime("%d-%m-%Y")  # date.today() OK en script normal
    return ["python3","scripts/bulk-downloaders/diario-oficial-bulk.py","--from",frm,"--to",today,"--workers","6"]

ZK = "export ZYTE_API_KEY=$(grep '^ZYTE_API_KEY' .env|cut -d= -f2);"

SOURCES = {
 # DIARIAS
 "diario-oficial":   dict(cadence="daily",  manifest="data/diario-oficial/manifest.sqlite3", cmd=_do_cmd),
 "boletin-concursal":dict(cadence="daily",  manifest=None, cmd=["python3","scripts/bulk-downloaders/boletin-concursal-bulk.py"]),
 "pjud":             dict(cadence="daily",  manifest=None, cmd=["python3","scripts/scrape-pjud-juris.py","--incremental"]),
 # SEMANALES (idempotentes: re-run baja lo nuevo via manifest skip + geo-rotation)
 "leychile":         dict(cadence="weekly", manifest="data/leychile/manifest.sqlite3", shell=f"{ZK} bash scripts/bulk-downloaders/leychile-persist.sh"),
 "cgr-dictamenes":   dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/cgr-dictamenes-bulk.py"]),
 "cplt":             dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/cplt-bulk.py"]),
 "suseso":           dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/suseso-bulk.py"]),
 "dt":               dict(cadence="weekly", manifest=None, shell=f"{ZK} python3 scripts/bulk-downloaders/dt-bulk.py"),
 "tta":              dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/tta-bulk.py"]),
 "tdlc":             dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/tdlc-bulk.py"]),
 "fne":              dict(cadence="weekly", manifest=None, cmd=["python3","scripts/bulk-downloaders/fne-bulk.py"]),
 # TODO[P2]: aduanas se bajó con site-crawl-bfs.py (necesita URL seed) — confirmar invocación.
 "aduanas":          dict(cadence="weekly", manifest=None, cmd=["python3","scripts/site-crawl-bfs.py","--aduanas"]),
 "sii-oficios":      dict(cadence="weekly", manifest=None, shell=f"{ZK} python3 scripts/bulk-downloaders/sii-oficios-bulk.py"),
 # MENSUALES (resto idempotente)
 "doctrina":         dict(cadence="monthly",manifest=None, cmd=["python3","scripts/scrape-doctrina-oai.py"]),
 "tc":               dict(cadence="monthly",manifest=None, cmd=["python3","scripts/bulk-downloaders/tc-bulk.py"]),
 "cmf":              dict(cadence="monthly",manifest=None, cmd=["python3","scripts/bulk-downloaders/cmf-bulk.py"]),
 "sii-normativa":    dict(cadence="monthly",manifest=None, cmd=["python3","scripts/bulk-downloaders/sii-normativa-bulk.py"]),
 "historia-ley":     dict(cadence="monthly",manifest=None, cmd=["python3","scripts/bulk-downloaders/historia-ley-bulk.py"]),
 # NOTA: las fuentes que vienen por rsync de Enigma (tribunal-ambiental, recursos-SEA) se
 # refrescan con refresh-rsync-enigma.sh (Raúl deja lo nuevo). DO histórico = estático, no refresh.
}

def run_one(name, cfg):
    print(f"\n=== REFRESH {name} ({cfg['cadence']}) · {time.strftime('%H:%M:%S')} ===", flush=True)
    before = manifest_downloaded(cfg["manifest"]) if cfg.get("manifest") else None
    cmd = cfg.get("cmd"); shell = cfg.get("shell")
    if callable(cmd): cmd = cmd()
    script = (cmd[1] if cmd and len(cmd) > 1 else "") or shell
    if cmd and not Path(ROOT/cmd[1]).exists() and not shell:
        print(f"  ⚠ scraper no existe: {cmd[1]} — SKIP (agregar/verificar)"); return ("skip", 0)
    t0 = time.time()
    try:
        if shell:
            subprocess.run(shell, shell=True, cwd=ROOT, timeout=86400)
        else:
            subprocess.run(cmd, cwd=ROOT, timeout=86400)
    except subprocess.TimeoutExpired:
        print("  ⚠ timeout 24h")
    after = manifest_downloaded(cfg["manifest"]) if cfg.get("manifest") else None
    delta = (after-before) if (before is not None and after is not None) else None
    msg = f"  {name}: " + (f"delta=+{delta} (→{after})" if delta is not None else "sin manifest p/ delta (idempotente)")
    msg += f" · {time.time()-t0:.0f}s"
    print(msg, flush=True)
    return ("ok", delta or 0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source"); ap.add_argument("--cadence", choices=["daily","weekly","monthly"])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for n,c in SOURCES.items(): print(f"{c['cadence']:<8} {n}")
        return
    if a.source:
        if a.source not in SOURCES: sys.exit(f"fuente desconocida: {a.source}")
        run_one(a.source, SOURCES[a.source]); return
    if a.cadence:
        names = [n for n,c in SOURCES.items() if c["cadence"]==a.cadence]
        print(f"REFRESH cadencia {a.cadence}: {len(names)} fuentes → {names}")
        tot=0
        for n in names:
            _, d = run_one(n, SOURCES[n]); tot += (d or 0)
        print(f"\n=== cadencia {a.cadence} completa · delta total +{tot} ===")
        print("→ ahora correr: bash scripts/refresh/refresh-downstream.sh")
        return
    ap.error("usa --source, --cadence o --list")

if __name__ == "__main__":
    main()
