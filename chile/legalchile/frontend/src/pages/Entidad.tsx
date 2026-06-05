import '../styles/decide.css'

type Cfg = { tag: string; h1: string; desc: string; count: string; sub: string; preguntas: string[] }

const ENT: Record<string, Cfg> = {
  jueces: {
    tag: 'Jueces',
    h1: 'La ficha de cada juez, leída de sus fallos',
    desc: 'Sobre las sentencias públicas de cada juez se construye su ficha — materias que más resuelve, duración de sus causas, tipo de resolución y montos — es decir, su tendencia histórica de fallo. No es opinión: es el comportamiento real medido sobre el corpus.',
    count: '2.390', sub: 'jueces con ficha en construcción',
    preguntas: ['¿Cómo tiende a fallar el juez al que le tocó mi causa?', '¿Qué proporción del monto demandado suele acoger?', '¿Cuánto demora una causa con este juez?', '¿Cómo evolucionó su criterio en el tiempo?'],
  },
  abogados: {
    tag: 'Abogados / Partes',
    h1: 'Cómo litiga cada parte, a partir de sus causas',
    desc: 'Identificando a la demandante y demandada en cada causa se reconstruye su historial litigioso — qué proporción resuelve por sentencia y cuánta por acuerdo, en qué materias litiga y con qué resultado. El historial real de esa contraparte, no su reputación.',
    count: '46.485', sub: 'empresas/partes perfiladas en lo laboral',
    preguntas: ['¿Cómo litiga esta empresa: pelea en tribunal o transa?', '¿En cuántas cuotas suele pactar los avenimientos?', '¿Qué montos se solicitan típicamente contra esta parte?', '¿Cuál es su tasa de resultados adversos?'],
  },
  fiscales: {
    tag: 'Fiscales',
    h1: 'El comportamiento del Ministerio Público, medido',
    desc: 'Sobre las causas penales se reconstruye la actuación persecutora — tasa de condena obtenida, delitos perseguidos, penas solicitadas y resultado. La capa penal de extracción se está corriendo sobre el corpus; las fichas se publican cuando están medidas y validadas.',
    count: 'En extracción', sub: '316.679 causas penales ya leídas',
    preguntas: ['¿Qué tasa de condena obtiene en esta materia?', '¿Qué delitos concentra la persecución?', '¿Qué penas se imponen típicamente?', '¿Cómo varía el resultado por tribunal?'],
  },
  tribunales: {
    tag: 'Tribunales',
    h1: 'El perfil de cada tribunal y juzgado',
    desc: 'Por juzgado se agregan duración de causas, materias, tasa de resultados y carga — para leer cómo opera cada tribunal del país. Construido sobre las sentencias públicas, no sobre estadísticas declaradas.',
    count: '437', sub: 'tribunales con perfil en construcción',
    preguntas: ['¿Cuánto demora una causa en este juzgado, en promedio y mediana?', '¿Qué materias concentra?', '¿Cómo es su tasa de acogidas?', '¿Conviene ir a sentencia o buscar conciliación aquí?'],
  },
}

export default function Entidad({ tipo }: { tipo: keyof typeof ENT }) {
  const c = ENT[tipo]
  return (
    <div className="decide-root">
      <header className="nav">
        <div className="wrap">
          <a href="/" className="brand"><b>Claude Legal Chile</b><span className="sub">· Derecho chileno real</span></a>
          <div className="spacer" />
          <nav className="navlinks">
            <a href="/jueces" style={tipo === 'jueces' ? { color: 'var(--primary)' } : undefined}>Jueces</a>
            <a href="/abogados" style={tipo === 'abogados' ? { color: 'var(--primary)' } : undefined}>Abogados</a>
            <a href="/fiscales" style={tipo === 'fiscales' ? { color: 'var(--primary)' } : undefined}>Fiscales</a>
            <a href="/tribunales" style={tipo === 'tribunales' ? { color: 'var(--primary)' } : undefined}>Tribunales</a>
            <details className="more">
              <summary>Más <span className="caret">▾</span></summary>
              <div className="more-menu">
                <a href="/">Inicio</a>
                <a href="/buscar">Buscar</a>
                <a href="/analisis">Análisis ↗</a>
                <a href="/#que-es">¿Qué es?</a>
                <a href="/#corpus">El corpus</a>
                <a href="/#participar">Participar</a>
              </div>
            </details>
            <a className="btn btn-primary" href="mailto:antonio@unholster.com?subject=Claude%20Legal%20Chile">Contacto</a>
          </nav>
        </div>
      </header>

      <section className="hero">
        <div className="wrap">
          <div className="toprow">
            <span className="section-tag">{c.tag} · Rayos X de la justicia</span>
            <span className="status"><span className="dot" style={{ background: 'var(--warn)' }} /> Explorador en construcción</span>
          </div>
          <h1>{c.h1}</h1>
          <p className="lead">{c.desc}</p>
          <div style={{ marginTop: 22 }}>
            <span className="kpi-value" style={{ color: 'var(--primary)' }}>{c.count}</span>
            <span className="mono" style={{ marginLeft: 12, fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{c.sub}</span>
          </div>
        </div>
      </section>

      <section className="blk gray">
        <div className="wrap">
          <div className="sec-head">
            <span className="section-tag">Lo que este explorador permite responder</span>
            <h2>Preguntas que se contestan con datos del corpus</h2>
            <p>Cada ficha se construye leyendo las sentencias públicas. La capa de extracción está procesando el universo completo; las cifras por entidad se publican cuando están medidas y validadas — no antes.</p>
          </div>
          <div className="chips">
            {c.preguntas.map((q) => <span key={q}>{q}</span>)}
          </div>
          <div style={{ marginTop: 30, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <a className="btn btn-primary" href="/buscar">Buscar en el corpus</a>
            <a className="btn btn-ghost" href="/">Volver al inicio</a>
          </div>
        </div>
      </section>
    </div>
  )
}
