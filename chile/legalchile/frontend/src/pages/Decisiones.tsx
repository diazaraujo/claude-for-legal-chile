import { useEffect, useMemo, useState } from 'react'
import '../styles/decide.css'
import { Footer } from './Sobre'
import ArbolDecision, { ArbolNode } from '../components/ArbolDecision'

type Bundle = { global: ArbolNode; materias: ArbolNode[]; jueces: Record<string, ArbolNode> }
type Mode = 'juez' | 'materia' | 'global'

function Header() {
  return (
    <header className="nav">
      <div className="wrap">
        <a href="/" className="brand"><b>Claude Legal Chile</b><span className="sub">· Derecho chileno real</span></a>
        <div className="spacer" />
        <nav className="navlinks">
          <a href="/jueces">Jueces</a>
          <a href="/abogados">Abogados</a>
          <a href="/fiscales">Fiscales</a>
          <a href="/tribunales">Tribunales</a>
          <a href="/decisiones" style={{ color: 'var(--primary)' }}>Decisiones</a>
          <details className="more">
            <summary>Más <span className="caret">▾</span></summary>
            <div className="more-menu">
              <a href="/empresas">Empresas demandadas</a>
              <a href="/">Inicio</a>
              <a href="/buscar">Buscar</a>
              <a href="/analisis">Análisis ↗</a>
              <a href="/sobre">¿Qué es?</a>
            </div>
          </details>
          <a className="btn btn-primary" href="mailto:antonio@unholster.com?subject=Claude%20Legal%20Chile">Contacto</a>
        </nav>
      </div>
    </header>
  )
}

export default function Decisiones() {
  const [bundle, setBundle] = useState<Bundle | null>(null)
  const [mode, setMode] = useState<Mode>('juez')
  const [q, setQ] = useState('')
  const [selKey, setSelKey] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/arbol.json').then((r) => r.json()).then((d: Bundle) => { setBundle(d); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  // lista del modo activo: [key, node]
  const list = useMemo(() => {
    if (!bundle) return [] as [string, ArbolNode][]
    if (mode === 'global') return [['__nac', bundle.global]] as [string, ArbolNode][]
    if (mode === 'materia') return bundle.materias.map((m, i) => [String(i), m] as [string, ArbolNode])
    return Object.entries(bundle.jueces).sort((a, b) => b[1].n - a[1].n)
  }, [bundle, mode])

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase()
    return (s ? list.filter(([, n]) => n.label.toLowerCase().includes(s)) : list).slice(0, 150)
  }, [list, q])

  // selección efectiva
  const selected = useMemo(() => {
    if (!filtered.length) return null
    const hit = filtered.find(([k]) => k === selKey)
    return (hit || filtered[0])[1]
  }, [filtered, selKey])

  const switchMode = (m: Mode) => { setMode(m); setQ(''); setSelKey('') }

  return (
    <div className="decide-root">
      <Header />
      <section className="hero" style={{ paddingBottom: 12 }}>
        <div className="wrap">
          <div className="toprow">
            <span className="section-tag">Decisiones · Rayos X de la justicia</span>
            <span className="status"><span className="dot" /> 592.900 sentencias penales</span>
          </div>
          <h1>Cómo se decide una causa penal</h1>
          <p className="lead">El árbol de decisión: probabilidad de condena o absolución y —cuando condena— el grado de pena y si se cumple efectiva o sustituida (Ley 18.216). Por juez, por materia o a nivel nacional, medido sobre las sentencias penales públicas.</p>
        </div>
      </section>

      <section className="blk" style={{ paddingTop: 6 }}>
        <div className="wrap">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 14 }}>
            {([['juez', 'Por juez'], ['materia', 'Por materia'], ['global', 'Nacional']] as [Mode, string][]).map(([m, lbl]) => (
              <button key={m} onClick={() => switchMode(m)}
                style={{ cursor: 'pointer', padding: '8px 18px', fontWeight: 600, fontSize: 13, borderRadius: 8, border: mode === m ? '1px solid #266FE0' : '1px solid var(--line)', background: mode === m ? '#266FE0' : '#fff', color: mode === m ? '#fff' : 'var(--ink)' }}>
                {lbl}
              </button>
            ))}
            {mode !== 'global' && (
              <form className="searchbox" style={{ flex: '1 1 240px', margin: 0 }} onSubmit={(e) => e.preventDefault()}>
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={mode === 'juez' ? 'Buscar juez por nombre…' : 'Buscar materia…'} autoComplete="off" />
              </form>
            )}
          </div>

          {loading ? (
            <p className="mono" style={{ color: 'var(--muted)', fontSize: 12 }}>Cargando…</p>
          ) : !bundle ? (
            <p className="mono" style={{ color: 'var(--muted)', fontSize: 12 }}>No se pudo cargar el árbol de decisiones.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: mode === 'global' ? '1fr' : '300px 1fr', gap: 22, alignItems: 'start' }} className="dec-grid">
              {mode !== 'global' && (
                <div>
                  <div className="section-tag uline">{q ? `${filtered.length} resultados` : mode === 'juez' ? `Top ${filtered.length} jueces por volumen` : `${filtered.length} materias`}</div>
                  <div className="exp-list" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 6, maxHeight: 640, overflowY: 'auto' }}>
                    {filtered.map(([k, n]) => {
                      const isSel = selected && n.label === selected.label
                      return (
                        <button key={k} onClick={() => setSelKey(k)} className="card"
                          style={{ textAlign: 'left', cursor: 'pointer', padding: '10px 14px', border: isSel ? '1px solid var(--primary)' : '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', textTransform: mode === 'materia' ? 'capitalize' : 'none' }}>{mode === 'materia' ? n.label.toLowerCase() : n.label}</span>
                          <span className="mono" style={{ fontSize: 11, color: 'var(--muted)', flex: 'none' }}>{n.n.toLocaleString('es-CL')}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
              <div className="card" style={{ padding: '18px 20px' }}>
                <div className="section-tag">{mode === 'global' ? 'Nacional · todo penal' : mode === 'juez' ? 'Juez' : 'Materia'}</div>
                <h2 style={{ fontSize: 20, fontWeight: 600, margin: '2px 0 14px', textTransform: mode === 'materia' ? 'capitalize' : 'none' }}>
                  {selected ? (mode === 'materia' ? selected.label.toLowerCase() : selected.label) : '—'}
                </h2>
                {selected && <ArbolDecision node={selected} mode={mode} />}
              </div>
            </div>
          )}
          <p className="mono" style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '0.08em', marginTop: 18, textTransform: 'uppercase' }}>Decisión: campo estructurado de cada sentencia · Pena y cumplimiento: extracción del texto · No incluye sobreseimiento (corpus selectivo de sentencias definitivas)</p>
        </div>
      </section>
      <Footer />
    </div>
  )
}
