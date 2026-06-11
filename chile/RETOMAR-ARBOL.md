# RETOMAR — Árbol normativo: activación del backend + frontend (2026-06-10 noche)

Todo construido y testeado en modo autónomo; **falta solo aplicar a producción** (bloqueado
por permisos: código nuevo en backend prod + secretos). Secuencia completa para Antonio:

## 1. Aplicar backend (código ya staged en enigma `/tmp/corpus-code/`)

```bash
ssh antonio@10.0.0.3 'cp /tmp/corpus-code/arbol.py /tmp/corpus-code/api.py \
  /mnt/data/legal-chile/app/backend/apps/corpus/ && docker restart app-backend-1'
```

Endpoints nuevos (mismo auth X-API-Key):
- `GET /api/corpus/arbol/normas?q=&limit=` — normas por nº de sentencias
- `GET /api/corpus/arbol/norma/{id}` — artículos con conteos
- `GET /api/corpus/arbol/norma/{id}/articulo?art=` — serie temporal + tesis + ejemplos
- `GET /api/corpus/considerandos/semantic?q=` — semántica granular (faiss 5,16M, mmap)
- `/stats` ahora reporta `"arbol": true`

Datos ya en su lugar (`/home/antonio/lc-index/`): `citas_normativas.sqlite3` (con
`arbol_mat`/`arbol_temporal_mat` materializadas e indexadas), `considerandos.ivf.faiss` (20GB),
`considerandos.ids.npy`, `tesis/*.npz` (18.190), `tesis/labels.json` (TF-IDF) y
`tesis/labels-llm.jsonl` (qwen2.5:14b, creciendo overnight — el backend lo relee por mtime).

Smoke: `curl -H "X-API-Key: $KEY" localhost:8090/api/corpus/arbol/normas?q=trabajo` →
debe traer CdT con ~1.037 artículos (validado localmente contra las mismas DBs).

## 2. Frontend con API key (resuelve además el blocker de /buscar)

```bash
ssh antonio@10.0.0.3 'docker exec app-backend-1 printenv CORPUS_API_KEYS'   # tomar la lck_fe_…
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile/legalchile/frontend" && \
  VITE_API_KEY=lck_fe_PEGAR_AQUI npx vite build && cp vercel.json dist/ && \
  cd dist && npx vercel deploy --prod --yes
```

Página nueva: **`/arbol`** (Arbol.tsx, look decide.css): buscador de normas → grilla de
artículos → detalle con barras por año (con caveat de densidad del corpus en el copy) +
tarjetas de tesis (nombre LLM > términos TF-IDF > fallback) + 3 sentencias de ejemplo
con fecha/tribunal/rol. Ruta agregada en App.tsx.

## 3. Verificación post-deploy (gates de costumbre)

- Semáforo TTFB: `/`, `/buscar`, `/analisis`, `/arbol` (verde ≤1.5s).
- Smoke funcional: en `/arbol` buscar "trabajo" → CdT → art. 162 → deben aparecer tesis
  con nombres tipo "Nulidad por falta de cotizaciones" y la serie 2005-2026.
- `/buscar` debe dejar de dar 401 (key horneada).

## Pendientes que siguen su curso solos
- Etiquetado LLM overnight (qwen2.5:14b, 18.190 artículos) — monitor avisa; el backend lo
  sirve incrementalmente sin redeploy (relee el JSONL).
- BCN: 21.065 normas (pausado, intento IP casa — ver RETOMAR-BCN.md).
