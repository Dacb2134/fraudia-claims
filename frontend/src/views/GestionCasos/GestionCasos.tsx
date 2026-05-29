import { useState, useEffect } from 'react'
import Sidebar from '../../components/shared/Sidebar'
import { obtenerSesion } from '../../services/authService'
import type { NavProps } from '../../App'
import type { Siniestro } from '../../models'
import { apiFetch, API_URL } from '../../services/api'

// ─── Helpers ────────────────────────────────────────────────────────────────
const RAMOS      = ['Todos los ramos', 'Vehículos', 'Hogar', 'Salud', 'Vida', 'Generales']
const SUCURSALES = ['Todas las sucursales', 'Quito', 'Guayaquil', 'Cuenca', 'Ambato', 'Loja', 'Ibarra', 'Manta', 'Riobamba', 'Portoviejo', 'Esmeraldas']
const PAGE_SIZE  = 25

function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(2)}`
}
function fmtDate(d: string) {
  try { return new Date(d).toLocaleDateString('es-EC', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return d }
}
function initials(id: string) { return (id || 'AS').replace(/[^A-Z0-9]/g, '').slice(0, 2) || 'AS' }

const NIVEL = {
  ROJO:     { icon: 'report',   color: 'text-error',     bar: 'bg-error',     rowBg: 'risk-gradient-high', label: 'Alto Riesgo'  },
  AMARILLO: { icon: 'warning',  color: 'text-secondary', bar: 'bg-secondary', rowBg: 'risk-gradient-med',  label: 'Medio Riesgo' },
  VERDE:    { icon: 'verified', color: 'text-outline',   bar: 'bg-outline',   rowBg: '',                   label: 'Sin anomalías'},
}

// ─── Component ──────────────────────────────────────────────────────────────
export default function GestionCasos({ onNav, onLogout, onVerDetalle }: NavProps & {
  onVerDetalle: (id: string) => void
}) {
  const [casos,       setCasos]       = useState<Siniestro[]>([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState<string | null>(null)
  const [total,       setTotal]       = useState(0)
  const [page,        setPage]        = useState(1)
  const [nivelFiltro, setNivelFiltro] = useState('')
  const [ramoFiltro,  setRamoFiltro]  = useState('')
  const [sucFiltro,   setSucFiltro]   = useState('')
  const [busqueda,    setBusqueda]    = useState('')
  const [tabActivo,   setTabActivo]   = useState<'todos'|'ROJO'|'AMARILLO'|'VERDE'>('todos')
  const [marcados,    setMarcados]    = useState<Record<string, 'revision'|'limpio'>>({})
  const [toast,       setToast]       = useState<string | null>(null)
  const [showNotif,   setShowNotif]   = useState(false)

  const usuario  = obtenerSesion()
  const rolLabel = usuario?.rol === 'admin'      ? 'Administrador'
                 : usuario?.rol === 'supervisor' ? 'Supervisor'
                 : 'Analista de Riesgos'
  const inicial  = usuario?.nombre?.charAt(0).toUpperCase() ?? 'A'

  const nivelEfectivo = tabActivo !== 'todos' ? tabActivo : nivelFiltro || undefined

  useEffect(() => {
    setLoading(true); setError(null)
    const p = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
    if (nivelEfectivo) p.set('nivel_riesgo', nivelEfectivo)
    if (ramoFiltro)    p.set('ramo',         ramoFiltro)
    if (sucFiltro)     p.set('sucursal',      sucFiltro)
    apiFetch<{ data: Siniestro[], total: number }>(`/api/v1/siniestros/?${p}`)
      .then(r => { setCasos(r.data); setTotal(r.total) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [nivelEfectivo, ramoFiltro, sucFiltro, page])

  const casosFiltrados = busqueda.trim()
    ? casos.filter(c =>
        c.id_siniestro.toLowerCase().includes(busqueda.toLowerCase()) ||
        c.id_asegurado.toLowerCase().includes(busqueda.toLowerCase()) ||
        c.ramo.toLowerCase().includes(busqueda.toLowerCase()))
    : casos

  const totalPages = Math.ceil(total / PAGE_SIZE)

  function cambiarTab(t: typeof tabActivo) { setTabActivo(t); setNivelFiltro(''); setPage(1) }

  function mostrarToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  function marcarRevision(id: string) {
    setMarcados(prev => ({ ...prev, [id]: 'revision' }))
    mostrarToast(`Caso ${id} marcado para revisión manual`)
  }

  function marcarLimpio(id: string) {
    setMarcados(prev => ({ ...prev, [id]: 'limpio' }))
    mostrarToast(`Caso ${id} marcado como sin anomalías`)
  }

  return (
    <div className="bg-background text-on-surface flex min-h-screen overflow-hidden">

      {/* ── Shared Sidebar ── */}
      <Sidebar vistaActiva="casos" onNav={onNav} onLogout={onLogout} />

      {/* ── Main ── */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">

        {/* TopAppBar */}
        <header className="flex justify-between items-center w-full px-margin-desktop h-16 z-50 bg-surface-container-lowest shadow-sm">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative w-full max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
              <input
                className="w-full bg-surface-container-low border-none rounded-full py-2 pl-10 pr-4 font-body-md text-on-surface focus:ring-2 focus:ring-primary transition-all"
                placeholder="Buscar por ID de caso, asegurado o ramo..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              {/* Campana */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setShowNotif(v => !v)}
                  className="p-2 text-on-surface-variant hover:bg-surface-container-high transition-colors rounded-full relative">
                  <span className="material-symbols-outlined">notifications</span>
                  <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full"/>
                </button>
                {showNotif && (
                  <div style={{
                    position: 'absolute', top: '100%', right: 0, marginTop: 8,
                    background: '#fff', borderRadius: 12, border: '1px solid #c4c6d3',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.12)', width: 300, zIndex: 200,
                  }}>
                    <div style={{ padding: '12px 16px', borderBottom: '1px solid #c4c6d3', fontWeight: 700, fontSize: 13, color: '#002662' }}>
                      Alertas del Sistema
                    </div>
                    {casos.filter(c => c.nivel_riesgo === 'ROJO').slice(0, 4).map(c => (
                      <div
                        key={c.id_siniestro}
                        onClick={() => { onVerDetalle(c.id_siniestro); setShowNotif(false) }}
                        style={{ padding: '10px 16px', borderBottom: '1px solid #f0f2fa', cursor: 'pointer', fontSize: 12 }}>
                        <strong style={{ color: '#ba1a1a' }}>{c.id_siniestro}</strong>
                        <span style={{ color: '#434652' }}> · {c.ramo} · Score {c.score_riesgo}</span>
                      </div>
                    ))}
                    <div style={{ padding: '8px 16px' }}>
                      <button
                        onClick={() => setShowNotif(false)}
                        style={{ width: '100%', padding: 6, background: '#e6eeff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12, color: '#002662', fontWeight: 600 }}>
                        Cerrar
                      </button>
                    </div>
                  </div>
                )}
              </div>
              {/* Help → configuración */}
              <button
                onClick={() => onNav('configuracion')}
                className="p-2 text-on-surface-variant hover:bg-surface-container-high transition-colors rounded-full">
                <span className="material-symbols-outlined">help</span>
              </button>
            </div>
            <div className="h-8 w-[1px] bg-outline-variant"/>
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="font-label-sm text-label-sm font-bold text-primary">{usuario?.nombre ?? rolLabel}</p>
                <p className="font-label-sm text-[10px] text-on-surface-variant uppercase">{rolLabel}</p>
              </div>
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white font-bold border-2 border-primary-container">{inicial}</div>
            </div>
          </div>
        </header>

        {/* Canvas */}
        <div className="flex-1 overflow-y-auto p-margin-desktop space-y-gutter">

          {/* Título + acciones */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h2 className="font-headline-lg text-headline-lg text-primary">Gestión de Casos</h2>
              <p className="font-body-lg text-on-surface-variant">Monitoreo y validación de reclamos sospechosos en tiempo real.</p>
            </div>
            <div className="flex items-center gap-3">
              <a
                href={`${API_URL}/api/v1/reporte/exportar?nivel=todos`}
                target="_blank" rel="noreferrer"
                className="flex items-center gap-2 px-4 py-2.5 bg-surface-container-highest text-primary font-body-md rounded-xl hover:bg-surface-variant transition-all no-underline">
                <span className="material-symbols-outlined text-[20px]">ios_share</span>
                Exportar Reporte
              </a>
              <button
                onClick={() => onNav('agente')}
                className="flex items-center gap-2 px-6 py-2.5 bg-primary text-white font-body-md rounded-xl hover:shadow-lg active:scale-[0.98] transition-all border-none cursor-pointer">
                <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                Consultar IA
              </button>
            </div>
          </div>

          {/* Filtros */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 bg-white p-4 rounded-xl shadow-sm border border-outline-variant/30">
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm text-on-surface-variant px-1">Nivel de Riesgo</label>
              <select
                className="w-full bg-surface-container-low border-outline-variant rounded-lg font-body-md focus:ring-primary"
                value={nivelFiltro}
                onChange={e => { setNivelFiltro(e.target.value); setTabActivo('todos'); setPage(1) }}>
                <option value="">Todos los niveles</option>
                <option value="ROJO">Alto Riesgo (ROJO)</option>
                <option value="AMARILLO">Medio Riesgo (AMARILLO)</option>
                <option value="VERDE">Bajo Riesgo (VERDE)</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm text-on-surface-variant px-1">Sucursal / Ciudad</label>
              <select
                className="w-full bg-surface-container-low border-outline-variant rounded-lg font-body-md"
                value={sucFiltro}
                onChange={e => { setSucFiltro(e.target.value === 'Todas las sucursales' ? '' : e.target.value); setPage(1) }}>
                {SUCURSALES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm text-on-surface-variant px-1">Ramo</label>
              <select
                className="w-full bg-surface-container-low border-outline-variant rounded-lg font-body-md"
                value={ramoFiltro}
                onChange={e => { setRamoFiltro(e.target.value === 'Todos los ramos' ? '' : e.target.value); setPage(1) }}>
                {RAMOS.map(r => <option key={r}>{r}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm text-on-surface-variant px-1">Resultados</label>
              <div className="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-lg px-3 py-1.5">
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant">info</span>
                <span className="font-body-md text-on-surface-variant">{total} casos encontrados</span>
              </div>
            </div>
          </div>

          {/* Tabla */}
          <div className="bg-white rounded-2xl shadow-sm border border-outline-variant/30 overflow-hidden flex flex-col min-h-[600px]">

            {/* Tabs */}
            <div className="flex border-b border-outline-variant/30 px-6">
              {([
                { key: 'todos',    label: 'Todos'        },
                { key: 'ROJO',     label: 'Alto Riesgo'  },
                { key: 'AMARILLO', label: 'Medio Riesgo' },
                { key: 'VERDE',    label: 'Bajo Riesgo'  },
              ] as const).map(({ key, label }) => (
                <button key={key}
                  onClick={() => cambiarTab(key)}
                  className={`px-6 py-4 font-title-md transition-colors border-none cursor-pointer bg-transparent ${
                    tabActivo === key
                      ? 'text-primary border-b-2 border-primary'
                      : 'text-on-surface-variant hover:text-primary border-b-2 border-transparent'
                  }`}>
                  {label}
                  {tabActivo === key && total > 0 && (
                    <span className="ml-2 bg-primary-container text-white text-[10px] px-1.5 py-0.5 rounded-full">{total}</span>
                  )}
                </button>
              ))}
            </div>

            {/* Tabla content */}
            <div className="overflow-x-auto flex-1">
              {loading ? (
                <div className="flex items-center justify-center gap-3 h-48 text-on-surface-variant">
                  <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 32, color: '#002662' }}>sync</span>
                  Cargando casos...
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-48 gap-2 text-error">
                  <span className="material-symbols-outlined text-[40px]">error</span>
                  <p>{error}</p>
                </div>
              ) : casosFiltrados.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 gap-2 text-on-surface-variant">
                  <span className="material-symbols-outlined text-[40px]">inbox</span>
                  <p>No hay casos con los filtros seleccionados.</p>
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low/50">
                      {['ID Caso / Fecha', 'Asegurado', 'Tipo / Monto', 'IA Score', 'Acciones Rápidas'].map(h => (
                        <th key={h} className="px-6 py-4 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/20">
                    {casosFiltrados.map(caso => {
                      const cfg = NIVEL[caso.nivel_riesgo] || NIVEL.VERDE
                      return (
                        <tr key={caso.id_siniestro}
                          className={`hover:bg-surface-container-low transition-colors group ${cfg.rowBg}`}>
                          <td className="px-6 py-4">
                            <span className="block font-label-sm text-primary font-bold">{caso.id_siniestro}</span>
                            <span className="block font-label-sm text-[11px] text-on-surface-variant">{fmtDate(caso.fecha_ocurrencia)}</span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center font-bold text-primary text-[12px] flex-shrink-0">
                                {initials(caso.id_asegurado)}
                              </div>
                              <div>
                                <span className="block font-body-md font-semibold">{caso.id_asegurado}</span>
                                <span className="block font-label-sm text-[11px] text-on-surface-variant">{caso.sucursal}</span>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="block font-body-md">{caso.ramo} · {caso.cobertura}</span>
                            <span className="block font-title-md text-primary">{fmt(caso.monto_reclamado)}</span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`material-symbols-outlined text-[18px] ${cfg.color}`}
                                  style={{ fontVariationSettings: "'FILL' 1" }}>
                                  {cfg.icon}
                                </span>
                                <span className={`font-title-md font-bold ${cfg.color}`}>{caso.score_riesgo}%</span>
                              </div>
                              <div className="w-24 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                                <div className={`${cfg.bar} h-full`} style={{ width: `${caso.score_riesgo}%` }}/>
                              </div>
                              <span className="font-label-sm text-[10px] text-on-surface-variant">{cfg.label}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                className="p-2 text-primary hover:bg-primary-container hover:text-white rounded-lg transition-all border-none cursor-pointer"
                                title="Ver Detalles"
                                onClick={() => onVerDetalle(caso.id_siniestro)}>
                                <span className="material-symbols-outlined">visibility</span>
                              </button>
                              <button
                                className={`p-2 rounded-lg transition-all border-none cursor-pointer ${marcados[caso.id_siniestro] === 'revision' ? 'bg-error text-white' : 'text-on-surface-variant hover:bg-error-container hover:text-error'}`}
                                title="Marcar para Revisión Manual"
                                onClick={() => marcarRevision(caso.id_siniestro)}>
                                <span className="material-symbols-outlined">flag</span>
                              </button>
                              <button
                                className={`p-2 rounded-lg transition-all border-none cursor-pointer ${marcados[caso.id_siniestro] === 'limpio' ? 'bg-green-500 text-white' : 'text-on-surface-variant hover:bg-green-100 hover:text-green-700'}`}
                                title="Marcar como Sin Anomalías"
                                onClick={() => marcarLimpio(caso.id_siniestro)}>
                                <span className="material-symbols-outlined">check_circle</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>

            {/* Paginación */}
            {!loading && total > PAGE_SIZE && (
              <div className="mt-auto px-6 py-4 border-t border-outline-variant/30 flex items-center justify-between">
                <span className="font-label-sm text-on-surface-variant">
                  Mostrando {(page-1)*PAGE_SIZE+1}–{Math.min(page*PAGE_SIZE, total)} de {total} reclamos
                </span>
                <div className="flex items-center gap-2">
                  <button
                    className="p-2 rounded-lg hover:bg-surface-container-high disabled:opacity-30 border-none cursor-pointer"
                    disabled={page === 1}
                    onClick={() => setPage(p => p-1)}>
                    <span className="material-symbols-outlined">chevron_left</span>
                  </button>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const n = page <= 3 ? i+1 : page-2+i
                    if (n < 1 || n > totalPages) return null
                    return (
                      <button key={n}
                        onClick={() => setPage(n)}
                        className={`w-8 h-8 rounded-lg font-label-sm border-none cursor-pointer ${n === page ? 'bg-primary text-white' : 'hover:bg-surface-container-high'}`}>
                        {n}
                      </button>
                    )
                  })}
                  <button
                    className="p-2 rounded-lg hover:bg-surface-container-high disabled:opacity-30 border-none cursor-pointer"
                    disabled={page === totalPages}
                    onClick={() => setPage(p => p+1)}>
                    <span className="material-symbols-outlined">chevron_right</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="w-full py-4 px-margin-desktop flex flex-col md:flex-row justify-between items-center bg-surface-dim mt-auto">
          <p className="font-label-sm text-label-sm text-on-surface-variant mb-4 md:mb-0">
            Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.
          </p>
          <div className="flex gap-6">
            {['Ética AI', 'Soporte Técnico', 'Documentación'].map(l => (
              <a key={l} className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#">{l}</a>
            ))}
          </div>
        </footer>
      </main>

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 100, left: '50%', transform: 'translateX(-50%)',
          background: '#1a1c1e', color: '#fff', padding: '10px 20px', borderRadius: 10,
          fontSize: 13, fontWeight: 500, zIndex: 200, whiteSpace: 'nowrap',
          boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
        }}>
          {toast}
        </div>
      )}

      {/* FAB IA */}
      <button
        onClick={() => onNav('agente')}
        className="fixed bottom-8 right-8 w-16 h-16 bg-primary text-white rounded-full flex items-center justify-center shadow-2xl hover:shadow-primary-container/40 transition-all z-[100] group border-none cursor-pointer">
        <span className="material-symbols-outlined text-[32px] group-hover:scale-110 transition-transform">smart_toy</span>
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-error rounded-full animate-pulse border-2 border-white"/>
      </button>

      <style>{`
        .risk-gradient-high { background: linear-gradient(90deg, rgba(186,26,26,0.1) 0%, rgba(255,255,255,0) 100%); }
        .risk-gradient-med  { background: linear-gradient(90deg, rgba(218,226,255,0.2) 0%, rgba(255,255,255,0) 100%); }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
