// Tab "Tramitación" del perfil de juez: distribución de tiempos del juicio,
// volumen de sentencias por año, y contexto nacional de apelaciones.
import { ArbolNode } from './ArbolDecision'

export type Apelaciones = {
  n: number
  resultados: { key: string; label: string; n: number; pct: number }[]
  tipos: { tipo: string; n: number }[]
}

const NF = (n: number) => n.toLocaleString('es-CL')
const DUR_ORDER = ['0', '1', '2', '3', '4+']
const DUR_LAB: Record<string, string> = { '0': 'Mismo año', '1': '1 año', '2': '2 años', '3': '3 años', '4+': '4+ años' }

function HBars({ rows, color, fmtRight }: { rows: [string, number, number][]; color: string; fmtRight?: (n: number, p: number) => string }) {
  return (
    <div style={{ marginTop: 8 }}>
      {rows.map(([k, n, p]) => (
        <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '7px 0' }}>
          <span style={{ width: 120, flex: 'none', fontSize: 12.5, color: 'var(--ink)', fontWeight: 400 }}>{k}</span>
          <div style={{ flex: 1, background: 'var(--bg)', borderRadius: 4, height: 16, overflow: 'hidden' }}>
            <div style={{ width: `${Math.max(2, p)}%`, height: '100%', background: color, borderRadius: 4 }} />
          </div>
          <span className="mono" style={{ width: 96, flex: 'none', textAlign: 'right', fontSize: 11.5, color: 'var(--ink)', fontWeight: 600 }}>{fmtRight ? fmtRight(n, p) : `${p.toFixed(0)}% · ${NF(n)}`}</span>
        </div>
      ))}
    </div>
  )
}

export default function TramitacionJuez({ node, apelaciones }: { node: ArbolNode; apelaciones?: Apelaciones }) {
  const durTotal = node.dur_total || 0
  const durRows: [string, number, number][] = DUR_ORDER.filter((b) => (node.dur || {})[b]).map((b) => [DUR_LAB[b], node.dur![b], durTotal ? (100 * node.dur![b]) / durTotal : 0])
  // típico: bucket modal
  const modal = durRows.slice().sort((a, b) => b[1] - a[1])[0]
  // sentencias por año
  const anios = node.anios || {}
  const years = Object.keys(anios).map(Number).sort((a, b) => a - b)
  const maxY = Math.max(1, ...years.map((y) => anios[String(y)]))

  return (
    <div style={{ marginTop: 4 }}>
      {/* TIEMPOS */}
      <div className="section-tag" style={{ marginBottom: 2 }}>Distribución de tiempos del juicio</div>
      <p className="mono" style={{ fontSize: 10, color: 'var(--muted)', margin: '0 0 4px' }}>Del año del rol a la sentencia · estimación a nivel anual · {NF(durTotal)} causas</p>
      {durTotal > 0 ? (
        <>
          <HBars rows={durRows} color="#266FE0" />
          {modal && <p style={{ fontSize: 12.5, color: 'var(--ink)', marginTop: 8 }}>La mayoría se resuelve en <b>{modal[0].toLowerCase()}</b> ({modal[2].toFixed(0)}% de las causas).</p>}
        </>
      ) : <p className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>Sin dato de rol para estimar duración.</p>}

      {/* SENTENCIAS POR AÑO */}
      <div className="section-tag" style={{ margin: '22px 0 2px' }}>Sentencias por año</div>
      <p className="mono" style={{ fontSize: 10, color: 'var(--muted)', margin: '0 0 8px' }}>Volumen anual de fallos de este juez · {years.length ? `${years[0]}–${years[years.length - 1]}` : '—'}</p>
      {years.length ? (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 120, borderBottom: '1px solid var(--line)', paddingBottom: 0 }}>
          {years.map((y) => {
            const v = anios[String(y)]
            return (
              <div key={y} title={`${y}: ${NF(v)} sentencias`} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', alignItems: 'center', height: '100%' }}>
                <div style={{ width: '100%', maxWidth: 26, height: `${(v / maxY) * 100}%`, background: '#266FE0', borderRadius: '3px 3px 0 0', minHeight: 2 }} />
                <span className="mono" style={{ fontSize: 8.5, color: 'var(--muted)', marginTop: 3, transform: 'rotate(-0deg)' }}>{String(y).slice(2)}</span>
              </div>
            )
          })}
        </div>
      ) : <p className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>Sin sentencias datadas.</p>}

      {/* APELACIONES */}
      <div className="section-tag" style={{ margin: '24px 0 2px' }}>Apelación a cortes superiores</div>
      <p style={{ fontSize: 12.5, color: 'var(--ink)', fontWeight: 300, lineHeight: 1.5, margin: '2px 0 8px', maxWidth: 760 }}>
        No es atribuible a este juez en particular: las sentencias de las Cortes no traen el identificador de la causa de origen ni el juez de primera instancia. Lo que sí se puede medir es el <b>contexto nacional</b> de cómo resuelven las Cortes los recursos en materia penal:
      </p>
      {apelaciones ? (
        <>
          <HBars
            rows={apelaciones.resultados.map((r) => [r.label, r.n, r.pct] as [string, number, number])}
            color="#5b7aa6"
            fmtRight={(_n, p) => `${p.toFixed(0)}%`}
          />
          <p className="mono" style={{ fontSize: 9.5, color: 'var(--muted)', marginTop: 10, lineHeight: 1.5 }}>
            {NF(apelaciones.n)} recursos penales en Corte de Apelaciones + Suprema. La mayoría son apelaciones cautelares o incidentales (p. ej. prisión preventiva); la nulidad de la sentencia definitiva es una fracción menor. Corpus selectivo de sentencias publicadas.
          </p>
        </>
      ) : <p className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>Contexto de apelaciones no disponible.</p>}
    </div>
  )
}
