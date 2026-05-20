#!/usr/bin/env python3
# std:input chile/normativa/**, chile/perfiles/**, chile/skills/**, chile/ejemplos/**
# std:output reporte stdout + exit code (0 ok, 1 errores encontrados)
# std:deps stdlib pura
"""
Verifica que los links Markdown internos del corpus apunten a archivos
existentes en el repositorio.

Chequeos:
1. Para cada `[texto](ruta.md)` en archivos Markdown, resuelve la
   ruta relativa contra el archivo origen.
2. Verifica que el archivo destino exista.
3. Reporta links rotos como ERROR.
4. Ignora URLs externas (https://, http://, mailto:, etc.).
5. Ignora anchors (#section) cuando van solos.
"""

import sys
import re
from pathlib import Path


SCAN_DIRS = [
    Path("chile/normativa"),
    Path("chile/perfiles"),
    Path("chile/skills"),
    Path("chile/ejemplos"),
    Path("chile/audits"),
]

# Regex para detectar Markdown links: [text](target)
# Captura el target (grupo 1) — ignora image links ![alt](src)
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")

# URLs externas a ignorar
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "tel:")


def is_internal_link(target: str) -> bool:
    """True si el target es link interno del repo (no URL externa)."""
    target_lower = target.lower().strip()
    if any(target_lower.startswith(p) for p in EXTERNAL_PREFIXES):
        return False
    # Solo anchors (#section) sin ruta = link interno al mismo archivo
    if target_lower.startswith("#"):
        return False  # No verificamos anchors por ahora
    return True


def resolve_link(source_file: Path, target: str, repo_root: Path) -> Path:
    """Resuelve un target relativo contra el archivo origen.
    Strip de anchors (#section) y querystring."""
    # Strip anchor + querystring
    if "#" in target:
        target = target.split("#", 1)[0]
    if "?" in target:
        target = target.split("?", 1)[0]
    target = target.strip()

    if not target:
        return None  # Era solo anchor

    # Resolver relativo al directorio del archivo origen
    resolved = (source_file.parent / target).resolve()
    return resolved


def check_file(path: Path, repo_root: Path) -> list[str]:
    """Devuelve lista de errores (links rotos) en el archivo."""
    errors = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"no se pudo leer: {e}"]

    for match in LINK_RE.finditer(content):
        target = match.group(1).strip()
        if not is_internal_link(target):
            continue

        resolved = resolve_link(path, target, repo_root)
        if resolved is None:
            continue  # Era solo anchor

        if not resolved.exists():
            try:
                target_rel = resolved.relative_to(repo_root)
            except ValueError:
                target_rel = resolved
            errors.append(f"link roto -> {target} (resuelve a {target_rel})")

    return errors


def main():
    repo_root = Path(__file__).resolve().parents[3]
    files = []
    for d in SCAN_DIRS:
        full = repo_root / d
        if not full.exists():
            print(f"[WARN] directorio no existe: {full}")
            continue
        files.extend(sorted(full.rglob("*.md")))

    print(f"[INFO] {len(files)} archivos Markdown a auditar")

    total_errors = 0
    files_with_errors = 0

    for f in files:
        errors = check_file(f, repo_root)
        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            rel = f.relative_to(repo_root)
            print(f"\n[ERROR] {rel}")
            for e in errors:
                print(f"  - {e}")

    print(f"\n[SUMMARY]")
    print(f"  Archivos auditados: {len(files)}")
    print(f"  Archivos con links rotos: {files_with_errors}")
    print(f"  Total links rotos: {total_errors}")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
