#!/usr/bin/env python3
"""Reporte de cobertura del corpus legal chileno.

Lee los manifests SQLite de cada bulk downloader + cuenta archivos en
disco, y emite tabla con totales para README/status.
"""
from __future__ import annotations
import sqlite3, os, json, sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = _REPO_ROOT / "chile/data"

SOURCES = [
    # (display, dir, table, where_ok)
    ("Diario Oficial", "diario-oficial", "descargas",  "status='ok'"),
    ("TC sentencias",  "tc",             "sentencias", "downloaded=1"),
    ("DT dictámenes",  "dt",             "dictamenes", "downloaded=1"),
    ("CMF normas",     "cmf",            "normas",     "downloaded=1"),
    ("SII circulares", "sii",            "circulares", "downloaded=1"),
    ("TDLC sentencias","tdlc",           "sentencias", "downloaded=1"),
    ("SERNAC",         "sernac",         None,         None),
    ("Subtel",         "subtel",         "documentos", "downloaded=1"),
    ("TDPI",           "tdpi",           "fallos",     "downloaded=1"),
    ("FNE",             "fne",           "posts",      "1=1"),
    ("Trib. Ambientales","tribunales-ambientales", "sentencias", "downloaded=1"),
    ("SEC",             "sec",            "files",       "downloaded=1"),
    ("TC moderno",      "tc-moderno",     "sentencias_modernas", "downloaded=1"),
    ("LeyChile XMLs",   "leychile",       "normas",      "downloaded=1"),
    ("CGR",            "cgr",            None,         None),
]


def manifest_count(db_path: Path, table: str | None, cond: str | None) -> int:
    if not table or not db_path.exists():
        return -1
    try:
        c = sqlite3.connect(str(db_path), timeout=5)
        n = c.execute(f"SELECT COUNT(*) FROM {table} WHERE {cond}").fetchone()[0]
        c.close()
        return n
    except sqlite3.OperationalError:
        return -2


def disk_stats(d: Path) -> tuple[int, int]:
    if not d.exists():
        return 0, 0
    n, sz = 0, 0
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith((".pdf", ".html")):
                n += 1
                try:
                    sz += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    return n, sz


def main() -> int:
    print(f"{'Fuente':18s} {'Manifest':>10s} {'Archivos':>10s} {'Tamaño':>10s}")
    print("-" * 52)
    grand_files, grand_size = 0, 0
    rows_json = []
    for display, subdir, table, cond in SOURCES:
        d = DATA_ROOT / subdir
        n = manifest_count(d / "manifest.sqlite3", table, cond)
        files, size = disk_stats(d)
        grand_files += files
        grand_size += size
        manifest = f"{n:,}" if n >= 0 else "-"
        size_str = f"{size / 1e9:.2f} GB" if size > 1e9 else f"{size / 1e6:.0f} MB"
        print(f"{display:18s} {manifest:>10s} {files:>10,} {size_str:>10s}")
        rows_json.append({
            "fuente": display, "directorio": subdir,
            "manifest_ok": n if n >= 0 else None,
            "archivos_disco": files, "bytes_disco": size,
        })

    print("-" * 52)
    print(f"{'TOTAL':18s} {' ':>10s} {grand_files:>10,} "
          f"{grand_size/1e9:.2f} GB")

    if "--json" in sys.argv:
        out = {"total_files": grand_files, "total_bytes": grand_size,
               "sources": rows_json}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
