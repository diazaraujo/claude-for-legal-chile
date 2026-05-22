#!/usr/bin/env python3
"""Smoke tests para todos los MCPs chile/scripts/mcp-*.

Verifica que cada MCP:
1. Importa sin fallos.
2. Su client class puede ser instanciado.
3. Funciones críticas de URL/ID building funcionan (sin red).

Correr: python3 chile/scripts/test_mcps_smoke.py
"""
from __future__ import annotations
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent  # chile/scripts/
SRC_DIRS = sorted(_SCRIPTS.glob("mcp-*/src"))
for s in SRC_DIRS:
    sys.path.insert(0, str(s))

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        fn()
        RESULTS.append((name, True, ""))
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {str(e)[:80]}"))


def test_cgr():
    from mcp_cgr_dictamenes.cgr_client import CGRClient, format_dictamen_id
    assert format_dictamen_id(66847, 2010) == "066847N10"
    assert format_dictamen_id(525080, 2024, prefix="E") == "E525080N24"
    assert format_dictamen_id(6586, 2025, prefix="0E") == "0E6586N25"
    c = CGRClient()
    urls = c.build_urls(66847, 2010)
    assert urls.html_url.endswith("/066847N10/html")
    assert urls.pdf_url.endswith("/066847N10/pdf")
check("mcp-cgr-dictamenes", test_cgr)


def test_dt():
    from mcp_dt_dictamenes.dt_client import DTClient
    c = DTClient()
    url = c.build_url(128735)
    assert url.endswith("w3-article-128735.html")
    assert callable(c.discover_period_ids)
    assert callable(c.list_by_period_id)
    assert callable(c.list_all_periods)
check("mcp-dt-dictamenes", test_dt)


def test_tc():
    from mcp_tc_fallos.tc_client import TCClient
    c = TCClient()
    url = c.build_legacy_url(123)
    assert "descargar_sentencia3.php?id=123" in url
check("mcp-tc-fallos", test_tc)


def test_do():
    from mcp_diario_oficial.do_client import DiarioOficialClient
    c = DiarioOficialClient()
    assert hasattr(c, "fetch_by_date")
    assert hasattr(c, "list_today")
    assert hasattr(c, "enumerate_date_range")
check("mcp-diario-oficial", test_do)


def test_cmf():
    from mcp_cmf.cmf_client import CMFClient
    c = CMFClient()
    assert hasattr(c, "build_ncg_url") or hasattr(c, "build_url")
check("mcp-cmf", test_cmf)


def test_sernac():
    from mcp_sernac.sernac_client import SERNACClient
    c = SERNACClient()
    assert c is not None
check("mcp-sernac", test_sernac)


def test_bcch():
    # BCCh requiere credenciales BCCH_USER/BCCH_PASS — test solo módulo
    import mcp_banco_central.bcch_client as m
    assert hasattr(m, "BCChClient")
check("mcp-banco-central", test_bcch)


def test_bcn_tram():
    from mcp_bcn_tramitacion.tramitacion_client import TramitacionClient
    c = TramitacionClient()
    assert c is not None
check("mcp-bcn-tramitacion", test_bcn_tram)


def report():
    print(f"\n{'='*60}")
    print(f"{'MCP':30s} {'STATUS':>10s}")
    print(f"{'='*60}")
    ok = 0
    for name, passed, err in RESULTS:
        flag = "PASS" if passed else "FAIL"
        print(f"{name:30s} {flag:>10s}")
        if not passed:
            print(f"  {err}")
        else:
            ok += 1
    print(f"{'='*60}")
    print(f"{ok}/{len(RESULTS)} pasaron")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(report())
