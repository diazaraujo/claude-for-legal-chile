import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import '../styles/decide.css'

type Hit = { path: string; snippet: string }

export default function Buscar() {
  const [q, setQ] = useState('')
  const [source, setSource] = useState<'new-sources' | 'corpus'>('new-sources')
  const [hits, setHits] = useState<Hit[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState('')

  async function run(e?: React.FormEvent) {
    e?.preventDefault()
    if (!q.trim()) return
    setLoading(true); setError(''); setSearched(true)
    try {
      const { data } = await api.get('/corpus/search', { params: { q, source, limit: 30 } })
      setHits(data.results || [])
    } catch {
      setError('No se pudo consultar el corpus. ¿Está corriendo el backend?')
      setHits([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="decide-root">
      <div className="topbar"><div className="wrap">
        <Link className="back" to="/">&larr; Claude Legal Chile</Link>
        <span className="tb-r">Búsqueda · Corpus jurídico</span>
      </div></div>

      <section className="hero" style={{ paddingBottom: 24 }}>
        <div className="wrap">
          <span className="section-tag">Búsqueda full-text</span>
          <h1 style={{ marginBottom: 8 }}>Busca el <em>corpus jurídico chileno</em>.</h1>
          <p className="lead" style={{ marginBottom: 20 }}>
            Full-text sobre legislación, jurisprudencia, dictámenes y registros públicos — con cita verificable, sin inventar.
          </p>
          <form onSubmit={run} style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ej.: despido injustificado, libre competencia, art. 168 código del trabajo…"
              style={{ flex: '1 1 420px', minWidth: 0, padding: '12px 16px', fontSize: 15, border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'inherit', background: '#fff', color: 'var(--ink)' }}
            />
            <select value={source} onChange={(e) => setSource(e.target.value as 'new-sources' | 'corpus')}
              style={{ padding: '12px 14px', border: '1px solid var(--line)', borderRadius: 10, background: '#fff', fontFamily: 'inherit', fontSize: 13 }}>
              <option value="new-sources">Fuentes nuevas</option>
              <option value="corpus">Corpus maestro</option>
            </select>
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Buscando…' : 'Buscar'}
            </button>
          </form>
        </div>
      </section>

      <section className="blk" style={{ paddingTop: 8 }}>
        <div className="wrap">
          {error && <div className="card" style={{ borderColor: 'var(--err)', color: '#9a3b2f' }}>{error}</div>}
          {!error && searched && !loading && (
            <div className="section-tag" style={{ marginBottom: 14 }}>{hits.length} resultado{hits.length === 1 ? '' : 's'}</div>
          )}
          <div style={{ display: 'grid', gap: 12 }}>
            {hits.map((h, i) => (
              <div className="card hov" key={i}>
                <div className="mono" style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8, wordBreak: 'break-all' }}>{h.path}</div>
                <div style={{ fontSize: 14, lineHeight: 1.55, color: 'var(--ink)' }}
                  dangerouslySetInnerHTML={{ __html: h.snippet.replace(/«/g, '<mark>').replace(/»/g, '</mark>') }} />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
