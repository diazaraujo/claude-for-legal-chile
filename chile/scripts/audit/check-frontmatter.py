#!/usr/bin/env python3
# std:input chile/normativa/leyes/, chile/normativa/codigos/, chile/normativa/constitucion/
# std:output reporte stdout + exit code (0 ok, 1 errores encontrados)
# std:deps stdlib pura
"""
Verifica consistencia técnica del frontmatter del corpus capa 3.

Chequeos:
1. Frontmatter YAML válido y presente.
2. Campos obligatorios presentes (slug, titulo_oficial, fuente_oficial,
   vigencia, capa, estado_revision).
3. Slug del frontmatter == nombre del archivo (sin .md).
4. URL BCN tiene formato esperado.
5. URLs BCN no duplicadas (alerta cuando lo están).
6. Estado de revisión es valor canónico (ver MARCADORES.md).
7. Frontmatter usa `relacionada_per` (no `relacionada_con`).
8. `relacionada_per` apunta a slugs que existen en el corpus.

Sin verificación externa contra BCN (esto requiere check-bcn-urls.py).
"""

import sys
from pathlib import Path
from collections import defaultdict
import re


CAPA3_DIRS = [
    Path("chile/normativa/leyes"),
    Path("chile/normativa/codigos"),
    Path("chile/normativa/constitucion"),
]

REQUIRED_FIELDS = ["slug", "titulo_oficial", "fuente_oficial", "vigencia",
                   "capa", "estado_revision"]

VALID_ESTADOS = {
    "borrador-no-validado",
    "en-revision",
    "validada",
    "obsoleta",
    "requiere-refactor-llm-wiki",
    "fuera-de-alcance",
}

BCN_URL_RE = re.compile(r"^https://www\.bcn\.cl/leychile/navegar\?idNorma=\d+$")


def parse_frontmatter(content: str) -> dict | None:
    """Extrae el frontmatter YAML del inicio del archivo. Naïve YAML
    parsing — no requiere PyYAML."""
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---\n", 4)
    if end == -1:
        return None
    raw = content[4:end]
    fields = {}
    current_key = None
    current_list = None
    for line in raw.split("\n"):
        if not line.strip():
            continue
        # Línea de lista
        if line.startswith("  - "):
            if current_list is not None:
                current_list.append(line[4:].strip())
            continue
        # Línea de campo
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v:
                fields[k] = v
                current_list = None
            else:
                # Campo con valor lista
                fields[k] = []
                current_list = fields[k]
            current_key = k
    return fields


def check_file(path: Path, slug_set: set[str], url_counts: dict[str, list[str]]) -> list[str]:
    """Devuelve lista de errores en el archivo (vacía si OK)."""
    errors = []
    content = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    if fm is None:
        errors.append("sin frontmatter YAML al inicio")
        return errors

    # 1. Campos obligatorios
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"falta campo obligatorio: {field}")

    # 2. Slug == nombre del archivo
    expected_slug = path.stem
    if fm.get("slug") and fm["slug"] != expected_slug:
        errors.append(f"slug del frontmatter '{fm['slug']}' != nombre archivo '{expected_slug}'")

    # 3. URL BCN
    url = fm.get("fuente_oficial", "")
    if url and not BCN_URL_RE.match(url):
        errors.append(f"URL BCN con formato inválido: {url}")
    elif url:
        url_counts[url].append(expected_slug)

    # 4. Estado revisión canónico
    estado = fm.get("estado_revision")
    if estado and estado not in VALID_ESTADOS:
        errors.append(f"estado_revision '{estado}' no canónico (ver MARCADORES.md)")

    # 5. relacionada_con vs relacionada_per
    if "relacionada_con" in fm:
        errors.append("usa campo legacy 'relacionada_con' — canonical es 'relacionada_per'")

    # 6. relacionada_per apunta a slugs existentes (WARN si no, no ERROR)
    relacionada = fm.get("relacionada_per", [])
    warns = []
    if isinstance(relacionada, list):
        for ref_slug in relacionada:
            if ref_slug not in slug_set:
                # Slug que aún no existe = marcador de trabajo futuro
                # válido según MARCADORES.md (linking liberalmente)
                warns.append(f"relacionada_per -> '{ref_slug}' (slug futuro / no existe aún)")

    # Devolvemos errores como ERROR y warns separados
    return errors, warns


def main():
    """Ejecuta la auditoría. Retorna exit 0 si todo OK, 1 si hay errores."""
    root = Path(__file__).resolve().parents[3]
    files = []
    for d in CAPA3_DIRS:
        full = root / d
        if not full.exists():
            print(f"[WARN] directorio no existe: {full}")
            continue
        files.extend(sorted(full.glob("*.md")))

    # Set de slugs disponibles
    slug_set = {f.stem for f in files}
    print(f"[INFO] {len(files)} archivos capa 3 a auditar")

    url_counts: dict[str, list[str]] = defaultdict(list)
    total_errors = 0
    total_warns = 0
    files_with_errors = 0
    files_with_warns = 0

    for f in files:
        # Skip indices
        if f.stem.startswith("00-"):
            continue
        errors, warns = check_file(f, slug_set, url_counts)
        rel = f.relative_to(root)
        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            print(f"\n[ERROR] {rel}")
            for e in errors:
                print(f"  - {e}")
        if warns:
            files_with_warns += 1
            total_warns += len(warns)
            print(f"\n[WARN] {rel}")
            for w in warns:
                print(f"  - {w}")

    # URLs duplicadas
    print("\n[INFO] URLs BCN con duplicación:")
    duplicates_found = False
    for url, slugs in sorted(url_counts.items()):
        if len(slugs) > 1:
            duplicates_found = True
            print(f"  {url}")
            for s in slugs:
                print(f"    - {s}")

    if not duplicates_found:
        print("  (ninguna)")

    # Resumen
    print(f"\n[SUMMARY]")
    print(f"  Archivos auditados: {len(files)}")
    print(f"  Archivos con errores: {files_with_errors}")
    print(f"  Total errores: {total_errors}")
    print(f"  Archivos con warnings: {files_with_warns}")
    print(f"  Total warnings: {total_warns}")
    print(f"  URLs BCN duplicadas: {sum(1 for s in url_counts.values() if len(s) > 1)}")

    # Exit 0 si no hay ERRORS (warnings sí permitidos)
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
