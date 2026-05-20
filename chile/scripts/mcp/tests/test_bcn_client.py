"""Tests offline para BCNClient. Usan fixtures XML locales (no requieren BCN online)."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from mcp_bcn_leychile.bcn_client import BCNClient, NormaMetadata

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def make_client(tmp_path: Path) -> BCNClient:
    cache_path = tmp_path / "cache.db"
    return BCNClient(cache_path=cache_path, rate_limit_seconds=0.0)


def test_init_db_creates_tables(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    conn = sqlite3.connect(client.cache_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert "xml_cache" in tables
        assert "metadata_cache" in tables
    finally:
        conn.close()


def test_cache_xml_roundtrip(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client._cache_xml("12345", "<Norma>test</Norma>")
    assert client._cached_xml("12345") == "<Norma>test</Norma>"


def test_cached_xml_returns_none_when_missing(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client._cached_xml("noexiste") is None


def test_parse_metadata_minimal_xml(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Norma xmlns="http://www.leychile.cl/esquemas">
  <Identificador>
    <IdNorma>1075210</IdNorma>
    <TipoNorma>LEY</TipoNorma>
    <Numero>21400</Numero>
    <Titulo>Matrimonio Igualitario</Titulo>
    <FechaPublicacion>2021-12-10</FechaPublicacion>
    <Organismo>Ministerio de Justicia</Organismo>
    <Vigencia>vigente</Vigencia>
  </Identificador>
</Norma>
"""
    meta = client.parse_metadata(xml)
    assert isinstance(meta, NormaMetadata)
    assert meta.id_norma == "1075210"
    assert meta.tipo == "LEY"
    assert meta.numero == "21400"
    assert meta.titulo == "Matrimonio Igualitario"
    assert meta.fecha_publicacion == "2021-12-10"
    assert meta.vigencia == "vigente"
    assert "1075210" in meta.url_consulta


def test_parse_estructura_returns_partes(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Norma xmlns="http://www.leychile.cl/esquemas">
  <Identificador>
    <IdNorma>1</IdNorma>
    <Vigencia>vigente</Vigencia>
  </Identificador>
  <EstructurasFuncionales>
    <EstructuraFuncional tipoParte="Articulo">
      <NumeroParte>1</NumeroParte>
      <Texto>Artículo 1. Esto es texto de ejemplo.</Texto>
    </EstructuraFuncional>
    <EstructuraFuncional tipoParte="Articulo">
      <NumeroParte>2</NumeroParte>
      <Texto>Artículo 2. Segundo artículo.</Texto>
    </EstructuraFuncional>
  </EstructurasFuncionales>
</Norma>
"""
    estructura = client.parse_estructura(xml)
    assert len(estructura) == 2
    assert estructura[0].tipo_parte == "Articulo"
    assert estructura[0].numero == "1"
    assert "Artículo 1" in estructura[0].texto


def test_parse_estructura_handles_nesting(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Norma xmlns="http://www.leychile.cl/esquemas">
  <Identificador><IdNorma>1</IdNorma></Identificador>
  <EstructurasFuncionales>
    <EstructuraFuncional tipoParte="Titulo">
      <NumeroParte>I</NumeroParte>
      <TituloParte>Disposiciones Generales</TituloParte>
      <Texto>Texto título I</Texto>
      <EstructuraFuncional tipoParte="Articulo">
        <NumeroParte>1</NumeroParte>
        <Texto>Texto del artículo 1.</Texto>
      </EstructuraFuncional>
    </EstructuraFuncional>
  </EstructurasFuncionales>
</Norma>
"""
    estructura = client.parse_estructura(xml)
    assert len(estructura) == 1
    titulo = estructura[0]
    assert titulo.tipo_parte == "Titulo"
    assert titulo.titulo == "Disposiciones Generales"
    assert len(titulo.hijos) == 1
    assert titulo.hijos[0].numero == "1"


def test_check_vigencia_uses_metadata(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Norma xmlns="http://www.leychile.cl/esquemas">
  <Identificador>
    <IdNorma>9999</IdNorma>
    <Titulo>Ejemplo</Titulo>
    <Vigencia>vigente</Vigencia>
  </Identificador>
</Norma>
"""
    client._cache_xml("9999", xml)
    result = client.check_vigencia("9999")
    assert result["id_norma"] == "9999"
    assert result["vigente"] is True
    assert result["vigencia_declarada"] == "vigente"
