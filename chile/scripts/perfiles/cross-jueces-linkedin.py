#!/usr/bin/env python3
"""Cruza los jueces (RUT de la rutificación Mallas, conf high) con el dataset
LinkedIn Chile de icare (unholster-linkedin-platform/rutificacion/linkedin_chile.duckdb),
rutificado por RUT. Trae educación + trayectoria, FILTRANDO a perfiles con coherencia
judicial/legal (descarta falsos positivos por homónimo). Escribe juez_linkedin.

Método icare (no datos cruzados sin pedido): match por RUT cuerpo, ambos lados high-conf.
Uso: python3 scripts/perfiles/cross-jueces-linkedin.py
"""
import duckdb, sqlite3, re, json, unicodedata

JDB = "data/_index/jueces_enriched.sqlite3"
LDB = "/Volumes/SSD ADA/unholster-linkedin-platform/rutificacion/data/linkedin_chile.duckdb"
JUD = re.compile(r"poder judicial|tribunal|juzgad|\bjuez|jueza|fiscal[ií]a|fiscal\b|abogad|derecho|jur[ií]dic|ministr|magistrad|defensor|corte de apel|academia judicial|leyes", re.I)


def cuerpo(x):
    return re.sub(r"[^0-9]", "", str(x or "")).lstrip("0")


_LOW = {"de", "del", "la", "las", "los", "y", "e", "da", "do"}
def cap(n):
    n = (n or "").strip()
    if not n:
        return None
    return " ".join(w.lower() if i and w.lower() in _LOW else w.lower()[:1].upper() + w.lower()[1:] for i, w in enumerate(n.split()))


def main():
    jc = sqlite3.connect(f"file:{JDB}?mode=ro", uri=True)
    jmap = {cuerpo(c): k for k, c in jc.execute(
        "SELECT juez_key,rut_cuerpo FROM juez_enriched WHERE conf_status='high' AND rut_cuerpo IS NOT NULL")}
    jc.close()

    c = duckdb.connect(LDB, read_only=True)
    lk = {cuerpo(r): pid for pid, r in c.execute(
        "SELECT pid,rut FROM ruled WHERE rut_status='high' AND rut IS NOT NULL").fetchall()}
    matched = {jmap[r]: lk[r] for r in set(jmap) & set(lk)}
    print(f"jueces con LinkedIn rutificado: {len(matched)}", flush=True)

    pids = list(matched.values())
    c.execute("CREATE TEMP TABLE jp(pid VARCHAR)")
    c.executemany("INSERT INTO jp VALUES(?)", [(p,) for p in pids])
    prof = {p[0]: p for p in c.execute(
        "SELECT pid,job_title,company,headline,url,industry FROM master WHERE pid IN (SELECT pid FROM jp)").fetchall()}
    edu = {}
    for pid, school, deg, field, sd, ed in c.execute(
            "SELECT pid,school,deg,field,sd,ed FROM m_edu WHERE pid IN (SELECT pid FROM jp)").fetchall():
        if school:
            edu.setdefault(pid, []).append((school, deg, field, ed))
    c.close()

    out = sqlite3.connect(JDB, timeout=120)
    out.execute("PRAGMA busy_timeout=120000")
    out.execute("DROP TABLE IF EXISTS juez_linkedin")
    out.execute("CREATE TABLE juez_linkedin(juez_key TEXT PRIMARY KEY, url TEXT, job_title TEXT, company TEXT, headline TEXT, educacion TEXT)")
    n = drop = 0
    for jk, pid in matched.items():
        pr = prof.get(pid)
        if not pr:
            continue
        _, job, comp, head, url, ind = pr
        edus = edu.get(pid, [])
        edu_text = " ".join(f"{e[0]} {e[1]} {e[2]}" for e in edus)
        blob = " ".join(str(x or "") for x in [job, comp, head, ind, edu_text])
        if not JUD.search(blob):  # coherencia judicial/legal → descarta homónimos no-jueces
            drop += 1
            continue
        edus_sorted = sorted(edus, key=lambda e: str(e[3] or ""), reverse=True)[:2]
        edu_json = json.dumps([{"school": cap(e[0]), "deg": cap(e[1]), "field": cap(e[2])} for e in edus_sorted], ensure_ascii=False)
        out.execute("INSERT OR REPLACE INTO juez_linkedin VALUES(?,?,?,?,?,?)",
                    (jk, url, cap(job), cap(comp), (head or "").strip()[:160] or None, edu_json))
        n += 1
    out.commit()
    out.close()
    print(f"juez_linkedin: {n} jueces coherentes (descartados por incoherencia judicial: {drop})")


if __name__ == "__main__":
    main()
