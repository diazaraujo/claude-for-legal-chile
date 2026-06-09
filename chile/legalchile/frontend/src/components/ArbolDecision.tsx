// Árbol de decisión penal — flujo tipo n8n (Causa → Decisión → Pena → Cumplimiento).
// Reusable: página /decisiones y dentro del perfil de cada juez.
// Datos: campos estructurados (decisión) + extracción de texto (grado de pena, cumplimiento).

export type ArbolNode = {
  label: string
  n: number
  pen_n?: number
  decision: { condenatoria?: number; absolutoria?: number; medida_seguridad?: number; otros?: number }
  grados: Record<string, number>
  prom_dias?: number | null
  efectiva?: number
  sustituida?: number
  cob?: number | null
  dur?: Record<string, number>
  dur_total?: number
  anios?: Record<string, number>
}

const GORDER = ['multa', 'prision_min', 'prision_medio', 'prision_max', 'menor_min', 'menor_medio', 'menor_max', 'mayor_min', 'mayor_medio', 'mayor_max']
const GLAB: Record<string, string> = {
  multa: 'Multa', prision_min: 'Prisión · mínimo', prision_medio: 'Prisión · medio', prision_max: 'Prisión · máximo',
  menor_min: 'Presidio menor · mín', menor_medio: 'Presidio menor · medio', menor_max: 'Presidio menor · máx',
  mayor_min: 'Presidio mayor · mín', mayor_medio: 'Presidio mayor · medio', mayor_max: 'Presidio mayor · máx',
}
const NF = (n: number) => n.toLocaleString('es-CL')
const PCT = (a: number, b: number) => (b ? (100 * a) / b : 0)
const fmtPct = (p: number) => (p >= 10 ? Math.round(p) : p.toFixed(1)) + '%'
function diasHuman(d?: number | null) {
  if (d == null) return '—'
  d = Math.round(d)
  if (d < 60) return d + ' días'
  const a = Math.floor(d / 365), m = Math.round((d % 365) / 30.4)
  return (a ? a + (a === 1 ? ' año' : ' años') : '') + (a && m ? ' ' : '') + (m ? m + ' m' : '') || d + ' días'
}

type N = { col: number; cls: string; cy: number; title: string; big?: string; sm?: string; color?: string }
type E = { x1: number; y1: number; x2: number; y2: number; pct: number; color: string }

export default function ArbolDecision({ node, mode }: { node: ArbolNode; mode: 'juez' | 'materia' | 'global' }) {
  if (!node) return null
  const dec = node.decision || {}
  const cond = dec.condenatoria || 0, abs = dec.absolutoria || 0, med = dec.medida_seguridad || 0
  const totDec = cond + abs + med || 1
  const decs: [string, string, number, string][] = ([
    ['cond', 'Condena', cond, '#0a7d3c'],
    ['abs', 'Absolución', abs, '#b42318'],
    ['med', 'Medida de seguridad', med, '#9a6b00'],
  ] as [string, string, number, string][]).filter((d) => d[2] > 0)

  const grd = node.grados || {}
  const totG = Object.values(grd).reduce((a, b) => a + b, 0) || 1
  const gentries = GORDER.filter((k) => grd[k]).map((k) => [k, grd[k]] as [string, number]).sort((a, b) => b[1] - a[1])
  const TOPN = 6
  const shown = gentries.slice(0, TOPN)
  const restN = gentries.slice(TOPN).reduce((a, b) => a + b[1], 0)
  const penRows: [string, number][] = shown.map((g) => [GLAB[g[0]] || g[0], g[1]] as [string, number]).concat(restN ? [['Otros grados', restN]] : [])

  const efe = node.efectiva || 0, sus = node.sustituida || 0, totC = efe + sus
  const cumRows: [string, number, string][] = totC > 0 ? [['Pena efectiva', efe, '#1f3a5f'], ['Pena sustituida', sus, '#5b7aa6']] : []

  const COL = [0, 212, 432, 652], NW = [182, 168, 182, 168]
  const gapDec = 96, gapPen = 70, gapCum = 118, NODEH = 58, TOP = 50
  const hDec = decs.length * gapDec, hPen = Math.max(penRows.length, 1) * gapPen, hCum = cumRows.length * gapCum
  const maxH = Math.max(hDec, hPen, hCum, 120)
  const midY = TOP + maxH / 2
  const cY = (i: number, k: number, g: number) => midY + (i - (k - 1) / 2) * g
  const W = COL[3] + NW[3], H = TOP + maxH + 30

  const nodes: N[] = []
  const edges: E[] = []
  const right = (c: number) => COL[c] + NW[c]

  nodes.push({ col: 0, cls: 'entry', cy: midY, title: (mode === 'materia' ? 'Sentencia' : 'Causa') + ' penal', big: NF(node.n), sm: mode === 'global' ? 'nacional' : mode === 'materia' ? 'de esta materia' : 'ante este juez' })

  let condCy: number | null = null
  decs.forEach((d, i) => {
    const cy = cY(i, decs.length, gapDec)
    nodes.push({ col: 1, cls: d[0], cy, title: d[1], big: fmtPct(PCT(d[2], totDec)), sm: NF(d[2]) + ' casos', color: d[3] })
    edges.push({ x1: right(0), y1: midY, x2: COL[1], y2: cy, pct: PCT(d[2], totDec), color: d[3] })
    if (d[0] === 'cond') condCy = cy
  })

  if (condCy != null && penRows.length) {
    penRows.forEach((g, i) => {
      const cy = cY(i, penRows.length, gapPen)
      nodes.push({ col: 2, cls: 'pena', cy, title: g[0], big: fmtPct(PCT(g[1], totG)), sm: NF(g[1]), color: 'var(--primary)' })
      edges.push({ x1: right(1), y1: condCy as number, x2: COL[2], y2: cy, pct: PCT(g[1], totG), color: '#3a5e8c' })
    })
  } else if (condCy != null) {
    nodes.push({ col: 2, cls: 'pena', cy: midY, title: 'Pena no detectada', sm: 'cobertura ' + (node.cob != null ? node.cob + '%' : '—') + ' del texto', color: 'var(--primary)' })
  }

  if (condCy != null && cumRows.length) {
    cumRows.forEach((c, i) => {
      const cy = cY(i, cumRows.length, gapCum)
      nodes.push({ col: 3, cls: 'cum', cy, title: c[0], big: fmtPct(PCT(c[1], totC)), sm: NF(c[1]), color: c[2] })
      edges.push({ x1: right(2), y1: midY, x2: COL[3], y2: cy, pct: PCT(c[1], totC), color: c[2] })
    })
  }

  const hdr = () => ({ position: 'absolute' as const, top: 14, fontFamily: 'var(--mono, monospace)', fontSize: 9.5, letterSpacing: '0.12em', textTransform: 'uppercase' as const, color: 'var(--muted)', fontWeight: 600 })

  return (
    <div>
      <div style={{ overflowX: 'auto', padding: '4px 2px 10px' }}>
        <div style={{ position: 'relative', width: W, height: H, minWidth: W }}>
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0, overflow: 'visible', pointerEvents: 'none' }}>
            {edges.map((e, i) => {
              const mx = (e.x1 + e.x2) / 2
              return (
                <g key={i}>
                  <path d={`M${e.x1},${e.y1} C${mx},${e.y1} ${mx},${e.y2} ${e.x2},${e.y2}`} fill="none" stroke={e.color} strokeWidth={Math.max(1.3, (e.pct / 100) * 12)} strokeOpacity={0.45} strokeLinecap="round" />
                  <text x={mx} y={(e.y1 + e.y2) / 2 - 5} textAnchor="middle" style={{ fill: 'var(--muted)', fontFamily: 'var(--mono, monospace)', fontSize: 10.5, fontWeight: 600, paintOrder: 'stroke', stroke: '#fff', strokeWidth: 4, strokeLinejoin: 'round' as const }}>{fmtPct(e.pct)}</text>
                </g>
              )
            })}
          </svg>
          {[['Causa', 0], ['Decisión', 1], ['Pena impuesta', 2], ['Cumplimiento', 3]].map(([t, c]) => (
            <div key={t as string} style={{ ...hdr(), left: COL[c as number], maxWidth: NW[c as number] + 40 }}>{t}</div>
          ))}
          {nodes.map((n, i) => {
            const isEntry = n.cls === 'entry'
            return (
              <div key={i} style={{
                position: 'absolute', left: COL[n.col], top: n.cy - NODEH / 2, width: NW[n.col], minHeight: NODEH,
                background: isEntry ? '#0b1f3a' : '#fff', color: isEntry ? '#fff' : 'var(--ink)',
                border: '1.5px solid ' + (isEntry ? '#0b1f3a' : 'var(--line)'), borderRadius: 11, padding: '9px 12px',
                boxShadow: '0 1px 2px rgba(11,31,58,.06)', boxSizing: 'border-box',
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.2 }}>{n.title}</div>
                {n.big && <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: isEntry ? 19 : 17, fontWeight: 600, marginTop: 2, color: isEntry ? '#fff' : n.color }}>{n.big}</div>}
                {n.sm && <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: isEntry ? '#aebfdd' : 'var(--muted)', marginTop: 2 }}>{n.sm}</div>}
              </div>
            )
          })}
        </div>
      </div>
      <p className="mono" style={{ fontSize: 10, color: 'var(--muted)', lineHeight: 1.55, marginTop: 6 }}>
        El grosor de cada conector es proporcional a la probabilidad. <b>Decisión</b> es campo estructurado de la sentencia.
        <b> Pena</b> se extrae del texto (cobertura ~73% de las condenas); el % de cada grado es sobre las penas detectadas.
        <b> Cumplimiento</b>: sustituida = beneficio Ley 18.216.{node.prom_dias != null ? <> Pena promedio ≈ <b>{diasHuman(node.prom_dias)}</b>.</> : null}
      </p>
    </div>
  )
}
