import 'server-only' // garantiza que esto nunca llegue al bundle del browser

const BASE = process.env.LEGAL_API_URL ?? 'https://claude-legal-chile.vercel.app/api/corpus'
const KEY = process.env.LEGAL_API_KEY!

export type LegalHit = { path: string; score?: number; snippet?: string }

async function call(path: string, params: Record<string, string | number>) {
  const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const res = await fetch(`${BASE}${path}?${qs}`, {
    headers: { 'X-API-Key': KEY },
    next: { revalidate: 3600 }, // corpus casi estático; usa cache:'no-store' si quieres siempre fresco
  })
  if (!res.ok) throw new Error(`legal-api ${path}: ${res.status}`)
  return res.json()
}

/** Búsqueda semántica (por significado, embeddings bge-m3). */
export async function semanticLegal(q: string, limit = 10): Promise<LegalHit[]> {
  const { results } = await call('/semantic', { q, limit })
  return results
}

/** Búsqueda keyword (FTS, coincidencia exacta de palabras). */
export async function searchLegal(q: string, limit = 10, source = 'new-sources'): Promise<LegalHit[]> {
  const { results } = await call('/search', { q, limit, source })
  return results
}

/** Estado del corpus (conteos por índice + disponibilidad semántica). */
export async function legalStats() {
  return call('/stats', {})
}
