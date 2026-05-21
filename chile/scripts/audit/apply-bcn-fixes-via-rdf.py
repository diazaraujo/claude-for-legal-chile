#!/usr/bin/env python3
# std:input archivos capa 3 marcados con fuente_oficial_status: pendiente-verificacion-bcn
# std:output modifica frontmatter con ID correcto cuando RDF de BCN responde
# std:deps stdlib pura
"""
Resuelve URLs BCN pendientes usando el endpoint RDF de datos.bcn.cl.

Para cada perfil con `fuente_oficial_status: pendiente-verificacion-bcn`:
1. Extrae número de norma del slug (ej. ley-21400-* → 21400).
2. Fetch https://datos.bcn.cl/recurso/cl/ley/{numero} con Accept rdf+xml.
3. Parsea bcnnorms:leychileCode + rdfs:label.
4. Match de título declarado vs label del RDF (≥1 palabra clave).
5. Si match: actualiza fuente_oficial + remueve fuente_oficial_status +
   remueve disclaimer del cuerpo.

Solo soporta tipo `ley/`. DL/DFL/DS quedan pendientes.

Conforme a regla de memoria 'no inventar IDs': no inventa, sólo aplica
lo que el RDF oficial confirma.
"""

from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SLUG_RE = re.compile(r"^(ley|dl|dfl)-(\d+)(?:-|$)")
LEYCHILE_CODE_RE = re.compile(r"leychileCode[^>]*>(\d+)<")
LABEL_RE = re.compile(r"<rdfs:label[^>]*>([^<]+)<")
USER_AGENT = "claude-legal-chile/0.5 (unholster.com)"

STOPWORDS = {
    "ley", "la", "el", "de", "del", "los", "las", "que", "por", "sobre",
    "modifica", "establece", "regula", "fija", "diversos", "que",
    "cuerpos", "legales", "para", "se", "y", "a", "en", "un", "una",
    "al", "como", "su", "sus", "es", "no", "lo", "este", "esta",
    "codigo", "decreto", "norma", "art", "n", "del",
}


def _tokens(s: str) -> set[str]:
    s = s.lower()
    s = s.translate(str.maketrans("áéíóúñü", "aeiounu"))
    return {w for w in re.findall(r"[a-z]+", s) if len(w) >= 4 and w not in STOPWORDS}


def titulo_match(local: str, remote: str) -> bool:
    a = _tokens(local)
    b = _tokens(remote)
    return bool(a) and bool(a & b)


def lookup_id(tipo: str, numero: str) -> tuple[str | None, str | None]:
    """Devuelve (leychile_code, label) o (None, None)."""
    if tipo != "ley":
        return None, None  # Solo ley/ funciona en este endpoint
    url = f"https://datos.bcn.cl/recurso/cl/ley/{numero}"
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/rdf+xml"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read().decode()
        m = LEYCHILE_CODE_RE.search(data)
        label = LABEL_RE.search(data)
        return (
            m.group(1) if m else None,
            label.group(1) if label else None,
        )
    except urllib.error.HTTPError:
        return None, None
    except Exception:
        return None, None


def parse_fm(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}
    raw = content[4:end]
    fields = {}
    for line in raw.split("\n"):
        if ":" not in line or line.startswith("  "):
            continue
        k, _, v = line.partition(":")
        if v.strip():
            fields[k.strip()] = v.strip()
    return fields


DISCLAIMER_RE = re.compile(
    r"^\s*\n*> ⚠️ \*\*URL BCN pendiente de verificación\.\*\*[^\n]*\n(> [^\n]*\n)*\n",
    re.MULTILINE,
)


def main() -> int:
    capa3_dirs = [
        REPO_ROOT / "chile/normativa/leyes",
        REPO_ROOT / "chile/normativa/codigos",
        REPO_ROOT / "chile/normativa/decretos",
    ]
    files: list[Path] = []
    for d in capa3_dirs:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))

    candidatos = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        if "fuente_oficial_status: pendiente-verificacion-bcn" not in content:
            continue
        candidatos.append(f)

    print(f"[INFO] {len(candidatos)} perfiles pendientes a resolver via RDF")

    applied = 0
    no_match_titulo = 0
    no_id = 0
    skipped_tipo = 0

    for i, f in enumerate(candidatos, 1):
        m = SLUG_RE.match(f.stem)
        if not m:
            skipped_tipo += 1
            continue
        tipo = m.group(1)
        numero = m.group(2)

        if tipo != "ley":
            skipped_tipo += 1
            continue

        time.sleep(0.5)  # rate limit suave
        code, label = lookup_id(tipo, numero)
        if not code:
            no_id += 1
            print(f"  [{i}/{len(candidatos)}] {f.stem}: SIN ID en BCN RDF")
            continue

        content = f.read_text(encoding="utf-8")
        fm = parse_fm(content)
        titulo_perfil = fm.get("titulo_oficial", "").strip('"')

        if not titulo_match(titulo_perfil, label or ""):
            no_match_titulo += 1
            print(
                f"  [{i}/{len(candidatos)}] {f.stem}: id={code} pero TITULO no matchea\n"
                f"      local={titulo_perfil[:60]!r}\n"
                f"      bcn  ={(label or '')[:60]!r}"
            )
            continue

        new_url = f"https://www.bcn.cl/leychile/navegar?idNorma={code}"
        new_content = re.sub(
            r"^fuente_oficial:.*$",
            f"fuente_oficial: {new_url}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        # Remover el status pendiente
        new_content = re.sub(
            r"^fuente_oficial_status: pendiente-verificacion-bcn\n",
            "",
            new_content,
            count=1,
            flags=re.MULTILINE,
        )
        # Remover el disclaimer del cuerpo
        new_content = DISCLAIMER_RE.sub("", new_content, count=1)

        f.write_text(new_content, encoding="utf-8")
        applied += 1
        print(f"  [{i}/{len(candidatos)}] {f.stem}: id={code} APLICADO")

    print(f"\n[DONE]")
    print(f"  Aplicados: {applied}")
    print(f"  Sin ID en BCN: {no_id}")
    print(f"  Título no matchea: {no_match_titulo}")
    print(f"  Skipped (DL/DFL/DS): {skipped_tipo}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
