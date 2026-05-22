#!/usr/bin/env python3
"""Coverage detallado por año/fuente. Usa los manifests SQLite y
estructura de directorios para reportar cobertura temporal.
"""
from __future__ import annotations
import sqlite3
import sys
import re
from pathlib import Path
from collections import defaultdict

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = _REPO_ROOT / "chile/data"


def fne_by_year() -> dict[int, int]:
    db = DATA_ROOT / "fne/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT SUBSTR(date, 1, 4) as y, COUNT(*) FROM posts "
        "GROUP BY y ORDER BY y"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y and y.isdigit()}


def dt_by_year() -> dict[int, int]:
    db = DATA_ROOT / "dt/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT year, COUNT(*) FROM dictamenes WHERE downloaded=1 "
        "GROUP BY year ORDER BY year"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y}


def do_by_year() -> dict[int, int]:
    db = DATA_ROOT / "diario-oficial/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT SUBSTR(date, 1, 4) as y, COUNT(*) "
        "FROM descargas WHERE status='ok' GROUP BY y ORDER BY y"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y and y.isdigit()}


def tc_by_year() -> dict[int, int]:
    """TC sin 'year' explícito en manifest — buscar en filename."""
    out = defaultdict(int)
    d = DATA_ROOT / "tc"
    if not d.exists():
        return {}
    for f in d.glob("*.pdf"):
        # archivos llamados tc_NNN.pdf (legacy id). Sin año.
        out[0] += 1
    return dict(out)


def cmf_by_year() -> dict[int, int]:
    db = DATA_ROOT / "cmf/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT year, COUNT(*) FROM normas WHERE downloaded=1 "
        "GROUP BY year ORDER BY year"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y}


def sii_by_year() -> dict[int, int]:
    db = DATA_ROOT / "sii/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT year, COUNT(*) FROM circulares WHERE downloaded=1 "
        "GROUP BY year ORDER BY year"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y}


def tdpi_by_year() -> dict[int, int]:
    db = DATA_ROOT / "tdpi/manifest.sqlite3"
    if not db.exists():
        return {}
    c = sqlite3.connect(str(db), timeout=5)
    rows = c.execute(
        "SELECT year, COUNT(*) FROM fallos WHERE downloaded=1 "
        "GROUP BY year ORDER BY year"
    ).fetchall()
    c.close()
    return {int(y): n for y, n in rows if y}


SOURCES = [
    ("Diario Oficial", do_by_year),
    ("FNE", fne_by_year),
    ("DT dictámenes", dt_by_year),
    ("CMF", cmf_by_year),
    ("SII", sii_by_year),
    ("TDPI", tdpi_by_year),
]


def main() -> int:
    # Build year × source matrix
    matrix: dict[tuple[int, str], int] = {}
    all_years: set[int] = set()
    sources_with_data: list[str] = []
    for name, fn in SOURCES:
        data = fn()
        if data:
            sources_with_data.append(name)
            for y, n in data.items():
                matrix[(y, name)] = n
                all_years.add(y)

    years_sorted = sorted(y for y in all_years if y > 1980)
    headers = sources_with_data

    print(f"\n{'Año':>6s} " + " ".join(f"{h[:8]:>8s}" for h in headers) + "    Total")
    print("-" * (8 + 9 * len(headers) + 10))
    totals_year = defaultdict(int)
    totals_src = defaultdict(int)
    for y in years_sorted:
        row = []
        row_total = 0
        for s in headers:
            n = matrix.get((y, s), 0)
            row.append(f"{n:>8d}" if n else f"{'-':>8s}")
            row_total += n
            totals_src[s] += n
        totals_year[y] = row_total
        print(f"{y:>6d} " + " ".join(row) + f"  {row_total:>7d}")

    # Footer totals
    print("-" * (8 + 9 * len(headers) + 10))
    grand = 0
    row = []
    for s in headers:
        row.append(f"{totals_src[s]:>8d}")
        grand += totals_src[s]
    print(f"{'TOTAL':>6s} " + " ".join(row) + f"  {grand:>7d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
