# mcp-ine — STUB

> **Estado: stub.** INE Chile no expone API REST pública estándar.
> Series clave (IPC, empleo) están disponibles via mcp-banco-central.

## Investigación 2026-05-22

- `stat.ine.cl/` es ASP.NET con endpoints `.ashx`, no REST.
- `ine.gob.cl/estadisticas/` distribuye boletines PDF mensuales (URLs CMS no-predecibles).
- API REDATAM existe pero requiere autenticación + es para censo.
- API codificación automática (CAENES, CIUO): solo para clasificación, no datos.

## Alternativa funcional

**Las series del INE más usadas en práctica legal están en BCCh BDE**:

| Indicador | Disponible en |
|---|---|
| IPC variación mensual | mcp-banco-central → `ipc_mensual` |
| Empleo nacional | BCCh tiene series F049.* |
| Tasa desempleo | BCCh series |
| Salarios mediana | INE solo, vía PDF mensual |

Para indicadores no cubiertos por BCCh, scrape de PDF mensual del INE
sería la vía — complejidad alta, ROI bajo en contexto legal.

## Si quieres implementar

1. Identificar dataset INE específico necesario.
2. Inspeccionar Network del browser en stat.ine.cl al consultar.
3. Reverse-engineer del endpoint .ashx + parámetros.
4. Construir cliente equivalente.

Diferido. Si la necesidad se concreta (ej. CASEN para alguna materia
de protección social), reabrir.
