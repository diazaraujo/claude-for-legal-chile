# mcp-banco-central

MCP server para la **Base de Datos Estadísticos (BDE)** del Banco
Central de Chile.

## Registro

Requiere cuenta gratuita en [si3.bcentral.cl](https://si3.bcentral.cl/).
Después de registrarse, setear credenciales en environment:

```bash
export BCCH_USER="tu-email@example.com"
export BCCH_PASS="tu-password"
```

Para usar dentro de Claude Code:

```bash
claude mcp add banco-central \
  -e BCCH_USER=tu-email -e BCCH_PASS=tu-pass \
  /path/al/binario/mcp-banco-central
```

## Series útiles para práctica legal

| Alias | Código BCCh | Uso típico |
|---|---|---|
| `uf_diaria` | F073.UFF.DIA.Z.Z.0.D | Contratos UF, reajustes |
| `uf_mensual` | F073.UFF.MEN.Z.Z.0.M | Promedios mensuales |
| `dolar_observado` | F073.TCO.PRE.Z.D | Conversión USD/CLP |
| `tpm` | F022.TPM.TIN.D001.NO.Z.D | Intereses, mora |
| `ipc_mensual` | F074.IPC.VAR.Z.Z.C.M | Reajuste pensiones alimentos |
| `utm_mensual` | F073.UTR.PRE.Z.Z.0.M | Tabla impuestos, multas |

## Tools

- `bcch_get_series(code, firstdate?, lastdate?)`: serie completa
- `bcch_uf_hoy()`: última UF
- `bcch_dolar_hoy()`: último dólar observado
- `bcch_tpm_hoy()`: TPM vigente
- `bcch_search_series(frequency)`: lista series por frecuencia

## Estado

✅ Funcional. Requiere credenciales BCCH (no proporciona usuario default).
