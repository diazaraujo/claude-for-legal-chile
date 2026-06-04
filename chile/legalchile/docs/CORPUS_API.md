# API del Corpus Legal Chileno — guía de uso

> **Para humanos y para IAs.** Si eres un agente/LLM integrando esta API en otro
> proyecto, este documento es autosuficiente: contiene la URL base, la autenticación,
> los endpoints, los esquemas de respuesta y ejemplos copiables. No necesitas leer el
> código del backend.

## Qué es

API HTTP de **búsqueda sobre el corpus jurídico chileno** (legislación, jurisprudencia
del Poder Judicial, dictámenes de Contraloría, doctrina, etc.). Ofrece dos modos:

- **Keyword (FTS)** — coincidencia exacta de palabras. Rápido, literal.
- **Semántica (vectorial)** — coincidencia por *significado* usando embeddings `bge-m3`.
  Encuentra documentos relevantes aunque no usen las mismas palabras de la consulta
  (ej. consultar `"despido sin causa justificada"` recupera fallos que dicen
  `"despido injustificado"`).

El motor corre en infraestructura propia (índices FTS + faiss); esta API es la
fachada estable. **Solo lectura.**

## URL base

```
https://claude-legal-chile.vercel.app/api/corpus
```

## Autenticación

Todas las llamadas requieren el header **`X-API-Key`** con una key válida.

```
X-API-Key: <TU_API_KEY>
```

- Sin key (o inválida) → **HTTP 401**.
- La key es **secreta**: guárdala en variables de entorno del servidor, **nunca** en
  código cliente / bundle de browser / repositorio.
- Cada proyecto debería usar su **propia key** (se revocan independientemente).
- ¿Necesitas una key? Pídela al responsable del corpus (se agrega a `CORPUS_API_KEYS`).

## Endpoints

### `GET /semantic` — búsqueda semántica (recomendada)

Devuelve los documentos más cercanos por significado.

| Param   | Tipo   | Default | Descripción                          |
|---------|--------|---------|--------------------------------------|
| `q`     | string | —       | Consulta en lenguaje natural (requerido) |
| `limit` | int    | 20      | Máximo de resultados (tope 100)      |

**Respuesta** `200`:
```json
{
  "query": "despido sin causa justificada",
  "mode": "semantic",
  "results": [
    { "path": "pjud/Corte_de_Apelaciones/18720234", "score": 0.6831 },
    { "path": "pjud/Laborales/12353612", "score": 0.6790 }
  ]
}
```
`score` = similitud coseno (0–1, mayor = más relevante). `path` = identificador del
documento en el corpus.

### `GET /search` — búsqueda keyword (FTS)

| Param    | Tipo   | Default        | Descripción                                  |
|----------|--------|----------------|----------------------------------------------|
| `q`      | string | —              | Términos a buscar (requerido)                |
| `limit`  | int    | 20             | Máximo de resultados (tope 100)              |
| `source` | string | `new-sources`  | Índice: `new-sources` (default) o `corpus`   |

**Respuesta** `200`:
```json
{
  "query": "despido injustificado",
  "source": "new-sources",
  "results": [
    { "path": "pjud/Laborales/9386891", "snippet": "…demanda por «despido» «injustificado»…" }
  ]
}
```
`snippet` trae los términos resaltados con `« »`.

### `GET /stats` — estado del corpus

**Respuesta** `200`:
```json
{ "indices": { "new-sources": 4904140, "corpus": 2205309 }, "semantic": true }
```
`indices` = nº de documentos por índice. `semantic` = si la búsqueda vectorial está activa.

## Errores

| Código | Significado                          |
|--------|--------------------------------------|
| 401    | Falta `X-API-Key` o es inválida      |
| 422    | Parámetro requerido ausente (ej. `q`)|
| 5xx    | Error del backend                    |

## Ejemplos

### curl
```bash
curl -H "X-API-Key: $LEGAL_API_KEY" \
  "https://claude-legal-chile.vercel.app/api/corpus/semantic?q=acoso+laboral+ambiente+hostil&limit=5"
```

### Node / fetch (server-side)
```js
const res = await fetch(
  `https://claude-legal-chile.vercel.app/api/corpus/semantic?q=${encodeURIComponent(q)}&limit=5`,
  { headers: { "X-API-Key": process.env.LEGAL_API_KEY } }
);
const { results } = await res.json();
```

### Python
```python
import os, requests
r = requests.get(
    "https://claude-legal-chile.vercel.app/api/corpus/semantic",
    params={"q": "empresa no pagó finiquito", "limit": 5},
    headers={"X-API-Key": os.environ["LEGAL_API_KEY"]},
    timeout=30,
)
r.raise_for_status()
results = r.json()["results"]
```

### Next.js (App Router)

Ver el ejemplo completo y copiable en [`../examples/nextjs/`](../examples/nextjs/).

## Notas para integradores

- **Server-to-server**: solo necesitas la key. CORS no aplica.
- **Browser directo** (un frontend de otro dominio llamando desde el navegador):
  además hay que **agregar tu origen** a la allowlist CORS del backend. Pídelo indicando
  el dominio. Recomendado: **no** llamar desde el browser; usa un proxy server-side
  (route handler / endpoint propio) para no exponer la key.
- **Caché**: el corpus es prácticamente estático; puedes cachear respuestas con
  generosidad (ej. `revalidate: 3600`).
- **Latencia**: típicamente 0,4–1,5 s; la primera consulta tras un reinicio puede tardar
  unos segundos (warm-up del índice).
