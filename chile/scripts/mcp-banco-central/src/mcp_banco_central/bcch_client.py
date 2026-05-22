"""Cliente Banco Central de Chile — Base de Datos Estadísticos (BDE).

API REST oficial:
  https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx

Requiere registro gratuito en si3.bcentral.cl. Credenciales via env:
  BCCH_USER (email)
  BCCH_PASS (password)

Funciones disponibles:
- GetSeries: data de una serie específica por código.
- SearchSeries: listado de series por frecuencia.

Series útiles para práctica legal chilena:
- UF diaria: F073.UFF.DIA.Z.Z.0.D
- Dólar observado: F073.TCO.PRE.Z.D
- TPM: F022.TPM.TIN.D001.NO.Z.D
- IPC mensual: F074.IPC.VAR.Z.Z.C.M
- UTM mensual: F073.UTR.PRE.Z.Z.0.M

Conforme a no-inventar: solo retorna valores que BCCh devuelve.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

# Series usadas frecuentemente
SERIES_COMUNES = {
    "uf_diaria": "F073.UFF.DIA.Z.Z.0.D",
    "uf_mensual": "F073.UFF.MEN.Z.Z.0.M",
    "dolar_observado": "F073.TCO.PRE.Z.D",
    "tpm": "F022.TPM.TIN.D001.NO.Z.D",
    "ipc_mensual": "F074.IPC.VAR.Z.Z.C.M",
    "utm_mensual": "F073.UTR.PRE.Z.Z.0.M",
}


@dataclass
class Observacion:
    date: str  # YYYY-MM-DD
    value: float | None


@dataclass
class SerieData:
    code: str
    titulo: str
    observaciones: list[Observacion]


class BCChClient:
    def __init__(
        self,
        user: str | None = None,
        password: str | None = None,
        rate_seconds: float = 1.0,
    ) -> None:
        self.user = user or os.environ.get("BCCH_USER", "")
        self.password = password or os.environ.get("BCCH_PASS", "")
        if not self.user or not self.password:
            raise ValueError(
                "Credenciales BCCh requeridas: setear BCCH_USER y BCCH_PASS "
                "(registro gratuito en si3.bcentral.cl)"
            )
        self.rate_seconds = rate_seconds
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        wait = self.rate_seconds - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()

    def _request(self, params: dict[str, str]) -> dict:
        params_full = {"user": self.user, "pass": self.password, **params}
        url = BASE_URL + "?" + urllib.parse.urlencode(params_full)
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
        return json.loads(body)

    def get_series(
        self, code: str, firstdate: str = "", lastdate: str = ""
    ) -> SerieData:
        """Obtiene observaciones de una serie. Fechas formato YYYY-MM-DD."""
        params: dict[str, str] = {
            "function": "GetSeries",
            "timeseries": code,
        }
        if firstdate:
            params["firstdate"] = firstdate
        if lastdate:
            params["lastdate"] = lastdate
        data = self._request(params)

        # API devuelve Series[0].Obs[] con DateTime + value
        series_list = data.get("Series", [])
        if not series_list:
            return SerieData(code=code, titulo="", observaciones=[])
        s = series_list[0]
        titulo = s.get("descripEsp", s.get("descripIng", "")) or ""
        obs_raw = s.get("Obs", [])
        observaciones = []
        for o in obs_raw:
            date = o.get("indexDateString", "")
            val_str = o.get("value", "NaN")
            try:
                value: float | None = float(val_str) if val_str != "NaN" else None
            except (TypeError, ValueError):
                value = None
            observaciones.append(Observacion(date=date, value=value))
        return SerieData(code=code, titulo=titulo, observaciones=observaciones)

    def search_series(self, frequency: str = "DAILY") -> list[dict]:
        """Lista series por frecuencia. DAILY | MONTHLY | QUARTERLY | ANNUAL."""
        if frequency not in ("DAILY", "MONTHLY", "QUARTERLY", "ANNUAL"):
            raise ValueError(
                "frequency debe ser DAILY/MONTHLY/QUARTERLY/ANNUAL"
            )
        data = self._request({
            "function": "SearchSeries",
            "frequency": frequency,
        })
        return data.get("SeriesInfos", [])

    def get_uf_hoy(self) -> Observacion | None:
        """Helper: última observación de UF diaria."""
        s = self.get_series(SERIES_COMUNES["uf_diaria"])
        return s.observaciones[-1] if s.observaciones else None

    def get_dolar_hoy(self) -> Observacion | None:
        s = self.get_series(SERIES_COMUNES["dolar_observado"])
        return s.observaciones[-1] if s.observaciones else None

    def get_tpm_hoy(self) -> Observacion | None:
        s = self.get_series(SERIES_COMUNES["tpm"])
        return s.observaciones[-1] if s.observaciones else None
