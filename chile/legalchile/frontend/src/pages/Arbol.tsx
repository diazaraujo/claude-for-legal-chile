import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import '../styles/decide.css'

type Norma = { id_norma: number; tipo: string; numero: string; titulo: string; derogado: string; n_articulos: number; n_sentencias: number }
type Articulo = { articulo: string; n_sentencias: number; n_citas: number }
type Ejemplo = { doc_path: string; extracto: string; fecha?: string; rol?: string; caratulado?: string; tribunal?: string }
type Tesis = { cluster: number; n: number; nombre?: string; descripcion?: string; terminos: string[]; ejemplos: Ejemplo[] }
type Detalle = { anios: { anio: string; n_sentencias: number }[]; tesis: Tesis[] }

const nf = new Intl.NumberFormat('es-CL')

export default function Arbol() {
  const [q, setQ] = useState('')
  const [normas, setNormas] = useState<Norma[]>([])
  const [norma, setNorma] = useState<Norma | null>(null)
  const [articulos, setArticulos] = useState<Articulo[]>([])
  const [art, setArt] = useState<string | null>(null)
  const [detalle, setDetalle] = useState<Detalle | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function buscarNormas(e?: React.FormEvent) {
    e?.preventDefault()
    setLoading(true); setError(''); setNorma(null); setArt(null); setDetalle(null)
    try {
      const { data } = await api.get('/corpus/arbol/normas', { params: { q, limit: 30 } })
      setNormas(data.normas || [])
    } catch {
      setError('No se pudo consultar el árbol normativo.')
    } finally { setLoading(false) }
  }

  useEffect(() => { buscarNormas() }, [])

  async function abrirNorma(n: Norma) {
    setNorma(n); setArt(null); setDetalle(null); setLoading(true)
    try {
      const { data } = await api.get(`/corpus/arbol/norma/${n.id_norma}`)
      setArticulos(data.articulos || [])
    } catch { setError('Error cargando artículos.') } finally { setLoading(false) }
  }

  async function abrirArticulo(a: string) {
    if (!norma) return
    setArt(a); setLoading(true); setDetalle(null)
    try {
      const { data } = await api.get(`/corpus/arbol/norma/${norma.id_norma}/articulo`, { params: { art: a, muestras: 3 } })
      setDetalle(data)
    } catch { setError('Error cargando el detalle del artículo.') } finally { setLoading(false) }
  }

  const maxAnio = detalle ? Math.max(1, ...detalle.anios.map((x) => x.n_sentencias)) : 1

  return (
    <div className="decide-root">
      <div className="topbar"><div className="wrap">
        <Link className="back" to="/">&larr; Claude Legal Chile</Link>
        <span className="tb-r">Árbol normativo · Interpretaciones</span>
      </div></div>

      <section className="hero" style={{ paddingBottom: 24 }}>
        <div className="wrap">
          <span className="section-tag">Árbol normativo</span>
          <h1 style={{ marginBottom: 8 }}>Cómo los tribunales <em>interpretan cada artículo</em>.</h1>
          <p className="lead" style={{ marginBottom: 20 }}>
            4,4 millones de citas normativas extraídas de los considerandos: norma → artículo →
            evolución temporal → líneas interpretativas, con sentencias de respaldo.
          </p>
          <form onSubmit={buscarNormas} style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Ej.: código del trabajo, 19.496, consumidores, constitución…"
              style={{ flex: '1 1 420px', minWidth: 0, padding: '12px 16px', fontSize: 15, border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'inherit', background: '#fff', color: 'var(--ink)' }} />
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Buscando…' : 'Buscar norma'}
            </button>
          </form>
          {error && <p style={{ color: '#b00', marginTop: 12 }}>{error}</p>}
        </div>
      </section>

      <section style={{ padding: '8px 0 60px' }}><div className="wrap">
        {!norma && normas.length > 0 && (
          <div style={{ display: 'grid', gap: 10 }}>
            {normas.map((n) => (
              <button key={n.id_norma} onClick={() => abrirNorma(n)}
                style={{ textAlign: 'left', padding: '14px 18px', border: '1px solid var(--line)', borderRadius: 12, background: '#fff', cursor: 'pointer', fontFamily: 'inherit' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <strong>{n.tipo} {n.numero}</strong>
                  <span style={{ fontSize: 13, opacity: 0.7 }}>
                    {nf.format(n.n_sentencias)} sentencias · {nf.format(n.n_articulos)} artículos
                    {n.derogado !== 'no derogado' && ' · DEROGADA'}
                  </span>
                </div>
                <div style={{ fontSize: 13.5, opacity: 0.85, marginTop: 4 }}>{n.titulo}</div>
              </button>
            ))}
          </div>
        )}

        {norma && (
          <>
            <p style={{ marginBottom: 14 }}>
              <a style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={() => { setNorma(null); setArt(null); setDetalle(null) }}>&larr; normas</a>
              <strong style={{ marginLeft: 10 }}>{norma.tipo} {norma.numero}</strong>
              <span style={{ marginLeft: 8, fontSize: 13, opacity: 0.7 }}>{norma.titulo}</span>
            </p>
            {!art && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {articulos.slice(0, 200).map((a) => (
                  <button key={a.articulo} onClick={() => abrirArticulo(a.articulo)}
                    style={{ padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 10, background: '#fff', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13.5 }}>
                    art. {a.articulo} <span style={{ opacity: 0.6 }}>· {nf.format(a.n_sentencias)}</span>
                  </button>
                ))}
                {articulos.length > 200 && <span style={{ fontSize: 13, opacity: 0.6, alignSelf: 'center' }}>… y {nf.format(articulos.length - 200)} artículos más (usa la búsqueda)</span>}
              </div>
            )}
          </>
        )}

        {norma && art && detalle && (
          <>
            <h2 style={{ margin: '6px 0 14px' }}>Artículo {art}</h2>

            {detalle.anios.length > 1 && (
              <div style={{ marginBottom: 26 }}>
                <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>
                  Sentencias que lo citan por año · la curva refleja también la densidad del corpus por período
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 90 }}>
                  {detalle.anios.map((y) => (
                    <div key={y.anio} title={`${y.anio}: ${nf.format(y.n_sentencias)}`}
                      style={{ flex: 1, background: 'var(--accent, #1a6f5b)', opacity: 0.85, borderRadius: '3px 3px 0 0', height: `${Math.max(3, (y.n_sentencias / maxAnio) * 100)}%` }} />
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, opacity: 0.6 }}>
                  <span>{detalle.anios[0]?.anio}</span><span>{detalle.anios[detalle.anios.length - 1]?.anio}</span>
                </div>
              </div>
            )}

            <div style={{ display: 'grid', gap: 14 }}>
              {detalle.tesis.map((t) => (
                <div key={t.cluster} style={{ border: '1px solid var(--line)', borderRadius: 12, background: '#fff', padding: '16px 18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
                    <strong>{t.nombre || (t.terminos.length ? t.terminos.slice(0, 3).join(' · ') : `Línea ${t.cluster + 1}`)}</strong>
                    <span style={{ fontSize: 13, opacity: 0.7 }}>{nf.format(t.n)} considerandos</span>
                  </div>
                  {t.descripcion && <p style={{ fontSize: 13.5, margin: '6px 0 0', opacity: 0.85 }}>{t.descripcion}</p>}
                  {!t.nombre && t.terminos.length > 0 && (
                    <p style={{ fontSize: 12.5, margin: '6px 0 0', opacity: 0.6 }}>términos distintivos: {t.terminos.join(', ')}</p>
                  )}
                  {t.ejemplos.length > 0 && (
                    <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
                      {t.ejemplos.map((e, i) => (
                        <div key={i} style={{ fontSize: 13, borderLeft: '3px solid var(--line)', paddingLeft: 10 }}>
                          <span style={{ opacity: 0.65 }}>{e.fecha || 's/f'}{e.tribunal ? ` · ${e.tribunal}` : ''}{e.rol ? ` · rol ${e.rol}` : ''}</span>
                          <div style={{ marginTop: 2 }}>«{e.extracto}…»</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {detalle.tesis.length === 0 && (
                <p style={{ opacity: 0.7, fontSize: 14 }}>
                  Este artículo tiene pocas citas para distinguir líneas interpretativas — revisa las sentencias directamente en Búsqueda.
                </p>
              )}
            </div>
          </>
        )}
      </div></section>
    </div>
  )
}
