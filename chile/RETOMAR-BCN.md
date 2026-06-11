# RETOMAR — descarga BCN/leychile (pausada 2026-06-10 ~20:45 CLT)

**Pausada a pedido de Antonio** (va a intentar bajar desde la IP de su casa). Los scrapers
están detenidos; `embed-loop.sh` y `bcn-monitor-faiss.sh` siguen corriendo (embeben lo que
caiga y gatillan el rebuild faiss al llegar a 0 — no estorban la descarga desde otra IP).

## Estado al pausar

| métrica | valor |
|---|---|
| descargadas (`downloaded=1`) | **148.071** |
| pendientes (`status IS NULL`) | **21.065** |
| universo manifest | 169.861 (incluye CPR 242302 agregada 10-jun) |
| terminales | err=123 · stub=599+ · skip=40 · http421=2 |

Manifest: `data/leychile/manifest.sqlite3` (tabla `normas`). XMLs en `data/leychile/<tipo>/<id>.xml`.

## Qué falta por hacer

1. **Bajar las 21.065 pendientes** (`SELECT id_norma, tipo FROM normas WHERE downloaded=0 AND status IS NULL`).
   - URL: `https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma=<id>` → respuesta válida empieza con `<Norma`.
   - Respuesta **vacía** = WAF empty-wall, NO norma muerta (ver guards abajo). 429 = throttle per-IP.
   - Desde IP casa: `scripts/bulk-downloaders/leychile-direct.py` (ASC, marca vacías como stub —
     revisar guard) o el canal Zyte `leychile-pending-fast.py` (12 geos, ya con guards).
2. **Al llegar a pend≈0**: `bcn-monitor-faiss.sh` (ya corriendo en el Mac) espera el catch-up del
   embed-loop, rsync-ea `new-sources.fts` a enigma y reconstruye el faiss (swap atómico). Solo
   queda el reload del backend (eyes-on): `ssh antonio@10.0.0.3 'docker restart app-backend-1'`.
3. **CPR (id 242302)**: agregada al manifest el 10-jun (texto refundido DTO-100/2005, verificada
   contra BCN). Debe bajar con el resto — es la norma más citada del árbol normativo (185k citas).

## Cómo relanzar los wrappers gateados (si se vuelve al modo automático)

```bash
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
nohup ./scripts/bulk-downloaders/leychile-gated-now.sh        > /tmp/lc-leychile-gated.log  2>&1 &  # Zyte
nohup ./scripts/bulk-downloaders/leychile-direct-gated-now.sh > /tmp/lc-leychile-direct.log 2>&1 &  # IP directa
```
Variantes `*-now.sh` = sin gate de reloj (corren 24/7), solo gate por **probe honesto**
(norma PENDIENTE aleatoria — la 1044382 está cacheada en CDN y da falso verde).

## Guards anti-falso-ban (aprendizajes 10-jun, ya implementados en `leychile-pending-fast.py`)

- El WAF en peak responde **200-vacío a todo** → antes se marcaban `ban` terminales masivos.
  Ahora: solo marca `ban` si la pasada ya tuvo ≥1 ok real; y **aborta (rc=3) tras 100 normas
  sin un solo ok** (pasada estéril, no quemar Zyte). El wrapper pausa 20 min tras abort.
- Recuperar falsos bans: `UPDATE normas SET status=NULL, downloaded=0 WHERE status='ban';`
- Ritmo observado 10-jun: peak = goteo/walled · 19:00+ CLT = ventana real (+1.200/30min, ~2.400/h).

## Contexto río abajo (por qué importa terminar)

Las normas faltantes alimentan: corpus `/buscar` (FTS+semántica), el **árbol normativo de
interpretaciones** (`data/_index/citas_normativas.sqlite3` — 4,39M citas ya resueltas contra
los títulos descargados) y la cobertura "corpus legal Chile = 100%". Ver memoria del proyecto
y `scripts/extract-citas-normativas.py` / `resolve-citas-normativas.py` / `build-sentencias-fechas.py`.
