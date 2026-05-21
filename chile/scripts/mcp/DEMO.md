# Demo `mcp-bcn-leychile` — queries reales contra catálogo + grafo

Catálogo actual: **17.817 normas** indexadas + grafo de relaciones BCN
(en construcción, 40k+ edges al momento de esta demo).

## 1. Stats globales

```bash
$ mcp-bcn-cli stats
```
```json
{
  "total_normas": 17817,
  "by_tipo": {
    "ley": 5273,    "dl": 3656,    "dfl": 530,
    "cer": 2952,    "acd": 2653,   "avi": 1008,
    "cir": 791,     "aa": 533,     "tra": 167,
    "cod": 19,      "bando": 71,   "cci": 143,
    "alc": 16
  }
}
```

## 2. Lookup directo

```bash
$ mcp-bcn-cli lookup --tipo ley --numero 21643
```
```json
{
  "found": true,
  "slug": "ley-21643-acoso-laboral",
  "titulo": "Ley Karin — acoso laboral, sexual y violencia en el trabajo",
  "publicacion": "2024-01-15",
  "leychile_code": "1200096",
  "fuente_oficial": "https://www.bcn.cl/leychile/navegar?idNorma=1200096",
  "capa": 3,
  "md_path": "chile/normativa/leyes/ley-21643-acoso-laboral.md"
}
```

→ Encuentra el perfil curado capa 3 (no solo el catálogo).

## 3. Búsqueda por título

```bash
$ mcp-bcn-cli search "género"
```
```json
[{
  "slug": "ley-21120-identidad-genero",
  "tipo": "ley", "numero": "21120",
  "titulo": "Reconoce y da protección al derecho a la identidad de género",
  "capa": 3
}]
```

```bash
$ mcp-bcn-cli search "laboral" --limit 5
```
Top resultados, todos capa 3:
- Ley 21643 (Karin — acoso laboral)
- Ley 21561 (reducción jornada)
- Ley 21015 (inclusión personas con discapacidad)
- Ley 20940 (moderniza relaciones laborales)
- Ley 20087 (procedimiento laboral)

## 4. Hubs del grafo — normas centrales

¿Qué normas modifican más otras normas?

```bash
$ mcp-bcn-cli hubs --rel modifiesTo --top 5
```
```json
[
  {"uri": ".../dfl/ministerio-de-hacienda/1982-08-07/28", "count": 528},
  {"uri": ".../avi/ministerio-de-obras-publicas_fiscalia/2011-12-15/s-n", "count": 190},
  {"uri": ".../dto/ministerio-de-agricultura/1989-03-06/169", "count": 188}
]
```

→ **DFL 28/1982 (Hacienda)** modifica 528 normas — un hub fundamental
del orden financiero chileno. Ayuda a entender la estructura del
ordenamiento sin leer norma por norma.

## 5. Relaciones de una norma — caso real Ley 19628 (Protección Datos)

```bash
$ mcp-bcn-cli lookup --tipo ley --numero 19628
```
→ devuelve `bcn_uri: http://datos.bcn.cl/recurso/cl/ley/ministerio-secretaria-general-de-la-presidencia/1999-08-28/19628`

```bash
$ mcp-bcn-cli relaciones <bcn_uri> --direction outgoing
```
→ Ley 19628 **modifica** DFL 725/1968 (Código Sanitario) — la LPD retocó
el código sanitario en su promulgación (1999).

```bash
$ mcp-bcn-cli relaciones <bcn_uri> --direction incoming
```
→ Ley 19628 **es modificada por 8 normas**:
- Ley 19812/2002 (SEGPRES)
- Varias leyes del Ministerio de Economía y Empresas Menor — incluye
  Ley 21719/2024 (Reforma LPD).

Esto reemplaza lecturas manuales de "¿qué leyes modifican el régimen de
protección de datos?" con un query <50ms.

## Valor para Claude

Cuando Claude responde una consulta legal chilena:

1. **Antes:** cita normas posiblemente alucinadas o de España/México.
2. **Con este MCP:**
   - Llama `lookup_norma` → resuelve el slug + URL oficial real.
   - Llama `search_normas` → encuentra el catálogo curado.
   - Llama `get_relaciones` → entiende qué modifica/deroga qué.
   - Llama `bcn_get_norma` (remoto) → solo si necesita texto integral.

Latencia local <50ms. Sin alucinación. Trazabilidad al BCN oficial.
