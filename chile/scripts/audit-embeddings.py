#!/usr/bin/env python3
"""
AUDITORÍA EXHAUSTIVA de embeddings — la verdad completa, no por partes.
Para CADA fuente en data/ reconcilia: archivos embebibles en disco vs embeddings
realmente presentes (manejando paths absolutos Y relativos, en new-sources + master).
Reporta el gap real por fuente. Solo lectura.
"""
import os, re, sqlite3, collections
from glob import glob
from pathlib import Path

ROOT=Path("/Volumes/SSD ADA/claude-for-legal-chile/chile")
DATA=ROOT/"data"
NEW=f"file:{DATA}/_index/new-sources.fts.sqlite3?immutable=1"
MASTER=f"file:{DATA}/_index/corpus.fts.sqlite3?immutable=1"
EXT_TEXT={".txt",".html",".htm",".xml"}   # embebibles directos
# pdf → se embebe vía pdftotext salvo que exista su .pdf.txt (dedup)

def source_of(path):
    """extrae el nombre de fuente del path del embedding (abs o rel)."""
    p=path.replace(str(DATA)+"/","").lstrip("/")
    if p.startswith("data/"): p=p[5:]
    seg=p.split("/")[0]
    return seg

def embedded_by_source():
    cnt=collections.Counter()
    for db in (NEW,MASTER):
        try:
            c=sqlite3.connect(db,uri=True,timeout=120)
            for (path,) in c.execute("SELECT path FROM embeddings"):
                cnt[source_of(path)]+=1
            c.close()
        except Exception as e:
            print(f"  (warn {db}: {e})")
    return cnt

def embeddable_on_disk(srcdir):
    """nº de archivos que DEBERÍAN estar embebidos en esta fuente."""
    txt=html=xml=pdftxt=pdf_solo=0
    pdftxt_bases=set()
    for p in srcdir.rglob("*"):
        if not p.is_file(): continue
        s=p.suffix.lower(); name=p.name.lower()
        if name.endswith(".pdf.txt"): pdftxt+=1; pdftxt_bases.add(p.name[:-4])  # quita .txt → foo.pdf
        elif s==".txt": txt+=1
        elif s in (".html",".htm"): html+=1
        elif s==".xml": xml+=1
    # pdfs sin su .pdf.txt (embed-loop los pdftotext directo)
    for p in srcdir.rglob("*"):
        if p.is_file() and p.suffix.lower()==".pdf" and p.name not in pdftxt_bases:
            pdf_solo+=1
    return {"txt":txt,"html":html,"xml":xml,"pdf.txt":pdftxt,"pdf_sin_txt":pdf_solo,
            "total_embebible":txt+html+xml+pdftxt+pdf_solo}

def main():
    print("Contando embeddings por fuente (3.4M+1.2M, ~1-2min)...",flush=True)
    emb=embedded_by_source()
    print(f"Total embeddings: {sum(emb.values()):,}\n")
    sources=sorted([d for d in DATA.iterdir() if d.is_dir() and d.name!="_index"], key=lambda d:d.name)
    print(f"{'FUENTE':<28}{'embebible_disco':>16}{'embebido':>10}{'gap':>8}  estado")
    total_gap=0; gapped=[]
    for d in sources:
        dz=embeddable_on_disk(d)
        e=emb.get(d.name,0)
        able=dz["total_embebible"]
        gap=able-e
        if able==0 and e==0:
            estado="(sin texto / estructurada)"
        elif gap<=max(5,able*0.02):
            estado="✓ OK"
        else:
            estado=f"⚠ FALTAN {gap}"; total_gap+=max(0,gap); gapped.append((d.name,able,e,gap,dz))
        if able>0 or e>0:
            print(f"{d.name:<28}{able:>16,}{e:>10,}{gap:>8,}  {estado}")
    # pjud (no es dir de fuente única, es competencias)
    pj=sum(v for k,v in emb.items() if k=="pjud")
    print(f"{'pjud (metadato, sin archivos)':<28}{'-':>16}{pj:>10,}{'-':>8}  ✓ (embebido directo de json.gz)")
    cc=emb.get("boletin-concursal",0)
    print(f"{'boletin-concursal (tabla)':<28}{747552:>16,}{cc:>10,}{747552-cc:>8,}  {'⚠ embebiendo' if cc<747000 else '✓'}")
    print(f"\n=== {len(gapped)} fuentes con GAP real · faltan {total_gap:,} embeddings ===")
    for n,able,e,gap,dz in sorted(gapped,key=lambda x:-x[3]):
        print(f"  {n}: disco={able} emb={e} gap={gap} · {dz}")

if __name__=="__main__": main()
