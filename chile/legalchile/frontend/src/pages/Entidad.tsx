import { useEffect, useMemo, useState } from 'react'
import '../styles/decide.css'
import { Footer } from './Sobre'

type Mat = [string, number]
type Row = {
  key: string; nombre: string; n: number; comp?: string; trib?: string; years?: string
  lab_n?: number; lab_acogida?: number | null; pen_n?: number; pen_condena?: number | null; pen_dias?: number | null
  nres?: number; condena?: number | null; rechazo?: number | null; concil?: number | null; pct_acept?: number | null; monto?: number
  materias?: Mat[]; defensas?: Mat[]; contrapartes?: Mat[]; delitos?: Mat[]
  bio?: string; patrimonio?: Patrimonio
}

const pct = (x?: number | null) => (x == null ? '—' : `${Math.round(x * 100)}%`)
const money = (n?: number) => (!n ? '—' : '$' + (n >= 1e9 ? (n / 1e9).toFixed(1) + ' B' : n >= 1e6 ? (n / 1e6).toFixed(0) + ' M' : n.toLocaleString('es-CL')))

const CFG: Record<string, { file: string; tag: string; h1: string; sub: string; intro: string }> = {
  jueces: { file: '/data/jueces.json', tag: 'Jueces', h1: 'La ficha de cada juez, leída de sus fallos', sub: 'jueces con ficha', intro: 'Materias que más resuelve, tasa de acogida laboral, tasa de condena penal y pena promedio — la tendencia histórica de cada juez, medida sobre sus sentencias públicas.' },
  abogados: { file: '/data/abogados.json', tag: 'Abogados', h1: 'Cómo litiga cada abogado, a partir de sus causas', sub: 'abogados perfilados', intro: 'Volumen de causas, competencias, materias y las partes/empresas que aparecen en sus causas — el historial litigioso real de cada abogado patrocinante, leído de las sentencias públicas. El rol no distingue siempre a qué parte representa; mostramos las contrapartes presentes en sus causas.' },
  fiscales: { file: '/data/fiscales.json', tag: 'Fiscales', h1: 'El comportamiento de cada fiscal, medido', sub: 'fiscales perfilados', intro: 'Tasa de condena obtenida, delitos perseguidos y volumen de causas de cada fiscal del Ministerio Público, construido sobre las sentencias penales públicas.' },
  empresas: { file: '/data/empresas.json', tag: 'Empresas demandadas', h1: 'Cómo litiga cada empresa, a partir de sus causas', sub: 'empresas demandadas perfiladas', intro: 'Historial litigioso de cada empresa demandada en lo laboral — cuánto resuelve por condena, cuánto por conciliación, qué materias enfrenta, con qué defensas y qué montos. Son las partes empleadoras, no sus abogados.' },
  tribunales: { file: '/data/tribunales.json', tag: 'Tribunales', h1: 'El perfil de cada tribunal y juzgado', sub: 'tribunales con perfil', intro: 'Volumen de causas, tasa de resultados y competencias de cada juzgado del país, construido sobre las sentencias públicas.' },
}

function Bars({ items, color }: { items: Mat[]; color: string }) {
  const max = Math.max(1, ...items.map((m) => m[1]))
  return (
    <div style={{ marginTop: 4 }}>
      {items.map(([k, v]) => (
        <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '6px 0' }}>
          <span style={{ width: 180, flex: 'none', fontSize: 12.5, color: 'var(--muted)', fontWeight: 300, textTransform: 'capitalize', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{k}</span>
          <div style={{ flex: 1, background: 'var(--bg)', borderRadius: 5, height: 16, overflow: 'hidden' }}>
            <div style={{ width: `${(v / max) * 100}%`, height: '100%', background: color, borderRadius: 5 }} />
          </div>
          <span style={{ width: 36, textAlign: 'right', fontWeight: 600, fontSize: 12.5, fontVariantNumeric: 'tabular-nums' }}>{v}</span>
        </div>
      ))}
    </div>
  )
}

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value sm">{value}</div>
      {sub && <div className="mono" style={{ fontSize: 10, color: 'var(--muted)', marginTop: 5 }}>{sub}</div>}
    </div>
  )
}

// ---- Patrimonio declarado (Ley 20.880 · InfoProbidad) + reseña IA · público ----
type HistPt = { fecha: string; inm: number; av_inm: number; veh: number; av_veh: number; pas: number }
type Tendencia = { dir: 'up' | 'down' | 'flat' | 'na'; ratio?: number | null; desde: string; hasta: string; peak: number; actual: number }
type Patrimonio = {
  fecha?: string | null; cargo?: string | null
  n_inmuebles?: number; avaluo_inmuebles?: number
  n_vehiculos?: number; avaluo_vehiculos?: number; n_pasivos?: number
  hist?: HistPt[]; tendencia?: Tendencia
}
const clp = (n?: number | null) => (!n ? '—' : '$' + Number(n).toLocaleString('es-CL'))

function JuezPerfil({ r }: { r: Row }) {
  const p = r.patrimonio
  if (!p && !r.bio) return null
  return (
    <div className="card" style={{ marginBottom: 22, borderColor: 'var(--primary)' }}>
      {p && <>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
          <div className="section-tag">Patrimonio declarado · Ley 20.880</div>
          {p.fecha && <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>Declaración {p.fecha}{p.cargo ? ` · ${p.cargo}` : ''}</span>}
        </div>
        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginTop: 8 }}>
          <Kpi label="Bienes raíces" value={String(p.n_inmuebles ?? 0)} sub={p.avaluo_inmuebles ? `avalúo ${clp(p.avaluo_inmuebles)}` : undefined} />
          <Kpi label="Vehículos" value={String(p.n_vehiculos ?? 0)} sub={p.avaluo_vehiculos ? `avalúo ${clp(p.avaluo_vehiculos)}` : undefined} />
          <Kpi label="Deudas declaradas" value={p.n_pasivos != null ? String(p.n_pasivos) : '—'} />
        </div>
        {p.tendencia && p.tendencia.dir !== 'na' && (() => {
          const t = p.tendencia
          const col = t.dir === 'up' ? '#0a7d3c' : t.dir === 'down' ? '#b42318' : 'var(--muted)'
          const lbl = t.dir === 'up' ? 'Al alza' : t.dir === 'down' ? 'A la baja' : 'Estable'
          return (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <span className="section-tag" style={{ margin: 0 }}>Tendencia del patrimonio</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: col }}>{lbl}{t.ratio ? ` · ×${t.ratio}` : ''}</span>
              <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>{t.desde}→{t.hasta} · máx {clp(t.peak)}</span>
            </div>
          )
        })()}
        {p.hist && p.hist.length > 1 && (() => {
          const pts = p.hist.map((h) => ({ ...h, total: (h.av_inm || 0) + (h.av_veh || 0) }))
          const mx = Math.max(...pts.map((x) => x.total), 1)
          return (
            <>
              <div className="section-tag uline" style={{ marginTop: 20, display: 'block' }}>Evolución del patrimonio declarado · {pts.length} declaraciones</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3, marginTop: 8 }}>
                {pts.map((h, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="mono" style={{ fontSize: 10, color: 'var(--muted)', width: 66, flexShrink: 0 }}>{h.fecha}</span>
                    <div style={{ flex: 1, background: 'var(--line)', borderRadius: 4, height: 13 }}>
                      <div style={{ width: `${Math.max(2, (100 * h.total) / mx)}%`, background: 'var(--primary)', height: '100%', borderRadius: 4 }} />
                    </div>
                    <span className="mono" style={{ fontSize: 10, color: 'var(--ink)', width: 96, flexShrink: 0, textAlign: 'right' }}>{clp(h.total)}</span>
                    <span className="mono" style={{ fontSize: 9.5, color: 'var(--muted)', width: 78, flexShrink: 0 }}>{h.inm} b.raíces · {h.veh} veh</span>
                  </div>
                ))}
              </div>
            </>
          )
        })()}
      </>}
      {r.bio && (
        <>
          <div className="section-tag uline" style={{ marginTop: p ? 20 : 0, display: 'block' }}>Reseña</div>
          <p style={{ fontSize: 14, color: 'var(--ink)', fontWeight: 300, lineHeight: 1.55, marginTop: 6 }}>{r.bio}</p>
        </>
      )}
      <p className="mono" style={{ fontSize: 9.5, color: 'var(--muted)', marginTop: 16, letterSpacing: '0.06em' }}>
        Reseña generada con IA sobre las sentencias públicas del juez.{p ? ' Patrimonio según la Declaración de Intereses y Patrimonio (Ley 20.880), publicada en InfoProbidad.' : ''}
      </p>
    </div>
  )
}

function Ficha({ tipo, r }: { tipo: string; r: Row }) {
  let kpis: { label: string; value: string; sub?: string }[]
  if (tipo === 'empresas') kpis = [
    { label: 'Juicios', value: r.n.toLocaleString('es-CL') },
    { label: 'Tasa de condena (en su contra)', value: pct(r.condena), sub: `${r.nres ?? 0} con resultado` },
    { label: 'Resuelto por conciliación', value: pct(r.concil) },
    { label: 'Monto acogido total', value: money(r.monto) },
  ]
  else if (tipo === 'abogados') kpis = [
    { label: 'Causas', value: r.n.toLocaleString('es-CL') },
    { label: 'Competencia principal', value: (r.comp || '—').replace(/_/g, ' ') },
    { label: 'Período', value: r.years || '—' },
  ]
  else if (tipo === 'fiscales') kpis = [
    { label: 'Causas penales', value: r.n.toLocaleString('es-CL') },
    { label: 'Tasa de condena obtenida', value: pct(r.condena), sub: r.nres ? `${r.nres.toLocaleString('es-CL')} con resultado` : 'sin resultado extraído aún' },
    { label: 'Período', value: r.years || '—' },
  ]
  else kpis = [
    { label: 'Causas', value: r.n.toLocaleString('es-CL') },
    { label: 'Acogida laboral', value: pct(r.lab_acogida), sub: r.lab_n ? `${r.lab_n.toLocaleString('es-CL')} laborales` : 'sin causas laborales' },
    { label: 'Condena penal', value: pct(r.pen_condena), sub: r.pen_n ? `${r.pen_n.toLocaleString('es-CL')} penales` : 'sin causas penales' },
    { label: 'Pena promedio', value: r.pen_dias ? `${Math.round(r.pen_dias)} días` : '—' },
  ]
  // gráficos por tipo
  const charts: { label: string; items?: Mat[]; color: string }[] = []
  if (tipo === 'fiscales') charts.push({ label: 'Delitos más perseguidos', items: r.delitos, color: 'var(--blue-dark)' })
  else charts.push({ label: 'Materias más frecuentes', items: r.materias, color: 'var(--primary)' })
  if (tipo === 'empresas') charts.push({ label: 'Defensas más usadas', items: r.defensas, color: 'var(--cyan)' })
  if (tipo === 'abogados') charts.push({ label: 'Partes / empresas en sus causas', items: r.contrapartes, color: 'var(--cyan)' })
  const shown = charts.filter((c) => c.items && c.items.length)
  return (
    <div className="card" style={{ marginBottom: 22 }}>
      <div className="section-tag">{CFG[tipo].tag} · ficha</div>
      <h2 style={{ fontSize: 22, fontWeight: 600, margin: '4px 0 4px' }}>{r.nombre}</h2>
      {(r.trib || r.comp) && <div className="mono" style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 16 }}>{(r.trib || r.comp || '').replace(/_/g, ' ')}</div>}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
        {kpis.map((k) => <Kpi key={k.label} {...k} />)}
      </div>
      {shown.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: shown.length > 1 ? '1fr 1fr' : '1fr', gap: 24, marginTop: 20 }} className="ficha-charts">
          {shown.map((c) => (
            <div key={c.label}>
              <div className="kpi-label">{c.label}</div>
              <Bars items={c.items as Mat[]} color={c.color} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function rowStat(tipo: string, r: Row) {
  if (tipo === 'fiscales') return `${r.n.toLocaleString('es-CL')} causas${r.condena != null ? ` · ${pct(r.condena)} condena` : ''}`
  if (tipo === 'abogados') return `${r.n.toLocaleString('es-CL')} causas${r.comp ? ` · ${r.comp.replace(/_/g, ' ')}` : ''}`
  if (tipo === 'empresas') return `${r.n.toLocaleString('es-CL')} causas${r.condena != null ? ` · ${pct(r.condena)} condena` : ''}`
  return `${r.n.toLocaleString('es-CL')} causas${r.pen_condena != null ? ` · ${pct(r.pen_condena)} condena` : ''}${r.lab_acogida != null ? ` · ${pct(r.lab_acogida)} acogida` : ''}`
}

function Header({ tipo }: { tipo: string }) {
  const on = (t: string) => (tipo === t ? { color: 'var(--primary)' } : undefined)
  return (
    <header className="nav">
      <div className="wrap">
        <a href="/" className="brand"><b>Claude Legal Chile</b><span className="sub">· Derecho chileno real</span></a>
        <div className="spacer" />
        <nav className="navlinks">
          <a href="/jueces" style={on('jueces')}>Jueces</a>
          <a href="/abogados" style={on('abogados')}>Abogados</a>
          <a href="/fiscales" style={on('fiscales')}>Fiscales</a>
          <a href="/tribunales" style={on('tribunales')}>Tribunales</a>
          <details className="more">
            <summary>Más <span className="caret">▾</span></summary>
            <div className="more-menu">
              <a href="/empresas" style={on('empresas')}>Empresas demandadas</a>
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

export default function Entidad({ tipo }: { tipo: string }) {
  const cfg = CFG[tipo]
  const [data, setData] = useState<Row[]>([])
  const [q, setQ] = useState('')
  const [sel, setSel] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true); setSel(null); setQ('')
    fetch(cfg.file).then((r) => r.json()).then((d: Row[]) => { setData(d); setSel(d[0] ?? null); setLoading(false) }).catch(() => setLoading(false))
  }, [cfg.file])

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase()
    return (s ? data.filter((d) => d.nombre.toLowerCase().includes(s)) : data).slice(0, 150)
  }, [data, q])

  return (
    <div className="decide-root">
      <Header tipo={tipo} />
      <section className="hero" style={{ paddingBottom: 12 }}>
        <div className="wrap">
          <div className="toprow">
            <span className="section-tag">{cfg.tag} · Rayos X de la justicia</span>
            <span className="status"><span className="dot" /> {data.length.toLocaleString('es-CL')} {cfg.sub} · muestra en aumento</span>
          </div>
          <h1>{cfg.h1}</h1>
          <p className="lead">{cfg.intro}</p>
          <form className="searchbox" onSubmit={(e) => e.preventDefault()}>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Buscar ${cfg.tag.toLowerCase()} por nombre…`} autoComplete="off" />
          </form>
        </div>
      </section>

      <section className="blk" style={{ paddingTop: 10 }}>
        <div className="wrap">
          {loading ? (
            <p className="mono" style={{ color: 'var(--muted)', fontSize: 12 }}>Cargando fichas…</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 24 }}>
              {sel && <div><Ficha tipo={tipo} r={sel} />{tipo === 'jueces' && <JuezPerfil r={sel} />}</div>}
              <div>
                <div className="section-tag uline">{q ? `${filtered.length} resultados` : `Top ${filtered.length} por volumen de causas`}</div>
                <div className="exp-list" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 6, maxHeight: 560, overflowY: 'auto' }}>
                  {filtered.map((r) => (
                    <button key={r.key} onClick={() => { setSel(r); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                      className="card" style={{ textAlign: 'left', cursor: 'pointer', padding: '12px 16px', border: sel?.key === r.key ? '1px solid var(--primary)' : '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.nombre}</span>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--muted)', flex: 'none' }}>{rowStat(tipo, r)}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          <p className="mono" style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '0.08em', marginTop: 18, textTransform: 'uppercase' }}>Datos extraídos de sentencias públicas · muestra en aumento mientras corre la extracción · las tasas y materias son sobre las causas ya procesadas</p>
        </div>
      </section>
      <Footer />
    </div>
  )
}
