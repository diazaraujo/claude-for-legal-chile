# Consumir el Corpus Legal Chileno desde Next.js (App Router)

Ejemplo mínimo y copiable. La API key se mantiene **server-side**. Spec completa de la
API en [`../../docs/CORPUS_API.md`](../../docs/CORPUS_API.md).

## 1. Configura el entorno

Copia `.env.example` a `.env.local` y pon tu key:

```bash
LEGAL_API_URL=https://claude-legal-chile.vercel.app/api/corpus
LEGAL_API_KEY=lck_...   # secreto, nunca NEXT_PUBLIC_
```

## 2. Copia el cliente

`lib/legal.ts` ya está acá. Expone `semanticLegal()`, `searchLegal()`, `legalStats()`.

## 3a. Úsalo en un Server Component

```tsx
// app/buscar/page.tsx
import { semanticLegal } from '@/lib/legal'

export default async function Page({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams
  const hits = q ? await semanticLegal(q, 10) : []
  return (
    <ul>
      {hits.map((h) => (
        <li key={h.path}>{h.path} — {h.score?.toFixed(3)}</li>
      ))}
    </ul>
  )
}
```

## 3b. Desde un Client Component → usa un Route Handler (la key no sale del servidor)

```ts
// app/api/legal/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { semanticLegal } from '@/lib/legal'

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q') ?? ''
  if (!q) return NextResponse.json({ results: [] })
  return NextResponse.json({ results: await semanticLegal(q, 10) })
}
```

El componente cliente llama `fetch('/api/legal?q=...')`; la `LEGAL_API_KEY` jamás llega al browser.

## Reglas

- **Nunca** uses `NEXT_PUBLIC_` para la key → la metería al bundle del browser.
- Server-to-server (patrones de arriba): solo la key, sin CORS.
- Si necesitas llamar la API **directo desde el browser** de otro dominio, hay que abrir
  el CORS de ese origen en el backend — pídelo. Preferible el patrón 3b.
