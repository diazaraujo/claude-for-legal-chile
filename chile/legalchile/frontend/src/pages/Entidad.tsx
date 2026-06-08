import { useEffect, useMemo, useState } from 'react'
import '../styles/decide.css'
import { Footer } from './Sobre'

type Mat = [string, number, (number | null)?, (string | null)?]
type Row = {
  key: string; nombre: string; n: number; comp?: string; trib?: string; years?: string
  lab_n?: number; lab_acogida?: number | null; pen_n?: number; pen_condena?: number | null; pen_dias?: number | null
  nres?: number; condena?: number | null; rechazo?: number | null; concil?: number | null; pct_acept?: number | null; monto?: number
  materias?: Mat[]; defensas?: Mat[]; contrapartes?: Mat[]; delitos?: Mat[]
  bio?: string; patrimonio?: Patrimonio; defensor?: Defensor; linkedin?: LinkedIn
}
type Defensor = { pub_n: number; pub_rate?: number | null; priv_n: number; priv_rate?: number | null }
type LinkedIn = { url?: string; job?: string; company?: string; headline?: string; edu?: { school?: string; deg?: string | null; field?: string | null }[] }

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
    <div style={{ marginTop: 6 }}>
      {items.map(([k, v, tasa, tipo]) => {
        const lbl = tipo === 'c' ? 'condena' : tipo === 'a' ? 'acogida' : ''
        return (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '7px 0' }}>
            <span style={{ width: 132, flex: 'none', fontSize: 12, color: 'var(--ink)', fontWeight: 300, textTransform: 'capitalize', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{k}</span>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
              <div style={{ width: `${Math.max(3, (v / max) * 100)}%`, minWidth: 4, height: 9, background: color, borderRadius: 4 }} />
            </div>
            {tasa != null && <span style={{ width: 90, flex: 'none', textAlign: 'right', fontSize: 11, color: 'var(--muted)', fontVariantNumeric: 'tabular-nums' }}>{tasa}% {lbl}</span>}
            <span style={{ width: 46, flex: 'none', textAlign: 'right', fontWeight: 600, fontSize: 12, fontVariantNumeric: 'tabular-nums', color: 'var(--ink)' }}>{v.toLocaleString('es-CL')}</span>
          </div>
        )
      })}
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
  if (!p) return null
  return (
    <div style={{ marginTop: 26, paddingTop: 20, borderTop: '1px solid var(--line)' }}>
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
          const pts = p.hist.map((h) => ({ fecha: h.fecha, total: (h.av_inm || 0) + (h.av_veh || 0) }))
          const W = 320, Hh = 46
          const vals = pts.map((q) => q.total)
          const lo = Math.min(...vals), hi = Math.max(...vals, 1)
          const range = hi - lo || 1
          const xx = (i: number) => (pts.length === 1 ? W / 2 : (i / (pts.length - 1)) * W)
          const yy = (v: number) => Hh - 4 - ((v - lo) / range) * (Hh - 8)
          const path = pts.map((q, i) => `${i === 0 ? 'M' : 'L'} ${xx(i).toFixed(1)} ${yy(q.total).toFixed(1)}`).join(' ')
          return (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <span className="section-tag" style={{ margin: 0 }}>Evolución del patrimonio declarado</span>
                <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>{pts.length} declaraciones · {pts[0].fecha.slice(0, 4)}–{pts[pts.length - 1].fecha.slice(0, 4)}</span>
              </div>
              <svg viewBox={`0 0 ${W} ${Hh}`} preserveAspectRatio="none" style={{ width: '100%', height: 44, marginTop: 6, overflow: 'visible' }}>
                <path d={path} fill="none" stroke="var(--primary)" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
                {pts.map((q, i) => (
                  <circle key={i} cx={xx(i)} cy={yy(q.total)} r={1.6} fill="var(--primary)">
                    <title>{q.fecha}: {clp(q.total)}</title>
                  </circle>
                ))}
              </svg>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                <span className="mono" style={{ fontSize: 9.5, color: 'var(--muted)' }}>{clp(pts[0].total)}</span>
                <span className="mono" style={{ fontSize: 9.5, color: 'var(--ink)' }}>hoy {clp(pts[pts.length - 1].total)}</span>
              </div>
            </div>
          )
        })()}
      </>}
      <p className="mono" style={{ fontSize: 9.5, color: 'var(--muted)', marginTop: 16, letterSpacing: '0.06em' }}>
        Patrimonio según la Declaración de Intereses y Patrimonio (Ley 20.880), publicada en InfoProbidad.
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
  else {
    // KPIs adaptativos: solo los tipos de causa que el juez efectivamente resuelve.
    kpis = [{ label: 'Causas', value: r.n.toLocaleString('es-CL') }]
    if (r.lab_n) kpis.push({ label: 'Acogida laboral', value: pct(r.lab_acogida), sub: `${r.lab_n.toLocaleString('es-CL')} laborales` })
    if (r.pen_n) {
      kpis.push({ label: 'Condena penal', value: pct(r.pen_condena), sub: `${r.pen_n.toLocaleString('es-CL')} penales` })
      kpis.push({ label: 'Pena promedio', value: r.pen_dias ? `${Math.round(r.pen_dias)} días` : '—' })
    }
    if (kpis.length < 4 && r.materias && r.materias.length)
      kpis.push({ label: 'Materia principal', value: String(r.materias[0][0]), sub: `${r.materias[0][1].toLocaleString('es-CL')} causas` })
    if (kpis.length < 4 && r.comp) kpis.push({ label: 'Competencia', value: r.comp.replace(/_/g, ' ') })
  }
  // gráficos por tipo
  const charts: { label: string; items?: Mat[]; color: string }[] = []
  if (tipo === 'fiscales') charts.push({ label: 'Delitos más perseguidos', items: r.delitos, color: 'var(--blue-dark)' })
  else {
    // rótulo sensible al tipo de juez: penal → condena, laboral → acogida, mixto → ambos
    const matLabel = tipo !== 'jueces' ? 'Materias más frecuentes'
      : r.pen_n && r.lab_n ? 'Cómo resuelve por materia · % condena (penal) / acogida (laboral)'
      : r.pen_n ? 'Cómo resuelve por materia · % de condena'
      : r.lab_n ? 'Cómo resuelve por materia · % de acogida de la demanda'
      : 'Materias más frecuentes'
    charts.push({ label: matLabel, items: r.materias, color: 'var(--primary)' })
  }
  if (tipo === 'empresas') charts.push({ label: 'Defensas más usadas', items: r.defensas, color: 'var(--cyan)' })
  if (tipo === 'abogados') charts.push({ label: 'Partes / empresas en sus causas', items: r.contrapartes, color: 'var(--cyan)' })
  const shown = charts.filter((c) => c.items && c.items.length)
  return (
    <div className="card" style={{ marginBottom: 22 }}>
      <div className="section-tag">{CFG[tipo].tag} · ficha</div>
      <h2 style={{ fontSize: 22, fontWeight: 600, margin: '4px 0 4px' }}>{r.nombre}</h2>
      {(r.trib || r.comp) && <div className="mono" style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 16 }}>{(r.trib || r.comp || '').replace(/_/g, ' ')}</div>}
      {tipo === 'jueces' && r.bio && (
        <p style={{ fontSize: 13.5, color: 'var(--ink)', fontWeight: 300, lineHeight: 1.55, margin: '0 0 18px', maxWidth: 820 }}>
          {r.bio}
          <span className="mono" style={{ display: 'block', fontSize: 9.5, color: 'var(--muted)', marginTop: 8, letterSpacing: '0.06em' }}>Reseña generada con IA sobre las sentencias públicas del juez.</span>
        </p>
      )}
      {tipo === 'jueces' && r.linkedin && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, margin: '0 0 18px', padding: '12px 14px', border: '1px solid var(--line)', borderRadius: 10, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <div className="kpi-label">Trayectoria · LinkedIn</div>
            {r.linkedin.job && <div style={{ fontSize: 13, color: 'var(--ink)', marginTop: 4 }}>{r.linkedin.job}{r.linkedin.company ? ` · ${r.linkedin.company}` : ''}</div>}
            {r.linkedin.edu && r.linkedin.edu.length > 0 && (
              <div className="mono" style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                {r.linkedin.edu.map((e) => [e.school, e.deg, e.field].filter(Boolean).join(' · ')).filter(Boolean).join('  /  ')}
              </div>
            )}
            <div className="mono" style={{ fontSize: 9, color: 'var(--muted)', marginTop: 5, letterSpacing: '0.06em' }}>Según LinkedIn · sin verificar</div>
          </div>
          {r.linkedin.url && (
            <a href={r.linkedin.url.startsWith('http') ? r.linkedin.url : `https://${r.linkedin.url}`} target="_blank" rel="noopener noreferrer" title="Ver perfil de LinkedIn" style={{ flexShrink: 0, color: 'var(--primary)', display: 'inline-flex' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-label="LinkedIn"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13zM7.12 20.45H3.55V9h3.57v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.21 0 22.23 0z"/></svg>
            </a>
          )}
        </div>
      )}
      {tipo === 'jueces' && <JuezPerfil r={r} />}
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
      {tipo === 'jueces' && r.defensor && (r.defensor.pub_rate != null || r.defensor.priv_rate != null) && (
        <div style={{ marginTop: 22 }}>
          <div className="kpi-label">Tasa de condena según la defensa del imputado</div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
            {([['Defensoría Penal Pública', r.defensor.pub_rate, r.defensor.pub_n], ['Defensa particular', r.defensor.priv_rate, r.defensor.priv_n]] as [string, number | null | undefined, number][]).map(([lbl, rate, n]) => rate == null ? null : (
              <div key={lbl} style={{ flex: '1 1 200px', border: '1px solid var(--line)', borderRadius: 8, padding: '12px 14px' }}>
                <div className="mono" style={{ fontSize: 9.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{lbl}</div>
                <div style={{ fontSize: 22, fontWeight: 600, color: 'var(--ink)', marginTop: 2 }}>{Math.round(rate * 100)}%</div>
                <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>condena · {n.toLocaleString('es-CL')} causas</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function rowStat(tipo: string, r: Row) {
  if (tipo === 'fiscales') return `${r.n.toLocaleString('es-CL')} causas${r.condena != null ? ` · ${pct(r.condena)} condena` : ''}`
  if (tipo === 'abogados') return `${r.n.toLocaleString('es-CL')} causas${r.comp ? ` · ${r.comp.replace(/_/g, ' ')}` : ''}`
  if (tipo === 'empresas') return `${r.n.toLocaleString('es-CL')} causas${r.condena != null ? ` · ${pct(r.condena)} condena` : ''}`
  // jueces: una sola métrica, la del tipo dominante → formato uniforme en la lista
  const penal = (r.pen_n || 0) >= (r.lab_n || 0)
  const m = penal
    ? (r.pen_condena != null ? `${pct(r.pen_condena)} condena` : '')
    : (r.lab_acogida != null ? `${pct(r.lab_acogida)} acogida` : '')
  return `${r.n.toLocaleString('es-CL')} causas${m ? ` · ${m}` : ''}`
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
              {sel && <div><Ficha tipo={tipo} r={sel} /></div>}
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
