#!/usr/bin/env python3
"""Extrae texto plano de los XMLs LeyChile (EsquemaIntercambioNorma).

Output: .xml.txt al lado del .xml, idempotente.

XML schema relevante:
  <Norma normaId=N>
    <Identificador> <Titulo>...</Titulo> ... </Identificador>
    <EstructurasFuncionales>
      <EstructurasFun><EstructuraFun>
        <Texto>texto literal de la norma...</Texto>
      </EstructuraFun></EstructurasFun>
    </EstructurasFuncionales>
  </Norma>

También puede tener <Articulado><Articulo><Texto>... según el tipo.
"""
from __future__ import annotations
import argparse, sys, time, re, html
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
import xml.etree.ElementTree as ET

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = _REPO_ROOT / "chile/data/leychile"
_STATS = {"ok": 0, "skip": 0, "empty": 0, "err": 0, "bytes_out": 0}
_LOCK = Lock()

# Namespace BCN
NS = "{http://www.leychile.cl/esquemas}"


def extract_text(xml_path: Path) -> str:
    """Extrae todo el texto literal del XML.

    Walks every element. Para nodos con tag local 'Texto' o 'Encabezado',
    concatena su content + tail. Mantiene saltos de línea entre artículos.
    """
    try:
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
    except ET.ParseError:
        return ""

    parts: list[str] = []

    def local(tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    # Title first
    for el in root.iter():
        if local(el.tag) in ("Titulo", "TituloNorma") and el.text:
            t = el.text.strip()
            if t:
                parts.append(f"# {t}\n")
                break

    seen_text_elements = 0
    for el in root.iter():
        tag = local(el.tag)
        if tag in ("Texto", "EpigrafeArticulo", "RotuloArticulo",
                   "Encabezado", "Promulgacion", "Footer"):
            text = "".join(el.itertext()).strip()
            if text:
                parts.append(text)
                seen_text_elements += 1

    if not seen_text_elements:
        # Fallback: get all text nodes
        all_text = "".join(root.itertext())
        cleaned = re.sub(r"\s+", " ", all_text).strip()
        if len(cleaned) > 100:
            return cleaned

    return "\n\n".join(parts)


def process_one(xml_path: Path, force: bool = False) -> str:
    txt = xml_path.with_suffix(".xml.txt")
    if not force and txt.exists() and txt.stat().st_size > 0:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    try:
        text = extract_text(xml_path)
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "err"
    if not text or len(text) < 50:
        with _LOCK: _STATS["empty"] += 1
        txt.touch()
        return "empty"
    try:
        txt.write_text(text, encoding="utf-8")
    except Exception:
        with _LOCK: _STATS["err"] += 1
        return "err"
    with _LOCK:
        _STATS["ok"] += 1
        _STATS["bytes_out"] += len(text.encode("utf-8"))
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    xmls = [p for p in root.rglob("*.xml") if p.is_file()]
    print(f"XMLs encontrados: {len(xmls)}", flush=True)
    if not xmls:
        return 0

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_one, p, args.force) for p in xmls]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 2000 == 0 or i == len(xmls):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                print(
                    f"  [{i}/{len(xmls)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"empty={_STATS['empty']} err={_STATS['err']} | "
                    f"{elapsed:.0f}s rate={rate:.0f}/s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} skip={_STATS['skip']} "
        f"empty={_STATS['empty']} err={_STATS['err']} | "
        f"texto: {_STATS['bytes_out']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
