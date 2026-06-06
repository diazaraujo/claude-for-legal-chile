"""Capa sensible del perfil de juez (identidad / patrimonio / familia / biografía).

Solo lectura sobre jueces_enriched.sqlite3 (construido offline por el pipeline
rutificación→Mallas en scripts/perfiles/). Esta capa NO se publica en JSON
estático: se sirve únicamente por endpoint con JWTAuth (apps/jueces/api.py).

Gateo por confianza de rutificación: si la identificación nombre→RUT no es
'high', NO se exponen patrimonio/familia (riesgo de homónimo → atribución
errónea). El endpoint devuelve identificado=False en ese caso.
"""
import json
import sqlite3
from pathlib import Path

from django.conf import settings

# Umbral de confianza para exponer identidad/patrimonio/familia.
CONF_MIN = 0.70


def _db_path() -> Path:
    p = getattr(settings, "JUECES_DB", None)
    if p:
        return Path(p)
    return Path(settings.CORPUS_INDEX_DIR) / "jueces_enriched.sqlite3"


def _conn() -> sqlite3.Connection | None:
    p = _db_path()
    if not p.exists():
        return None
    con = sqlite3.connect(f"file:{p}?immutable=1", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def available() -> bool:
    return _db_path().exists()


def _j(s):
    try:
        return json.loads(s) if s else None
    except (ValueError, TypeError):
        return None


def perfil(juez_key: str) -> dict | None:
    """Devuelve la capa sensible de un juez, o None si no hay registro.

    Si la rutificación no alcanza CONF_MIN, devuelve solo el estado de
    identificación (identificado=False) sin patrimonio/familia.
    """
    con = _conn()
    if con is None:
        return None
    try:
        r = con.execute(
            "SELECT * FROM juez_enriched WHERE juez_key = ?", (juez_key,)
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    finally:
        con.close()
    if r is None:
        return None

    conf = r["confianza"] if r["confianza"] is not None else 0.0
    base = {
        "juez_key": r["juez_key"],
        "nombre": r["nombre"],
        "confianza": round(conf, 3),
        "identificado": conf >= CONF_MIN and bool(r["rut_cuerpo"]),
        "fuentes": _j(r["fuentes_json"]) or [],
        "actualizado": r["updated_at"],
    }
    # Biografía proviene de estadísticas reales del corpus → publicable aunque
    # la identificación civil no sea 'high'.
    if r["biografia"]:
        base["biografia"] = r["biografia"]

    if not base["identificado"]:
        base["nota"] = (
            "Identificación civil no confirmada con confianza suficiente; "
            "no se muestran datos personales para evitar atribución por homónimo."
        )
        return base

    base.update({
        "rut": r["rut_fmt"],
        "identidad": {
            "edad": r["edad"],
            "genero": r["genero"],
            "estado_civil": r["estado_civil"],
            "n_hijos": r["n_hijos"],
            "comuna": r["comuna"],
            "nse_decil": r["nse_decil"],
            "conyuge": r["conyuge"],
        },
        "patrimonio": {
            "patrimonio_estimado": r["patrimonio"],
            "bienes_raices": r["bienes_raices"],
            "avaluo_total": r["avaluo"],
        },
        "familia": _j(r["familia_json"]) or [],
    })
    return base
