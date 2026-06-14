"""Fixtures compartidos para los tests del árbol normativo legalchile.

Los tests de datos hacen skip si la DB no está presente (corren donde esté el índice:
local en el Mac o en enigma). Los tests de unidad del extractor siempre corren.
"""
import importlib.util
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CITAS_DB = ROOT / "data/_index/citas_normativas.sqlite3"


def _load(modname: str, relpath: str):
    spec = importlib.util.spec_from_file_location(modname, str(ROOT / relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def extractor():
    """Módulo extract-citas-normativas (regex + extract())."""
    return _load("extract_citas", "scripts/extract-citas-normativas.py")


@pytest.fixture(scope="session")
def citas_con():
    if not CITAS_DB.exists():
        pytest.skip(f"sin DB de citas en {CITAS_DB} (corre donde esté el índice)")
    con = sqlite3.connect(f"file:{CITAS_DB}?mode=ro", uri=True, timeout=60)
    yield con
    con.close()
