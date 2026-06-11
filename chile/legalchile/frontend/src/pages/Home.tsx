import '../styles/decide.css'
import { Footer } from './Sobre'

const LAB: [string, number, string][] = [
  ['Demanda acogida', 35.7, 'var(--ok)'],
  ['Acogida en parte', 32.6, 'var(--cyan)'],
  ['Rechazada', 26.3, 'var(--err)'],
  ['Otros (desist./concil.)', 5.4, 'var(--muted)'],
]
const PEN: [string, number, string][] = [
  ['Condena', 76.7, 'var(--blue-dark)'],
  ['Absolución', 17.5, 'var(--ok)'],
  ['No aplica', 4.9, 'var(--muted)'],
  ['Sobreseimiento', 0.8, 'var(--line)'],
]

function Bars({ rows }: { rows: [string, number, string][] }) {
  return (
    <>
      {rows.map(([label, pct, color]) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '9px 0' }}>
          <span style={{ width: 140, flex: 'none', fontSize: 13, color: 'var(--muted)', fontWeight: 300 }}>{label}</span>
          <div style={{ flex: 1, background: 'var(--bg)', borderRadius: 6, height: 20, overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 6 }} />
          </div>
          <span style={{ width: 50, textAlign: 'right', fontWeight: 600, fontSize: 13, fontVariantNumeric: 'tabular-nums' }}>{String(pct).replace('.', ',')}%</span>
        </div>
      ))}
    </>
  )
}

export default function Home() {
  return (
    <div className="decide-root">
      {/* HEADER */}
      <header className="nav">
        <div className="wrap">
          <a href="/" className="brand"><b>Claude Legal Chile</b><span className="sub">· Derecho chileno real</span></a>
          <div className="spacer" />
          <nav className="navlinks">
            <a href="/jueces">Jueces</a>
            <a href="/abogados">Abogados</a>
            <a href="/fiscales">Fiscales</a>
            <a href="/tribunales">Tribunales</a>
            <a href="/decisiones">Decisiones</a>
            <a href="/arbol">Árbol normativo</a>
            <details className="more">
              <summary>Más <span className="caret">▾</span></summary>
              <div className="more-menu">
                <a href="/empresas">Empresas demandadas</a>
                <a href="/buscar">Buscar</a>
                <a href="/analisis">Análisis ↗</a>
                <a href="/sobre">¿Qué es?</a>
                <a href="/sobre#comparativa">Antes / después</a>
                <a href="/sobre#corpus">El corpus</a>
                <a href="/sobre#pipeline">El recorrido</a>
                <a href="/sobre#capacidades">Capacidades</a>
                <a href="/sobre#participar">Participar</a>
              </div>
            </details>
            <a className="btn btn-primary" href="mailto:antonio@unholster.com?subject=Claude%20Legal%20Chile">Contacto</a>
          </nav>
        </div>
      </header>

      {/* HERO · dashboard estilo Decide (status, buscador, pills) */}
      <section className="hero">
        <div className="wrap">
          <div className="toprow">
            <span className="section-tag">Claude Legal Chile</span>
            <div style={{ textAlign: 'right' }}>
              <div className="status"><span className="dot"></span> Al día · actualización continua</div>
              <div className="mono" style={{ fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginTop: 4 }}>Cobertura 1834 → 2026</div>
            </div>
          </div>
          <h1>Rayos X de la <em>justicia chilena</em></h1>
          <p className="lead">Cuánto, cómo y con qué resultado falla cada tribunal — leído de los fallos reales. Un corpus verificable del derecho chileno (legislación vigente, jurisprudencia y dictámenes) que se puede consultar, citar y medir.</p>
          <form action="/buscar" method="get" className="searchbox">
            <input name="q" placeholder="Buscar — ley, artículo, rol de causa, RUT, materia, dictamen…" autoComplete="off" />
          </form>
          <div className="pills">
            <a className="pill" href="/jueces">Jueces</a>
            <a className="pill" href="/abogados">Abogados</a>
            <a className="pill" href="/fiscales">Fiscales</a>
            <a className="pill" href="/tribunales">Tribunales</a>
            <a className="pill" href="/decisiones">Decisiones</a>
            <a className="pill" href="/arbol">Árbol normativo</a>
            <a className="pill" href="/sobre">Sobre el corpus</a>
          </div>
        </div>
      </section>

      {/* KPI STATS · números reales del corpus */}
      <section className="blk" style={{ padding: '8px 0 24px' }}>
        <div className="wrap">
          <span className="section-tag uline">Lo que tiene este corpus</span>
          <div className="kpi-grid">
            <div className="kpi-card"><div className="kpi-label">Documentos indexados</div><div className="kpi-value">4,9 M</div></div>
            <div className="kpi-card"><div className="kpi-label">Normas · BCN</div><div className="kpi-value">142.283</div></div>
            <div className="kpi-card"><div className="kpi-label">Causas leídas por IA</div><div className="kpi-value">585.688</div></div>
            <div className="kpi-card"><div className="kpi-label">Embeddings semánticos</div><div className="kpi-value">4,8 M</div></div>
          </div>
          <span className="section-tag uline" style={{ marginTop: 18, display: 'block' }}>Entidades perfiladas · clic para explorar</span>
          <div className="kpi-grid">
            <a className="kpi-card hov" href="/jueces"><div className="kpi-label">Jueces</div><div className="kpi-value">2.390</div></a>
            <a className="kpi-card hov" href="/abogados"><div className="kpi-label">Abogados</div><div className="kpi-value">71.245</div></a>
            <a className="kpi-card hov" href="/fiscales"><div className="kpi-label">Fiscales</div><div className="kpi-value">8.643</div></a>
            <a className="kpi-card hov" href="/tribunales"><div className="kpi-label">Tribunales</div><div className="kpi-value">437</div></a>
            <a className="kpi-card hov" href="/decisiones"><div className="kpi-label">Árbol de decisión</div><div className="kpi-value">penal</div></a>
            <a className="kpi-card hov" href="/arbol"><div className="kpi-label">Árbol normativo</div><div className="kpi-value">4,4 M citas</div></a>
          </div>
        </div>
      </section>

      {/* ANALÍTICA · Rayos X de la justicia (datos reales) */}
      <section className="blk gray" id="rayos-x">
        <div className="wrap">
          <div className="sec-head" style={{ marginBottom: 18 }}>
            <span className="section-tag">Lectura del corpus · datos reales</span>
            <h2>¿Cómo falla la justicia chilena?</h2>
            <p>No es teoría: la capa de extracción lee la parte resolutiva de cada sentencia y mide el resultado. Estas cifras salen de los fallos ya procesados — algo que una IA general no puede saber porque no tiene los datos.</p>
          </div>
          <div className="rayosx-cols">
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                <div className="kpi-label" style={{ marginBottom: 0 }}>Justicia laboral · resultado</div>
                <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>139.126 causas leídas</div>
              </div>
              <Bars rows={LAB} />
              <p style={{ marginTop: 14, fontSize: 14, color: 'var(--ink)', fontWeight: 300 }}><b style={{ fontWeight: 600 }}>68% de las demandas laborales prosperan</b> total o parcialmente. Materias más frecuentes: cobro de prestaciones, despido injustificado, nulidad del despido (Ley Bustos).</p>
            </div>
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                <div className="kpi-label" style={{ marginBottom: 0 }}>Justicia penal · decisión</div>
                <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>316.679 causas leídas</div>
              </div>
              <Bars rows={PEN} />
              <p style={{ marginTop: 14, fontSize: 14, color: 'var(--ink)', fontWeight: 300 }}><b style={{ fontWeight: 600 }}>Tasa de condena del 81%</b> cuando hay decisión de fondo. La ficha de cada juez y juzgado se construye sobre estas sentencias públicas.</p>
            </div>
          </div>
          <div style={{ marginTop: 22, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <a className="btn btn-primary" href="/analisis">Ver el análisis del corpus completo <svg className="ic"><path d="M5 12h14M13 6l6 6-6 6" /></svg></a>
            <a className="btn btn-ghost" href="/sobre">Cómo funciona</a>
            <span className="mono" style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Muestra en aumento · extracción en curso</span>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
