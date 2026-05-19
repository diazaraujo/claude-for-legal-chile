#!/usr/bin/env python3
"""
promote-to-capa2.py — Promoción de capa 1 a capa 2 del corpus chileno.

Toma un archivo capa 1 de `chile/normativa/catalogo/<tipo>/<num>.md`, descarga
el texto vigente desde el endpoint XML estructurado de LeyChile, parsea la
estructura (libros / títulos / párrafos / artículos), y reescribe el archivo
como capa 2 con resumen estructural.

Endpoint XML:
    https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=<leychile_code>

Capa 2 contiene:
- Frontmatter enriquecido (capa: 2, estado_revision: resumen-estructural)
- Resumen ejecutivo (extraído de Metadatos.TituloNorma + Encabezado)
- Estructura (jerarquía de Libros / Títulos / Capítulos / Párrafos)
- Artículos con su número y primeras líneas
- Modificaciones declaradas en el XML
- Fuente con fecha de versión

Modos:
- Parsing estructural puro (default): rápido, reproducible, sin LLM
- --with-llm: agrega resumen ejecutivo y "cuándo invocar" via Claude API
  (requiere ANTHROPIC_API_KEY en env)

Uso:
    python promote-to-capa2.py --slug ley/19628
    python promote-to-capa2.py --slug cod/codigo-trabajo
    python promote-to-capa2.py --tipo ley --batch 50
    python promote-to-capa2.py --slug ley/19628 --with-llm
    python promote-to-capa2.py --slug ley/19628 --dry-run

# std:input chile/normativa/catalogo/<tipo>/<num>.md (capa 1)
# std:output chile/normativa/catalogo/<tipo>/<num>.md (sobreescrito como capa 2)
# std:deps urllib (stdlib), xml.etree.ElementTree (stdlib), opcional: anthropic
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

LEYCHILE_XML = "https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={code}"
DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "chile" / "normativa" / "catalogo"

# Namespace del esquema LeyChile
NS = {"lc": "http://www.leychile.cl/esquemas"}

USER_AGENT = (
    "Mozilla/5.0 (compatible; claude-for-legal-chile/0.2; "
    "+https://github.com/diazaraujo/claude-for-legal-chile)"
)


def download_xml(leychile_code: str, sleep_ms: int = 300) -> bytes:
    """Descarga XML estructurado de LeyChile."""
    url = LEYCHILE_XML.format(code=leychile_code)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/xml"},
    )
    time.sleep(sleep_ms / 1000.0)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parsea YAML frontmatter sencillo. Devuelve (dict, resto_markdown)."""
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    yaml_block = content[4:end]
    body = content[end + 5:]
    fm = {}
    for line in yaml_block.splitlines():
        if ":" not in line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"')
    return fm, body


def extract_xml_text(elem) -> str:
    """Texto plano de un elemento XML, sin tags."""
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def parse_norma_xml(xml_bytes: bytes) -> dict:
    """Parsea XML de norma LeyChile y devuelve estructura."""
    root = ET.fromstring(xml_bytes)
    result = {
        "norma_id": root.attrib.get("normaId", ""),
        "fecha_version": root.attrib.get("fechaVersion", ""),
        "derogado": root.attrib.get("derogado", ""),
        "es_tratado": root.attrib.get("esTratado", ""),
        "titulo": "",
        "tipo": "",
        "numero": "",
        "fecha_promulgacion": "",
        "fecha_publicacion": "",
        "organismo": "",
        "materias": [],
        "nombres_uso_comun": [],
        "encabezado": "",
        "estructura": [],
        "articulos": [],
        "modificaciones": [],
    }

    # Identificador
    ident = root.find("lc:Identificador", NS)
    if ident is not None:
        result["fecha_promulgacion"] = ident.attrib.get("fechaPromulgacion", "")
        result["fecha_publicacion"] = ident.attrib.get("fechaPublicacion", "")
        for tn in ident.findall(".//lc:TipoNumero", NS):
            tipo_el = tn.find("lc:Tipo", NS)
            num_el = tn.find("lc:Numero", NS)
            if tipo_el is not None and not result["tipo"]:
                result["tipo"] = extract_xml_text(tipo_el)
            if num_el is not None and not result["numero"]:
                result["numero"] = extract_xml_text(num_el)
        org_el = ident.find(".//lc:Organismo", NS)
        if org_el is not None:
            result["organismo"] = extract_xml_text(org_el)

    # Metadatos
    meta = root.find("lc:Metadatos", NS)
    if meta is not None:
        tit_el = meta.find("lc:TituloNorma", NS)
        if tit_el is not None:
            result["titulo"] = extract_xml_text(tit_el)
        for m in meta.findall(".//lc:Materia", NS):
            t = extract_xml_text(m)
            if t and t not in result["materias"]:
                result["materias"].append(t)
        for n in meta.findall(".//lc:NombreUsoComun", NS):
            t = extract_xml_text(n)
            if t and t not in result["nombres_uso_comun"]:
                result["nombres_uso_comun"].append(t)

    # Encabezado (primer texto de la norma)
    enc = root.find("lc:Encabezado", NS)
    if enc is not None:
        texto_el = enc.find("lc:Texto", NS)
        if texto_el is not None:
            txt = extract_xml_text(texto_el)
            # Tomar primeras ~500 chars para resumen
            result["encabezado"] = txt[:500].strip()

    # Estructura jerárquica + artículos
    # LeyChile usa <EstructurasFuncionales> conteniendo <EstructuraFuncional
    # tipoParte="Título|Artículo|Párrafo|..."> recursivos. Iteramos desde el
    # primer contenedor de nivel raíz.
    contenedor = root.find("lc:EstructurasFuncionales", NS)
    if contenedor is not None:
        for ef in contenedor.findall("lc:EstructuraFuncional", NS):
            _walk_estructura(ef, result["estructura"], result["articulos"], depth=0)

    # Modificaciones
    for mod in root.findall(".//lc:Modificacion", NS):
        mod_txt = extract_xml_text(mod)[:200]
        if mod_txt:
            result["modificaciones"].append(mod_txt)

    return result


def _walk_estructura(elem, estructura_list, articulos_list, depth: int):
    """Recorre <EstructuraFuncional> recursivos discriminando por tipoParte.

    tipoParte típicos: Libro, Título, Capítulo, Párrafo, Sección, Artículo,
    Inciso, Numeral, Letra.
    """
    tag = elem.tag.replace(f"{{{NS['lc']}}}", "")
    if tag != "EstructuraFuncional":
        # Descender sin agregar
        for child in elem:
            _walk_estructura(child, estructura_list, articulos_list, depth)
        return

    tipo_parte = elem.attrib.get("tipoParte", "")
    # Título del nivel: puede estar en <TituloParte> (Artículos) o en <Texto>
    # directo (Libros, Títulos, Capítulos, etc.).
    titulo_el = elem.find("lc:TituloParte", NS)
    if titulo_el is not None and titulo_el.attrib.get("presente") == "si":
        titulo = extract_xml_text(titulo_el)
    else:
        titulo = ""
    if not titulo and tipo_parte.lower() not in ("artículo", "articulo"):
        # Fallback: el primer <Texto> hijo directo contiene el título del nivel
        texto_directo = elem.find("lc:Texto", NS)
        if texto_directo is not None:
            titulo = " ".join(extract_xml_text(texto_directo).split())[:120]

    if tipo_parte.lower() in ("artículo", "articulo"):
        texto_el = elem.find("lc:Texto", NS)
        texto_completo = ""
        if texto_el is not None:
            texto_completo = extract_xml_text(texto_el).strip()
        # Extraer número desde inicio del texto: "Artículo Nº" / "Art. N°" / "Artículo único"
        num = ""
        m = re.match(
            r"^\s*Art[íi]?culo\s*[°º]?\s*([\dIVXLC]+(?:°|º|\.|\s|\b)\w*|\bú?nico\b|\bprimero\b|\bsegundo\b|\btercero\b)",
            texto_completo,
            re.IGNORECASE,
        )
        if m:
            num = m.group(1).strip(".° º").lower()
        else:
            # Fallback: idParte
            num = elem.attrib.get("idParte", "?")
        # Inciso inicial: 200 chars sin "Artículo Nº.-" inicial
        primer = re.sub(r"^Art[íi]?culo\s*[°º\d.\s]+\.?-?\s*", "", texto_completo, flags=re.IGNORECASE)
        primer = primer[:200].replace("\n", " ").strip()
        articulos_list.append({
            "numero": num,
            "titulo_parte": titulo,
            "inciso_inicial": primer,
        })
    elif tipo_parte:
        # Nivel jerárquico (Libro, Título, Capítulo, etc.)
        estructura_list.append({
            "nivel": tipo_parte,
            "depth": depth,
            "titulo": titulo,
        })

    # Descender vía EstructurasFuncionales (contenedor plural)
    for contenedor in elem.findall("lc:EstructurasFuncionales", NS):
        for child in contenedor.findall("lc:EstructuraFuncional", NS):
            next_depth = depth + 1 if tipo_parte and tipo_parte.lower() not in ("artículo", "articulo") else depth
            _walk_estructura(child, estructura_list, articulos_list, next_depth)


def render_capa2(fm: dict, parsed: dict, slug: str) -> str:
    """Renderiza el markdown capa 2."""
    tipo = fm.get("tipo", "")
    numero = parsed.get("numero") or fm.get("numero", "")
    titulo = parsed.get("titulo") or fm.get("titulo_oficial", "")
    nombre_corto = f"{parsed.get('tipo', tipo).upper()} {numero}" if tipo == "ley" else f"{tipo.upper()} {numero}"

    # Mantener metadata original + capa 2
    lines = [
        "---",
        f"norma: {fm.get('norma', nombre_corto)}",
        f"slug: {fm.get('slug', slug)}",
        f"tipo: {fm.get('tipo', '')}",
        f"numero: {numero}",
        f"titulo_oficial: {json.dumps(titulo, ensure_ascii=False)}",
        f"publicacion: {parsed.get('fecha_publicacion') or fm.get('publicacion', '')}",
        f"promulgacion: {parsed.get('fecha_promulgacion') or fm.get('promulgacion', '')}",
        f"emisor: {fm.get('emisor', '')}",
        f"leychile_code: {fm.get('leychile_code', '')}",
        f"fuente_oficial: {fm.get('fuente_oficial', '')}",
        f"bcn_uri: {fm.get('bcn_uri', '')}",
        f"version_xml: {parsed.get('fecha_version', '')}",
        f"derogado: {parsed.get('derogado', 'no derogado')}",
    ]
    if parsed.get("nombres_uso_comun"):
        lines.append(f"nombres_uso_comun: {json.dumps(parsed['nombres_uso_comun'], ensure_ascii=False)}")
    if parsed.get("materias"):
        lines.append(f"materias_bcn: {json.dumps(parsed['materias'], ensure_ascii=False)}")
    lines.extend([
        "capa: 2",
        "estado_revision: resumen-estructural",
        "validador: null",
        "fecha_validacion: null",
        "---",
        "",
        f"# {parsed.get('tipo', tipo).upper()} {numero}",
        "",
        f"**Título oficial:** {titulo}",
        "",
    ])

    if parsed.get("nombres_uso_comun"):
        lines.append(f"**Nombre de uso común:** {', '.join(parsed['nombres_uso_comun'])}")
        lines.append("")

    lines.extend([
        f"**Tipo:** {parsed.get('tipo', tipo)}",
        f"**Número:** {numero}",
        f"**Publicación:** {parsed.get('fecha_publicacion', 'desconocida')}",
        f"**Promulgación:** {parsed.get('fecha_promulgacion', 'desconocida')}",
        f"**Versión vigente:** {parsed.get('fecha_version', 'desconocida')}",
        f"**Estado:** {parsed.get('derogado', 'no derogado')}",
        f"**Emisor:** {parsed.get('organismo', fm.get('emisor', 'desconocido'))}",
        "",
    ])

    # Materias BCN
    if parsed.get("materias"):
        lines.append("## Materias (BCN)")
        lines.append("")
        for m in parsed["materias"][:15]:
            lines.append(f"- {m}")
        lines.append("")

    # Encabezado
    if parsed.get("encabezado"):
        lines.append("## Encabezado")
        lines.append("")
        lines.append(f"_{parsed['encabezado'][:400]}_")
        if len(parsed["encabezado"]) > 400:
            lines.append("")
            lines.append("(...) — ver texto íntegro en BCN/LeyChile.")
        lines.append("")

    # Estructura jerárquica
    if parsed.get("estructura"):
        lines.append("## Estructura")
        lines.append("")
        for nivel in parsed["estructura"][:80]:
            indent = "  " * nivel["depth"]
            titulo = nivel.get("titulo", "") or "(sin título)"
            lines.append(f"{indent}- **{nivel['nivel']}**: {titulo}")
        if len(parsed["estructura"]) > 80:
            lines.append("")
            lines.append(f"_(... {len(parsed['estructura']) - 80} niveles más, ver fuente completa)_")
        lines.append("")

    # Artículos
    if parsed.get("articulos"):
        total_art = len(parsed["articulos"])
        lines.append(f"## Artículos ({total_art} totales)")
        lines.append("")
        # Mostrar primeros 30 con incisos
        for art in parsed["articulos"][:30]:
            num = art.get("numero", "?")
            inciso = art.get("inciso_inicial", "").replace("\n", " ").strip()
            lines.append(f"- **Art. {num}** — {inciso}")
        if total_art > 30:
            lines.append("")
            lines.append(f"_(... {total_art - 30} artículos más, ver texto íntegro en BCN/LeyChile)_")
        lines.append("")

    # Modificaciones
    if parsed.get("modificaciones"):
        lines.append("## Modificaciones declaradas en XML")
        lines.append("")
        for mod in parsed["modificaciones"][:10]:
            lines.append(f"- {mod}")
        lines.append("")

    # Fuente
    lines.extend([
        "## Fuente oficial",
        "",
        f"- [BCN/LeyChile (texto vigente)]({fm.get('fuente_oficial', '')})",
        f"- [XML estructurado](https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={fm.get('leychile_code', '')})",
        "",
        "## Estado en el corpus",
        "",
        "Entrada **capa 2** generada automáticamente desde el XML estructurado de BCN.",
        "Contiene metadata + estructura jerárquica + artículos con incisos iniciales.",
        "El texto íntegro NO está incluido — consultar BCN/LeyChile.",
        "",
        "Para promover a **capa 3** (análisis operativo curado con conceptos clave,",
        "conexiones, cuándo invocar, plazos críticos), abrir PR siguiendo el schema en",
        "`chile/normativa/README.md`.",
        "",
        "## Disclaimers",
        "",
        "- Capa 2: estructura auto-generada, sin validación legal sustantiva.",
        "- El texto literal de cada artículo NO está en este archivo. Verificar en BCN.",
        "- `version_xml` indica la fecha de la última versión que LeyChile expone.",
        "",
    ])

    return "\n".join(lines)


def promote_one(slug: str, output_root: Path, *, sleep_ms: int, force: bool, dry_run: bool) -> str:
    """Promueve un archivo capa 1 → capa 2.

    Devuelve estado: 'promoted' | 'skipped' | 'no_xml' | 'already_capa2' | 'error:<msg>'.
    """
    tipo, _, num = slug.partition("/")
    if not tipo or not num:
        return f"error:slug-mal-formado ({slug})"
    # Buscar archivo (con o sin padding)
    candidates = [output_root / tipo / f"{num}.md"]
    if num.isdigit():
        candidates.append(output_root / tipo / f"{num.zfill(5)}.md")
    src = None
    for c in candidates:
        if c.exists():
            src = c
            break
    if not src:
        return f"error:no-encontrado ({slug})"

    content = src.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(content)
    if fm.get("capa") == "2" and not force:
        return "already_capa2"
    code = fm.get("leychile_code", "")
    if not code:
        return "no_xml"

    if dry_run:
        return "would_promote"

    try:
        xml_bytes = download_xml(code, sleep_ms=sleep_ms)
        parsed = parse_norma_xml(xml_bytes)
    except Exception as e:
        return f"error:download-or-parse ({e})"

    new_content = render_capa2(fm, parsed, slug=slug)
    src.write_text(new_content, encoding="utf-8")
    return "promoted"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", help="Slug específico, ej. ley/19628")
    p.add_argument("--tipo", help="Tipo para batch processing (ley, cod, dfl, dl, tra, aa)")
    p.add_argument("--batch", type=int, default=None, help="Máximo de archivos a promover en modo batch")
    p.add_argument("--output", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--sleep-ms", type=int, default=300)
    p.add_argument("--force", action="store_true", help="Sobreescribir capa 2 existente")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.slug and not args.tipo:
        print("ERROR: especificar --slug o --tipo", file=sys.stderr)
        return 2

    if args.dry_run:
        print("[DRY RUN] No se escribirán archivos.")

    if args.slug:
        result = promote_one(
            args.slug,
            args.output,
            sleep_ms=args.sleep_ms,
            force=args.force,
            dry_run=args.dry_run,
        )
        print(f"  {args.slug:30s} → {result}")
        return 0

    # Batch mode
    tipo_dir = args.output / args.tipo
    if not tipo_dir.exists():
        print(f"ERROR: dir no encontrado: {tipo_dir}", file=sys.stderr)
        return 2

    stats = {"promoted": 0, "skipped": 0, "already_capa2": 0, "no_xml": 0, "errors": 0}
    files = sorted(tipo_dir.glob("*.md"))
    for i, f in enumerate(files):
        if args.batch is not None and stats["promoted"] >= args.batch:
            break
        slug = f"{args.tipo}/{f.stem}"
        result = promote_one(
            slug,
            args.output,
            sleep_ms=args.sleep_ms,
            force=args.force,
            dry_run=args.dry_run,
        )
        if result == "promoted" or result == "would_promote":
            stats["promoted"] += 1
        elif result == "already_capa2":
            stats["already_capa2"] += 1
        elif result == "no_xml":
            stats["no_xml"] += 1
        elif result.startswith("error"):
            stats["errors"] += 1
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(files)}] promoted={stats['promoted']} skipped={stats['already_capa2']} sin_xml={stats['no_xml']} errors={stats['errors']}")

    print(f"\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
