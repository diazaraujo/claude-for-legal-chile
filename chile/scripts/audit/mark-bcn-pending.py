#!/usr/bin/env python3
# std:input archivo de discrepancias pendientes (1 por línea con [DISCREPANCIA] prefix)
# std:output modifica frontmatter agregando fuente_oficial_status: pendiente-verificacion-bcn
# std:deps stdlib pura
"""
Marca perfiles capa 3 con URL BCN pendiente de verificación.

Para cada archivo de la lista de pendientes:
1. Lee frontmatter.
2. Agrega campo `fuente_oficial_status: pendiente-verificacion-bcn` si no existe.
3. Mantiene `fuente_oficial` (URL existente — el sistema necesita una URL aunque
   sea sospechosa para no romper parsers).
4. Agrega disclaimer al inicio del cuerpo si no está.

Conforme a regla de memoria: NO inventar URLs/IDs. Mantener URL existente
pero marcar honestamente que requiere verificación.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DISCLAIMER = (
    "> ⚠️ **URL BCN pendiente de verificación.** El catálogo capa 1 no contiene\n"
    "> el ID de esta norma; el campo `fuente_oficial` puede apuntar a una norma\n"
    "> distinta. Verificar contra BCN antes de citar.\n\n"
)


def main(input_file: Path) -> int:
    pendientes = []
    for line in input_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("[DISCREPANCIA]"):
            path_str = line.replace("[DISCREPANCIA]", "").strip()
            pendientes.append(REPO_ROOT / path_str)

    print(f"[INFO] {len(pendientes)} archivos a marcar como pendientes")

    modified = 0
    for f in pendientes:
        if not f.exists():
            print(f"  SKIP: {f} no existe")
            continue

        content = f.read_text(encoding="utf-8")

        # Skip si ya está marcado
        if "fuente_oficial_status:" in content:
            continue

        # Agregar fuente_oficial_status al frontmatter
        new_content = re.sub(
            r"(^fuente_oficial:.*\n)",
            r"\1fuente_oficial_status: pendiente-verificacion-bcn\n",
            content,
            count=1,
            flags=re.MULTILINE,
        )

        # Agregar disclaimer al inicio del cuerpo si no está
        if "URL BCN pendiente de verificación" not in new_content:
            # Buscar el primer header después del frontmatter
            fm_end = new_content.find("\n---\n", 4)
            if fm_end != -1:
                body_start = fm_end + 5  # after \n---\n
                # Encontrar la primera línea no vacía
                rest = new_content[body_start:]
                new_content = (
                    new_content[:body_start] + "\n" + DISCLAIMER + rest.lstrip("\n")
                )

        if new_content != content:
            f.write_text(new_content, encoding="utf-8")
            modified += 1
            print(f"  marked: {f.relative_to(REPO_ROOT)}")

    print(f"\n[DONE] {modified} archivos modificados")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: mark-bcn-pending.py <archivo-con-DISCREPANCIA>")
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
