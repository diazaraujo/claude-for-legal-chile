"""Generador de citas formales desde paths del corpus.

Conoce patrones de naming de cada fuente y extrae rol/edicion/año
para producir una cita verificable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Citation:
    source: str
    citation: str         # cita formal corta (ej. "STC Rol N° 17.083-2025")
    long_citation: str    # cita extendida (caratula + fecha)
    rol: str = ""
    fecha: str = ""
    extra: dict | None = None


def _norm_rol(s: str) -> str:
    """17_083-25 → 17.083-2025. Normaliza underscores y expande año."""
    s = s.replace("_", ".").replace("-", "-")
    parts = s.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 2:
        n = int(parts[1])
        century = 2000 if n < 50 else 1900
        return f"{parts[0]}-{century + n}"
    return s


def from_path(path: str) -> Citation:
    """Parsea un path del corpus → Citation."""
    p = Path(path)
    parts = p.parts
    fname = p.name.replace(".pdf.txt", ".pdf").replace(".xml.txt", ".xml")

    # Detectar fuente desde el path
    src = ""
    if "chile/data" in path:
        idx = parts.index("data") if "data" in parts else -1
        if idx >= 0 and idx + 1 < len(parts):
            src = parts[idx + 1]
    src_lower = src.lower()

    # ── TC moderno ──
    if src_lower == "tc-moderno":
        # STC_Rol_N_17_083-25_INA.pdf, Sentencia_Rol_16_597-25-INA___.pdf
        m = re.search(r"Rol[_ ]N?_?(\d+[_.]?\d*)[_-](\d{2})", fname, re.I)
        if m:
            rol_num = m.group(1).replace("_", ".")
            yy = int(m.group(2))
            year = 2000 + yy if yy < 50 else 1900 + yy
            # tipo procedimiento — buscar 2-4 letras mayúsculas separadas
            # por _ o - antes de .pdf (puede ser INA, CPR, RIN, INC).
            tipo_m = re.search(r"[-_]([A-Z]{2,4})(?:[._-]|\.pdf|$)", fname)
            tipo = tipo_m.group(1).upper() if tipo_m else ""
            tipo_full = {"INA": "Inaplicabilidad", "CPR": "Control Preventivo",
                         "RIN": "Requerimiento Inconstitucionalidad",
                         "INC": "Inconstitucionalidad"}.get(tipo, tipo)
            short = f"STC Rol N° {rol_num}-{year}"
            if tipo: short += f" ({tipo})"
            return Citation(
                source="tc-moderno", citation=short,
                long_citation=f"{short} — Tribunal Constitucional, {tipo_full}",
                rol=f"{rol_num}-{year}",
                extra={"tipo_procedimiento": tipo},
            )

    # ── TC legacy ──
    if src_lower == "tc":
        m = re.search(r"tc_(\d+)\.pdf", fname)
        if m:
            return Citation(
                source="tc-legacy", citation=f"TC ID Legacy {m.group(1)}",
                long_citation=f"Tribunal Constitucional, expediente legacy id={m.group(1)}",
                rol=m.group(1),
            )

    # ── TDLC ──
    if src_lower == "tdlc":
        # path: tdlc/sentencia-159-2017-demanda-de-conadecus-contra-cencosud/foo.pdf
        idx = parts.index("tdlc") if "tdlc" in parts else -1
        if idx >= 0 and idx + 1 < len(parts):
            slug = parts[idx + 1]
            m = re.match(r"sentencia-(\d+)-(\d{4})-(.+)", slug)
            if m:
                num, year, rest = m.group(1), m.group(2), m.group(3)
                caratula = rest.replace("-", " ").title()[:100]
                return Citation(
                    source="tdlc", citation=f"TDLC Sentencia N° {num}/{year}",
                    long_citation=f"TDLC Sentencia N° {num}/{year} — {caratula}",
                    rol=f"{num}/{year}",
                    extra={"caratula": caratula, "doc_archivo": fname},
                )

    # ── TDPI ──
    if src_lower == "tdpi":
        # 4-PATENTE-DE-INVENCION-BIOQUIMICA-ROL-TdPI-0613-2024-...
        m = re.search(r"ROL[_-]TdPI[_-](\d+)[_-](\d{4})", fname, re.I)
        if m:
            rol = m.group(1).lstrip("0")
            year = m.group(2)
            tipo_m = re.search(r"(PATENTE-DE-INVENCION-\w+|MARCA-COMERCIAL|VARIEDAD-VEGETAL)",
                               fname, re.I)
            tipo = tipo_m.group(1).replace("-", " ").title() if tipo_m else ""
            return Citation(
                source="tdpi", citation=f"TDPI Rol N° {rol}/{year}",
                long_citation=f"TDPI Rol N° {rol}/{year}" + (f" — {tipo}" if tipo else ""),
                rol=f"{rol}/{year}", fecha=year,
                extra={"tipo": tipo},
            )

    # ── Diario Oficial ──
    if src_lower == "diario-oficial":
        # 2024/03/15/edicion_N/M.pdf
        m = re.search(r"(\d{4})/(\d{2})/(\d{2})/edicion_(\d+)/(\d+)\.pdf",
                      str(p))
        if m:
            yyyy, mm, dd, ed, pub_id = m.groups()
            fecha = f"{dd}-{mm}-{yyyy}"
            return Citation(
                source="diario-oficial",
                citation=f"D.O. edición N° {ed} ({fecha})",
                long_citation=f"Diario Oficial de Chile, edición N° {ed}, "
                              f"publicación {pub_id}, {fecha}",
                fecha=fecha,
                extra={"edicion": ed, "publicacion_id": pub_id},
            )

    # ── LeyChile XMLs ──
    if src_lower == "leychile" or src_lower.startswith("leychile-"):
        # leychile/ley/1199623.xml → idNorma 1199623
        m = re.search(r"/(ley|dto|dfl|dl|cod)/(\d+)\.xml", str(p))
        if m:
            tipo, idn = m.group(1), m.group(2)
            tipo_name = {"ley": "Ley", "dto": "Decreto Supremo",
                         "dfl": "DFL", "dl": "Decreto Ley",
                         "cod": "Código"}.get(tipo, tipo.upper())
            return Citation(
                source=f"leychile-{tipo}",
                citation=f"{tipo_name} (idNorma BCN {idn})",
                long_citation=f"{tipo_name} — BCN idNorma {idn}, "
                              f"texto íntegro https://www.leychile.cl/Navegar?idNorma={idn}",
                rol=idn,
                extra={"id_norma": idn, "tipo": tipo,
                       "leychile_url": f"https://www.leychile.cl/Navegar?idNorma={idn}"},
            )

    # ── Tribunales Ambientales ──
    if src_lower == "tribunales-ambientales":
        idx = parts.index("tribunales-ambientales") if "tribunales-ambientales" in parts else -1
        tribunal_dir = parts[idx + 1] if idx >= 0 and idx + 1 < len(parts) else ""
        tribunal = {"tribunal-12": "2° Tribunal Ambiental (Santiago)",
                    "tribunal-3": "3er Tribunal Ambiental (Valdivia)"}.get(
                        tribunal_dir, f"Tribunal Ambiental ({tribunal_dir})")
        # Try parse Rol R-NNN-YYYY or R_NNN_YYYY
        m = re.search(r"R[-_](\d+)[-_](\d{4})", fname)
        if m:
            return Citation(
                source="tribunales-ambientales",
                citation=f"{tribunal} R-{m.group(1)}-{m.group(2)}",
                long_citation=f"{tribunal}, expediente R-{m.group(1)}-{m.group(2)}",
                rol=f"R-{m.group(1)}-{m.group(2)}",
            )
        return Citation(
            source="tribunales-ambientales", citation=tribunal,
            long_citation=f"{tribunal} — {fname}",
        )

    # ── FNE ──
    if src_lower == "fne":
        # posts/2024/post_id.html o pdfs/2024/post_id_archivo.pdf
        m = re.search(r"/(\d{4})/(\d+)_", str(p))
        if m:
            return Citation(
                source="fne",
                citation=f"FNE post {m.group(2)} ({m.group(1)})",
                long_citation=f"Fiscalía Nacional Económica, post {m.group(2)}, "
                              f"año {m.group(1)} — ver fne.gob.cl",
                fecha=m.group(1),
            )

    # ── SII circulares ──
    if src_lower == "sii":
        # Filename: circu31.pdf. Year viene del directorio: /sii/2017/
        m = re.search(r"(?:circu|cir)[-_]?(\d+)", fname, re.I)
        year = ""
        for part in parts:
            if re.fullmatch(r"(19|20)\d{2}", part):
                year = part
                break
        if m:
            num = m.group(1)
            cite_short = f"SII Circular N° {num}" + (f"/{year}" if year else "")
            return Citation(
                source="sii", citation=cite_short,
                long_citation=f"Servicio de Impuestos Internos, "
                              f"Circular N° {num}" + (f" de {year}" if year else ""),
                rol=f"{num}/{year}" if year else num, fecha=year,
            )

    # ── CMF ──
    if src_lower == "cmf":
        m = re.search(r"(?:ncg|circ?)[-_]?(\d+).*?(\d{4})", fname, re.I)
        if m:
            tipo = "NCG" if "ncg" in fname.lower() else "Circular"
            return Citation(
                source="cmf", citation=f"CMF {tipo} N° {m.group(1)}/{m.group(2)}",
                long_citation=f"Comisión para el Mercado Financiero, "
                              f"{tipo} N° {m.group(1)} de {m.group(2)}",
                rol=f"{m.group(1)}/{m.group(2)}",
            )

    # ── Default ──
    return Citation(
        source=src or "desconocido",
        citation=f"{src or 'doc'}: {fname[:80]}",
        long_citation=f"{src or 'documento'} — {fname}",
    )
