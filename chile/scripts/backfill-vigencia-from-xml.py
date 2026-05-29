#!/usr/bin/env python3
"""Backfill de vigencia en `docs_norma` desde los XML LeyChile locales.

Problema que resuelve: `docs_norma.derogado` estaba 80% en 'sin_dato' y
`version_xml` 20% poblado, porque al construir el índice no se parsearon los
atributos del root `<Norma>` para la mayoría de las normas. Pero la señal
autoritativa YA está en disco: cada `data/leychile/{tipo}/{idNorma}.xml`
trae en su root `derogado="(no )derogado"` y `fechaVersion="YYYY-MM-DD"`.

Este script recorre los XML locales, extrae esos dos atributos del root
(por regex sobre el primer bloque del archivo, sin parsear el XML completo)
y actualiza `docs_norma`. El XML es la fuente autoritativa, así que pisa el
valor existente; reporta cuántos cambian de 'sin_dato' a un valor real.

Idempotente: correr de nuevo no cambia nada si los XML no cambiaron.

Uso:
  python3 backfill-vigencia-from-xml.py            # aplica
  python3 backfill-vigencia-from-xml.py --dry-run  # solo reporta
  python3 backfill-vigencia-from-xml.py --tipo ley # solo un tipo
"""
from __future__ import annotations
import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = _REPO_ROOT / "chile/data"
DB_PATH = DATA_ROOT / "_index/corpus.fts.sqlite3"
LEYCHILE_ROOT = DATA_ROOT / "leychile"

# El root <Norma ...> está al inicio del archivo; leemos solo una ventana.
_HEAD_BYTES = 4096
_RE_DEROGADO = re.compile(rb'derogado="([^"]*)"')
_RE_FECHA = re.compile(rb'fechaVersion="([^"]*)"')
_RE_NORMA_ID = re.compile(rb'normaId="(\d+)"')


def parse_root(xml_path: Path) -> tuple[str | None, str | None]:
    """Devuelve (derogado, fechaVersion) del root, o (None, None) si no se
    encuentra el tag <Norma> en la ventana inicial."""
    try:
        with open(xml_path, "rb") as f:
            head = f.read(_HEAD_BYTES)
    except OSError:
        return None, None
    # Asegurar que estamos viendo el root <Norma (no un .xml.txt de texto).
    if b"<Norma" not in head:
        return None, None
    md = _RE_DEROGADO.search(head)
    mf = _RE_FECHA.search(head)
    derogado = md.group(1).decode("utf-8", "replace").strip() if md else None
    fecha = mf.group(1).decode("utf-8", "replace").strip() if mf else None
    # Normalizar derogado a los valores canónicos del esquema.
    if derogado is not None:
        d = derogado.lower()
        derogado = "derogado" if (d == "derogado") else (
            "no derogado" if "no derogado" in d else derogado
        )
    return derogado, fecha


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--tipo", default="", help="Solo este tipo (ley, dl, dfl, dto, cod)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=60)
    # Estado previo (para reportar el delta de cobertura).
    before = dict(conn.execute(
        "SELECT derogado, COUNT(*) FROM docs_norma GROUP BY derogado"
    ).fetchall())

    tipos = [args.tipo] if args.tipo else (
        [p.name for p in LEYCHILE_ROOT.iterdir() if p.is_dir()]
    )

    stats = {"xml_vistos": 0, "sin_root": 0, "no_en_docs_norma": 0,
             "actualizados": 0, "rescatados_de_sin_dato": 0, "sin_cambio": 0}
    t0 = time.time()
    pending: list[tuple[str | None, str | None, int]] = []

    # Mapa actual de docs_norma para saber qué cambia (y no tocar inexistentes).
    cur_map = dict(conn.execute(
        "SELECT leychile_code, derogado || '|' || COALESCE(version_xml,'') "
        "FROM docs_norma"
    ).fetchall())

    for tipo in tipos:
        tdir = LEYCHILE_ROOT / tipo
        if not tdir.is_dir():
            continue
        for xml in tdir.glob("*.xml"):
            stats["xml_vistos"] += 1
            try:
                code = int(xml.stem)
            except ValueError:
                continue
            derogado, fecha = parse_root(xml)
            if derogado is None and fecha is None:
                stats["sin_root"] += 1
                continue
            if code not in cur_map:
                stats["no_en_docs_norma"] += 1
                continue
            prev_der, _, prev_ver = cur_map[code].partition("|")
            new_der = derogado if derogado is not None else prev_der
            new_ver = fecha if fecha is not None else prev_ver
            if f"{new_der}|{new_ver}" == cur_map[code]:
                stats["sin_cambio"] += 1
                continue
            if prev_der == "sin_dato" and new_der in ("derogado", "no derogado"):
                stats["rescatados_de_sin_dato"] += 1
            stats["actualizados"] += 1
            pending.append((new_der, new_ver, code))

    if not args.dry_run and pending:
        conn.executemany(
            "UPDATE docs_norma SET derogado = ?, version_xml = ? "
            "WHERE leychile_code = ?", pending,
        )
        conn.commit()

    after = dict(conn.execute(
        "SELECT derogado, COUNT(*) FROM docs_norma GROUP BY derogado"
    ).fetchall()) if not args.dry_run else None
    conn.close()

    print(f"[{'DRY-RUN' if args.dry_run else 'APLICADO'}] {time.time()-t0:.1f}s")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\n  derogado ANTES: {before}")
    if after is not None:
        print(f"  derogado DESPUÉS: {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
