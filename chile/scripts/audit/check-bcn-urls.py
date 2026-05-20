#!/usr/bin/env python3
# std:input chile/normativa/leyes/, chile/normativa/codigos/, chile/normativa/constitucion/, chile/normativa/decretos/
# std:output reporte stdout + exit code (0 ok, 1 discrepancias encontradas)
# std:deps mcp-bcn-leychile (chile/scripts/mcp/)
"""
Verifica URLs BCN de cada perfil capa 3 contra el contenido real de BCN.

Para cada archivo:
1. Lee `fuente_oficial:` del frontmatter.
2. Extrae el `idNorma` de la URL.
3. Fetch del XML BCN (con cache + rate limiting).
4. Compara `titulo_oficial` del frontmatter con `TituloNorma` del XML.
5. Compara `numero` declarado (en `norma:`) con `Numero` del XML.
6. Reporta discrepancias.

Salida: reporte por archivo + resumen al final.
Exit 0 si todas las URLs apuntan a la norma correcta.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Optional

# Permitir import del cliente MCP desde el repo
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "chile" / "scripts" / "mcp" / "src"))

from mcp_bcn_leychile.bcn_client import BCNClient  # noqa: E402

CAPA3_DIRS = [
    Path("chile/normativa/leyes"),
    Path("chile/normativa/codigos"),
    Path("chile/normativa/constitucion"),
    Path("chile/normativa/decretos"),
]

URL_RE = re.compile(r"idNorma=(\d+)")


def parse_simple_frontmatter(content: str) -> dict[str, str]:
    """YAML naïve parser — solo scalars de un solo nivel."""
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
        v = v.strip()
        if v:  # Solo scalars
            fields[k.strip()] = v
    return fields


def extract_norma_numero(norma_str: str) -> Optional[str]:
    """De 'Ley 21.400' o 'DL 825' extrae '21400' o '825'."""
    m = re.search(r"(\d[\d.]*)", norma_str)
    if not m:
        return None
    return m.group(1).replace(".", "")


STOPWORDS = {
    "ley", "la", "el", "de", "del", "los", "las", "que", "por",
    "modifica", "establece", "regula", "fija", "diversos", "sobre",
    "cuerpos", "legales", "para", "se", "y", "a", "en", "un", "una",
    "al", "como", "su", "sus", "es", "no", "lo", "este", "esta",
    "código", "decreto", "ley", "norma", "art", "n",
}


def _tokens(s: str) -> set[str]:
    """Extrae palabras significativas normalizadas (sin tildes, sin
    stopwords) de longitud >= 4."""
    s = s.lower()
    # Quitar tildes simples
    repl = str.maketrans("áéíóúñü", "aeiounu")
    s = s.translate(repl)
    words = re.findall(r"[a-z]+", s)
    return {w for w in words if len(w) >= 4 and w not in STOPWORDS}


def compare_titulos(local: str, bcn: str) -> bool:
    """Match si al menos 1 palabra clave del título declarado aparece
    en el BCN. Elimina falsos positivos cuando BCN usa solo la
    descripción operativa (ej. 'FIJA TEXTO REFUNDIDO DEL CODIGO DEL
    TRABAJO' vs 'Código del Trabajo')."""
    local_tokens = _tokens(local)
    bcn_tokens = _tokens(bcn)
    if not local_tokens:
        return True  # No hay forma de verificar
    overlap = local_tokens & bcn_tokens
    # Pide al menos 1 palabra clave en común
    return len(overlap) >= 1


def check_file(path: Path, client: BCNClient) -> list[str]:
    """Devuelve lista de discrepancias (vacía si OK)."""
    content = path.read_text(encoding="utf-8")
    fm = parse_simple_frontmatter(content)

    url = fm.get("fuente_oficial", "")
    if not url:
        return ["sin campo fuente_oficial"]

    m = URL_RE.search(url)
    if not m:
        return [f"URL sin idNorma reconocible: {url}"]

    id_norma = m.group(1)
    norma_declarada = fm.get("norma", "")
    titulo_declarado = fm.get("titulo_oficial", "")
    numero_declarado = extract_norma_numero(norma_declarada)

    try:
        xml = client.fetch_xml(id_norma)
        meta = client.parse_metadata(xml)
    except Exception as e:
        return [f"BCN error ({type(e).__name__}): no se pudo verificar id={id_norma}"]

    discrepancias = []

    # Verificar número
    if numero_declarado and meta.numero:
        # BCN puede tener leading zeros
        bcn_num = meta.numero.lstrip("0")
        if bcn_num != numero_declarado:
            discrepancias.append(
                f"NUMERO: declarado='{numero_declarado}' BCN='{bcn_num}'"
            )

    # Verificar título (fuzzy match)
    if titulo_declarado and meta.titulo:
        # Strip quotes si las hay
        td = titulo_declarado.strip('"').strip("'").strip()
        if not compare_titulos(td, meta.titulo):
            discrepancias.append(
                f"TITULO: declarado='{td[:60]}...' BCN='{meta.titulo[:60]}...'"
            )

    return discrepancias


def main() -> int:
    files = []
    for d in CAPA3_DIRS:
        full = REPO_ROOT / d
        if not full.exists():
            continue
        files.extend(sorted(full.glob("*.md")))

    files = [f for f in files if not f.stem.startswith("00-")]
    print(f"[INFO] {len(files)} perfiles capa 3 a verificar contra BCN")
    print(f"[INFO] Rate limit: 1 req/seg → ~{len(files)} segundos estimados\n")

    client = BCNClient(rate_limit_seconds=1.0)

    ok = 0
    discrep = 0
    errors = 0
    start = time.time()

    for i, f in enumerate(files, 1):
        rel = f.relative_to(REPO_ROOT)
        try:
            disc = check_file(f, client)
        except Exception as e:
            errors += 1
            print(f"[{i}/{len(files)}] EXCEPTION {rel}: {e}")
            continue

        if not disc:
            ok += 1
            # Imprimir solo cada 20 para no inundar
            if i % 20 == 0:
                elapsed = time.time() - start
                print(f"  [{i}/{len(files)}] ok ({elapsed:.0f}s elapsed)")
        else:
            discrep += 1
            print(f"\n[DISCREPANCIA] {rel}")
            for d in disc:
                print(f"  - {d}")

    elapsed = time.time() - start
    print(f"\n[SUMMARY] {elapsed:.0f}s elapsed")
    print(f"  OK: {ok}")
    print(f"  Discrepancias: {discrep}")
    print(f"  Errores BCN: {errors}")

    return 0 if discrep == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
