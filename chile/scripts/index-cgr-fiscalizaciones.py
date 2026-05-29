#!/usr/bin/env python3
"""Indexa observaciones CGR (auditorías + fiscalizaciones 2020-2025) a docs FTS.

Lee los 3 CSVs en data/cgr/bases/*.csv (encoding latin-1 + ; separator),
combina en un doc por (Id Fiscalizacion, ID Observacion) con metadata rica.

Cada doc incluye:
  Tipo, Materia, Objetivo, Entidad, Sector, Área, Titulo + Acción derivada/correctiva.
"""
from __future__ import annotations
import csv, sqlite3, sys, time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
CGR_ROOT = _REPO_ROOT / "chile/data/cgr/bases"
CORPUS_DB = _REPO_ROOT / "chile/data/_index/corpus.fts.sqlite3"


# Algunos CSVs vienen latin-1 (Región corrupted en cp1252)
def read_csv(path: Path):
    # Detectar encoding por header bytes
    with open(path, "rb") as f:
        head = f.read(200)
    if b"\xef\xbb\xbf" in head[:3] or b"R\xc3\xa9gion" in head:
        enc = "utf-8-sig"
    elif b"Regi\xc3\xb3n" in head:
        enc = "utf-8"
    else:
        enc = "latin-1"
    with open(path, "r", encoding=enc, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            yield row


def main() -> int:
    if not CGR_ROOT.exists():
        print(f"no existe {CGR_ROOT}", flush=True)
        return 1
    csv_files = sorted(CGR_ROOT.glob("*.csv"))
    print(f"CSVs: {len(csv_files)}", flush=True)
    for c in csv_files:
        print(f"  {c.name} ({c.stat().st_size/1e6:.1f} MB)", flush=True)

    corpus = sqlite3.connect(str(CORPUS_DB), timeout=120)
    corpus.execute("PRAGMA journal_mode=WAL")
    corpus.execute("PRAGMA busy_timeout=120000")
    existing = set(
        r[0] for r in corpus.execute(
            "SELECT path FROM docs_meta WHERE path LIKE 'cgr-fiscalizaciones/%'"
        )
    )
    print(f"already indexed: {len(existing)}", flush=True)

    def gv(row, key):
        # Normaliza keys con encoding corrupted
        for k in row:
            if k.lower().replace("ó", "o").replace("á", "a").replace("í", "i") \
                    .replace("﻿", "").strip() == key.lower():
                return (row[k] or "").strip()
            # Tolerar caracteres corrupted en headers latin-1 mal decoded
            kn = k.replace("�", "?").replace("\x8c\xa6", "o").lower().strip()
            if kn.startswith(key.lower()[:5]):
                return (row[k] or "").strip()
        return ""

    n_ok = n_skip = n_empty = 0
    t0 = time.time()
    now = time.time()
    for csv_file in csv_files:
        slug = csv_file.stem.split("_")[0].lower()  # base, municipalidades, no
        if slug == "no": slug = "no-municipales"
        elif slug == "base": slug = "general"
        print(f"\n--- {csv_file.name} ({slug}) ---", flush=True)
        n_file = 0
        for row in read_csv(csv_file):
            fid = gv(row, "Id Fiscalizacion")
            oid = gv(row, "ID Observacion")
            if not fid or not oid:
                continue
            path = f"cgr-fiscalizaciones/{slug}/{fid}-{oid}.txt"
            if path in existing:
                n_skip += 1
                continue
            anio = gv(row, "Año informe publicado") or gv(row, "A?o informe publicado")
            try:
                anio_int = int(anio[:4])
            except: anio_int = None
            tipo = gv(row, "Tipo Fiscalizacion")
            nombre = gv(row, "Nombre Fiscalizacion")
            materia = gv(row, "Materia Fiscalizacion")
            objetivo = gv(row, "Objetivo Fiscalizacion")
            entidad = gv(row, "Entidad")
            sector = gv(row, "Sector")
            region = gv(row, "Región") or gv(row, "Regi?n") or gv(row, "Regi�n")
            titulo = gv(row, "Titulo Observacion")
            complejidad = gv(row, "Complejidad Observacion")
            accion_der = gv(row, "Accion derivada")
            accion_corr = gv(row, "Accion correctiva")
            link = gv(row, "Link informe publicado")

            content_parts = [
                f"CGR — Observación de fiscalización {fid}/{oid}",
                f"Tipo: {tipo}",
                f"Nombre fiscalización: {nombre}",
                f"Materia: {materia}",
                f"Objetivo: {objetivo}",
                f"Entidad: {entidad}",
                f"Sector: {sector}    Región: {region}",
                f"Año: {anio}",
                f"Link informe: {link}",
                "",
                f"Título observación: {titulo}",
                f"Complejidad: {complejidad}",
                f"Acción derivada: {accion_der}",
                f"Acción correctiva: {accion_corr}",
            ]
            content = "\n".join(p for p in content_parts if p)
            if len(content) < 120:
                n_empty += 1
                continue
            corpus.execute(
                "INSERT INTO docs(path, source, year, content) VALUES (?,?,?,?)",
                (path, "cgr-fiscalizaciones", str(anio_int) if anio_int else "?",
                 content),
            )
            corpus.execute(
                "INSERT OR REPLACE INTO docs_meta(path, mtime, size) VALUES (?,?,?)",
                (path, now, len(content)),
            )
            n_ok += 1
            n_file += 1
            if n_ok % 5000 == 0:
                corpus.commit()
                print(f"  ok={n_ok} skip={n_skip} empty={n_empty}", flush=True)
        corpus.commit()
        print(f"  {csv_file.name}: {n_file} indexed", flush=True)
    corpus.close()
    print(f"\n[DONE] {time.time()-t0:.0f}s | ok={n_ok} skip={n_skip} empty={n_empty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
