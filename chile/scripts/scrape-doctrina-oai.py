#!/usr/bin/env python3
"""Harvester OAI-PMH genérico para repositorios universitarios chilenos.

Fuente principal: repositorio.uchile.cl (DSpace OAI-PMH) — Facultad de
Derecho UCh ~8.570 records (tesis + papers).

Pipeline:
  Fase 1 (este script): metadata-only completo vía ListRecords.
  Fase 2 (otro script): descargar PDF fulltext desde dc:identifier
    cuando es URL handle DSpace.

Output: chile/normativa/doctrina/{fuente}/{handle_slug}.md
con frontmatter Dublin Core (titulo, autor, año, tipo, palabras_clave,
abstract, fuente_url, doi si aplica) + handle. Idempotente.

Repos soportados:
  uch    → repositorio.uchile.cl  set=com_2250_100009 (Facultad Derecho)
  udp    → repositorio.udp.cl     (pending: ListSets)
  uach   → cybertesis.uach.cl     (pending)
  utalca → dspace.utalca.cl       (pending)

CLI:
  python3 scrape-doctrina-oai.py --fuente uch
  python3 scrape-doctrina-oai.py --fuente uch --max 100  # smoke
"""
from __future__ import annotations
import argparse, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTRINA_ROOT = REPO_ROOT / "chile/normativa/doctrina"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

FUENTES = {
    "uch": {
        "base": "https://repositorio.uchile.cl/oai/request",
        "set": "com_2250_100009",
        "label": "UCh Facultad de Derecho",
    },
    "ucn": {
        "base": "https://repositorio.ucn.cl/server/oai/request",
        "set": "com_20.500.14729_7",
        "label": "UCN Facultad de Ciencias Jurídicas",
    },
    "ucn-revista-derecho": {
        "base": "https://repositorio.ucn.cl/server/oai/request",
        "set": "col_20.500.14729_4645",
        "label": "Revista de Derecho UCN Coquimbo",
    },
    "uautonoma": {
        "base": "https://repositorio.uautonoma.cl/server/oai/request",
        "set": "com_20.500.12728_7362",
        "label": "U. Autónoma Facultad de Derecho",
    },
    "umayor": {
        "base": "https://repositorio.umayor.cl/oai/request",
        "set": "com_sibum_6771",
        "label": "U. Mayor Derecho",
    },
    "uft": {
        "base": "https://repositorio.uft.cl/server/oai/request",
        "set": "com_20.500.12254_2321",
        "label": "U. Finis Terrae Facultad de Derecho",
    },
    "unab": {
        "base": "https://repositorio.unab.cl/server/oai/request",
        "set": "com_ria_60463",
        "label": "U. Andrés Bello FADERE",
    },
    "uv": {
        "base": "https://repositoriobibliotecas.uv.cl/oai/request",
        "set": "com_uvscl_244",
        "label": "U. Valparaíso Facultad de Derecho",
    },
}


def slug(text: str, maxlen: int = 100) -> str:
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", text).strip("-").lower()
    return s[:maxlen] or "untitled"


def handle_to_slug(identifier: str) -> str:
    """oai:repositorio.uchile.cl:2250/202110 → uch-2250-202110"""
    m = re.search(r"(\d+)/(\d+)$", identifier)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return slug(identifier, 60)


def fetch_xml(url: str, timeout: int = 60, retries: int = 4) -> str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            wait = 5 * (2 ** attempt)
            print(f"  err {type(e).__name__} attempt {attempt+1}/{retries}, "
                  f"sleep {wait}s", flush=True)
            time.sleep(wait)
    return None


def parse_records(xml: str) -> tuple[list[dict], str | None, int | None]:
    """Returns (records, resumption_token, complete_list_size)."""
    root = ET.fromstring(xml)
    records = []
    for rec in root.iter(f"{{{NS['oai']}}}record"):
        header = rec.find(f"{{{NS['oai']}}}header")
        if header is None:
            continue
        ident_el = header.find(f"{{{NS['oai']}}}identifier")
        if ident_el is None or ident_el.text is None:
            continue
        ident = ident_el.text
        # deleted?
        status = header.attrib.get("status", "")
        if status == "deleted":
            continue

        meta = rec.find(f"{{{NS['oai']}}}metadata")
        if meta is None:
            continue
        oai_dc = meta.find(f"{{{NS['oai_dc']}}}dc")
        if oai_dc is None:
            continue

        d = {"identifier": ident}
        for tag in (
            "title", "creator", "subject", "description", "date",
            "type", "publisher", "language", "rights"
        ):
            els = oai_dc.findall(f"{{{NS['dc']}}}{tag}")
            vals = [e.text.strip() for e in els if e.text]
            if vals:
                d[tag] = vals
        # identifier URLs separately
        ident_urls = []
        for el in oai_dc.findall(f"{{{NS['dc']}}}identifier"):
            if el.text and el.text.startswith("http"):
                ident_urls.append(el.text.strip())
        if ident_urls:
            d["urls"] = ident_urls
        records.append(d)

    tok_el = root.find(f".//{{{NS['oai']}}}resumptionToken")
    token = tok_el.text if (tok_el is not None and tok_el.text) else None
    cls = tok_el.attrib.get("completeListSize") if tok_el is not None else None
    return records, token, int(cls) if cls and cls.isdigit() else None


def write_record(rec: dict, fuente: str) -> bool:
    out_dir = DOCTRINA_ROOT / fuente
    out_dir.mkdir(parents=True, exist_ok=True)
    handle_slug = handle_to_slug(rec["identifier"])
    path = out_dir / f"{handle_slug}.md"
    if path.exists():
        return False  # idempotente

    titulo = (rec.get("title") or ["Sin título"])[0].replace('"', '\\"')
    autores = rec.get("creator") or []
    fecha = (rec.get("date") or [""])[0]
    anio = fecha[:4] if fecha and len(fecha) >= 4 else ""
    tipo = (rec.get("type") or [""])[0]
    abstract = (rec.get("description") or [""])[0]
    subjects = rec.get("subject") or []
    urls = rec.get("urls") or []
    publisher = (rec.get("publisher") or [""])[0]
    lang = (rec.get("language") or [""])[0]

    fm = "---\n"
    fm += f"identifier: {rec['identifier']}\n"
    fm += f'titulo: "{titulo}"\n'
    if autores:
        fm += "autores:\n"
        for a in autores:
            fm += f"  - {a}\n"
    if anio: fm += f"anio: {anio}\n"
    if fecha: fm += f"fecha: {fecha}\n"
    if tipo: fm += f'tipo: "{tipo}"\n'
    if publisher: fm += f"publisher: {publisher}\n"
    if lang: fm += f"idioma: {lang}\n"
    if subjects:
        fm += "materias:\n"
        for s in subjects[:10]:
            sc = s.replace('"', '\\"')
            fm += f'  - "{sc}"\n'
    if urls:
        fm += "urls:\n"
        for u in urls[:5]:
            fm += f"  - {u}\n"
    fm += f"fuente: {fuente}\n"
    fm += "capa: 1\n"
    fm += "estado_revision: oai-metadata-only\n"
    fm += "---\n\n"
    fm += f"# {titulo}\n\n"
    if autores:
        fm += f"**Autor(es):** {', '.join(autores)}\n\n"
    if anio: fm += f"**Año:** {anio}  "
    if tipo: fm += f"**Tipo:** {tipo}\n\n"
    if abstract:
        fm += "## Resumen\n\n" + abstract + "\n"

    path.write_text(fm, encoding="utf-8")
    return True


def harvest(fuente: str, max_records: int = 0, rate: float = 1.0) -> int:
    cfg = FUENTES[fuente]
    base = cfg["base"]
    set_spec = cfg["set"]

    params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
    if set_spec:
        params["set"] = set_spec
    url = base + "?" + urllib.parse.urlencode(params)

    total = 0
    written = 0
    page = 0
    expected: int | None = None
    while True:
        page += 1
        print(f"\n[{fuente}] page {page} — fetching...", flush=True)
        xml = fetch_xml(url)
        if not xml:
            print(f"  FAIL after retries, stopping", flush=True)
            break
        try:
            records, token, cls = parse_records(xml)
        except ET.ParseError as e:
            print(f"  XML parse error: {e}", flush=True)
            break
        if expected is None and cls:
            expected = cls
            print(f"  Total esperado: {cls}", flush=True)

        n_written = 0
        for rec in records:
            if write_record(rec, fuente):
                n_written += 1
        total += len(records)
        written += n_written
        pct = 100.0 * total / expected if expected else 0
        print(f"  recs={len(records)} written={n_written} | "
              f"total={total}/{expected} ({pct:.1f}%) cumWritten={written}",
              flush=True)

        if max_records and total >= max_records:
            print(f"  --max alcanzado", flush=True)
            break
        if not token:
            print(f"  resumptionToken vacío — fin", flush=True)
            break
        url = base + "?" + urllib.parse.urlencode({
            "verb": "ListRecords", "resumptionToken": token,
        })
        time.sleep(rate)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente", choices=list(FUENTES.keys()),
                        default="uch")
    parser.add_argument("--max", type=int, default=0,
                        help="Stop after N records (0 = todo)")
    parser.add_argument("--rate", type=float, default=1.0,
                        help="sleep entre páginas (segundos)")
    args = parser.parse_args()

    start = time.time()
    print(f"Doctrina OAI harvester — fuente={args.fuente}", flush=True)
    written = harvest(args.fuente, args.max, args.rate)
    elapsed = time.time() - start
    print(f"\n[DONE] {elapsed:.0f}s | nuevos: {written}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
