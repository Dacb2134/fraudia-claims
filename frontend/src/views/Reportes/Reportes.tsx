import { useState, useEffect } from 'react'
import Sidebar from '../../components/shared/Sidebar'
import { apiFetch, API_URL } from '../../services/api'
import type { NavProps } from '../../App'

// ─── Tipos ──────────────────────────────────────────────────────────────────
interface ResumenGeneral {
  total_siniestros: number
  casos_alto_riesgo: number
  casos_medio_riesgo: number
  casos_bajo_riesgo: number
  monto_en_riesgo_alto: number
  score_promedio: number
  porcentaje_riesgo: number
}
interface CasoCritico {
  id_siniestro: string
  ramo: string
  monto_reclamado: number
  score_normalizado: number
  nivel_riesgo: string
  alertas_activadas: string
}
interface RamoRiesgo {
  ramo: string
  total: number
  rojos: number
  pct_riesgo: number
}
interface MetricasModelo {
  precision: number
  recall: number
  f1_score: number
  auc_roc: number
  algoritmo: string
}
interface ReporteEjecutivo {
  resumen_general: ResumenGeneral
  top_10_casos_criticos: CasoCritico[]
  riesgo_por_ramo: RamoRiesgo[]
  metricas_modelo: MetricasModelo
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(2)}`
}

const NIVEL_COLOR = { ROJO: '#ba1a1a', AMARILLO: '#f97316', VERDE: '#16a34a' }

// ─── Componente ──────────────────────────────────────────────────────────────
export default function Reportes({ onNav, onLogout, onVerDetalle }: NavProps & {
  onVerDetalle: (id: string) => void
}) {
  const [data,    setData]    = useState<ReporteEjecutivo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    apiFetch<ReporteEjecutivo>('/api/v1/reporte/ejecutivo')
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const r = data?.resumen_general

  return (
    <div className="bg-background text-on-surface flex min-h-screen overflow-hidden">
      <Sidebar vistaActiva="reportes" onNav={onNav} onLogout={onLogout} />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Header */}
        <header className="flex justify-between items-center px-margin-desktop h-16 bg-surface-container-lowest shadow-sm flex-shrink-0">
          <h2 className="font-title-md text-title-md font-black text-primary">Reportes y Análisis Ejecutivo</h2>
          <button
            onClick={() => document.getElementById('export-section')?.scrollIntoView({ behavior: 'smooth' })}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border border-primary text-primary bg-white hover:bg-primary hover:text-white transition-colors cursor-pointer">
            <span className="material-symbols-outlined text-[18px]">download</span>
            Exportar Reporte
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-margin-desktop space-y-gutter">

          {loading ? (
            <div className="flex items-center justify-center h-64 gap-3 text-on-surface-variant">
              <span className="material-symbols-outlined text-[36px] text-primary" style={{ animation: 'spin 1s linear infinite' }}>sync</span>
              Cargando reporte ejecutivo…
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-64 gap-2 text-error">
              <span className="material-symbols-outlined text-[40px]">error</span>
              <p>{error}</p>
            </div>
          ) : data && r && (
            <>
              {/* ── KPIs ── */}
              <section>
                <h3 className="font-headline-lg text-headline-lg text-primary mb-4">Resumen General</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

                  <div className="bg-white rounded-xl p-5 border border-outline-variant/30 shadow-sm">
                    <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Total Siniestros</p>
                    <p className="text-3xl font-bold text-primary">{r.total_siniestros.toLocaleString()}</p>
                    <p className="text-xs text-on-surface-variant mt-1">Score promedio: {r.score_promedio}</p>
                  </div>

                  <div className="bg-white rounded-xl p-5 border-b-4 shadow-sm" style={{ borderBottomColor: '#ba1a1a' }}>
                    <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Alto Riesgo (ROJO)</p>
                    <p className="text-3xl font-bold" style={{ color: '#ba1a1a' }}>{r.casos_alto_riesgo}</p>
                    <p className="text-xs mt-1" style={{ color: '#ba1a1a' }}>{r.porcentaje_riesgo}% del total</p>
                  </div>

                  <div className="bg-white rounded-xl p-5 border-b-4 shadow-sm" style={{ borderBottomColor: '#f97316' }}>
                    <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Medio Riesgo (AMARILLO)</p>
                    <p className="text-3xl font-bold" style={{ color: '#f97316' }}>{r.casos_medio_riesgo}</p>
                    <p className="text-xs text-on-surface-variant mt-1">Requieren revisión documental</p>
                  </div>

                  <div className="bg-primary rounded-xl p-5 shadow-sm">
                    <p className="font-label-sm text-label-sm text-primary-fixed-dim mb-1">Monto en Riesgo Alto</p>
                    <p className="text-3xl font-bold text-white">{fmt(r.monto_en_riesgo_alto)}</p>
                    <p className="text-xs text-primary-fixed-dim mt-1">En casos nivel ROJO</p>
                  </div>
                </div>
              </section>

              {/* ── Top 10 casos + Riesgo por ramo ── */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Top 10 */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-outline-variant/30 shadow-sm overflow-hidden">
                  <div className="flex items-center justify-between p-5 border-b border-outline-variant/20">
                    <h3 className="font-medium text-on-surface flex items-center gap-2">
                      <span className="material-symbols-outlined text-error" style={{ fontVariationSettings: "'FILL' 1" }}>crisis_alert</span>
                      Top 10 Casos Críticos
                    </h3>
                    <span className="text-xs text-on-surface-variant">Ordenados por score descendente</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-surface-container-low/40">
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">#</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">ID Siniestro</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">Ramo</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">Monto</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">Score</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">Acción</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant/15">
                        {data.top_10_casos_criticos.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="px-4 py-12 text-center text-on-surface-variant">
                              <span className="material-symbols-outlined text-[40px] block mb-2 opacity-40">inbox</span>
                              No hay casos críticos en el nivel actual.
                              <br/>
                              <span className="text-xs">Los casos de riesgo medio se pueden revisar en Gestión de Casos.</span>
                            </td>
                          </tr>
                        ) : (
                          data.top_10_casos_criticos.map((caso, i) => (
                            <tr key={caso.id_siniestro} className="hover:bg-surface-container-low/50 transition-colors">
                              <td className="px-4 py-3 text-sm font-bold text-on-surface-variant">{i + 1}</td>
                              <td className="px-4 py-3">
                                <span className="font-label-sm text-label-sm font-bold text-primary">{caso.id_siniestro}</span>
                              </td>
                              <td className="px-4 py-3 text-sm text-on-surface-variant">{caso.ramo}</td>
                              <td className="px-4 py-3 text-sm font-semibold">{fmt(caso.monto_reclamado)}</td>
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                                    <div className="h-full rounded-full"
                                      style={{ width: `${caso.score_normalizado}%`, background: NIVEL_COLOR[caso.nivel_riesgo as keyof typeof NIVEL_COLOR] || '#ba1a1a' }}/>
                                  </div>
                                  <span className="text-sm font-bold" style={{ color: NIVEL_COLOR[caso.nivel_riesgo as keyof typeof NIVEL_COLOR] || '#ba1a1a' }}>
                                    {caso.score_normalizado}
                                  </span>
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <button
                                  onClick={() => onVerDetalle(caso.id_siniestro)}
                                  className="text-primary hover:bg-surface-container-high rounded-lg p-1.5 transition-colors border-none cursor-pointer bg-transparent"
                                  title="Ver detalle">
                                  <span className="material-symbols-outlined text-[18px]">visibility</span>
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Riesgo por ramo */}
                <div className="bg-white rounded-xl border border-outline-variant/30 shadow-sm p-5">
                  <h3 className="font-medium text-on-surface mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">bar_chart</span>
                    Riesgo por Ramo
                  </h3>
                  <div className="space-y-4">
                    {data.riesgo_por_ramo.map(r => (
                      <div key={r.ramo}>
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="text-on-surface font-medium">{r.ramo}</span>
                          <span className="font-bold" style={{ color: r.pct_riesgo > 20 ? '#ba1a1a' : r.pct_riesgo > 10 ? '#f97316' : '#16a34a' }}>
                            {r.pct_riesgo}% riesgo
                          </span>
                        </div>
                        <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min(r.pct_riesgo * 3, 100)}%`,
                              background: r.pct_riesgo > 20 ? '#ba1a1a' : r.pct_riesgo > 10 ? '#f97316' : '#16a34a',
                            }}/>
                        </div>
                        <p className="text-[11px] text-on-surface-variant mt-0.5">
                          {r.total} siniestros · {r.rojos} alto riesgo
                          {r.rojos === 0 && <span className="text-green-600"> · sin alertas críticas</span>}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ── Métricas del modelo ── */}
              <section>
                <h3 className="font-headline-lg text-headline-lg text-primary mb-4">Métricas del Modelo IA</h3>
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                  {[
                    { label: 'Algoritmo',  value: data.metricas_modelo.algoritmo,                   unit: '',   color: '#002662' },
                    { label: 'Precisión',  value: (data.metricas_modelo.precision * 100).toFixed(1), unit: '%',  color: '#16a34a' },
                    { label: 'Recall',     value: (data.metricas_modelo.recall * 100).toFixed(1),    unit: '%',  color: '#0053cf' },
                    { label: 'F1-Score',   value: (data.metricas_modelo.f1_score * 100).toFixed(1),  unit: '%',  color: '#0053cf' },
                    { label: 'AUC-ROC',    value: (data.metricas_modelo.auc_roc * 100).toFixed(1),   unit: '%',  color: '#16a34a' },
                  ].map(m => (
                    <div key={m.label} className="bg-white rounded-xl p-5 border border-outline-variant/30 shadow-sm text-center">
                      <p className="font-label-sm text-label-sm text-on-surface-variant mb-2">{m.label}</p>
                      <p className="text-2xl font-bold" style={{ color: m.color }}>{m.value}{m.unit}</p>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-on-surface-variant mt-3 text-center italic">
                  Motor híbrido: 60% reglas de negocio + 40% modelo ML supervisado. Estas métricas son orientativas y corresponden al conjunto de evaluación sintético.
                </p>
              </section>

              {/* ── Exportar ── */}
              <section id="export-section" className="rounded-xl p-6 flex flex-col gap-5"
                style={{ background: 'linear-gradient(135deg, #002662 0%, #003a8f 100%)' }}>
                <div>
                  <h3 className="font-medium mb-1" style={{ color: '#fff' }}>Exportar reporte para auditoría</h3>
                  <p className="text-sm" style={{ color: '#b9c9ed' }}>
                    Excel incluye formato con colores por nivel de riesgo y dos hojas (presentación + datos).
                    CSV para importar en otros sistemas.
                  </p>
                </div>
                <div className="flex flex-wrap gap-4">
                  {([
                    { nivel: 'ROJO',     label: 'Alto Riesgo',  accentBg: '#ba1a1a', accentText: '#fff' },
                    { nivel: 'AMARILLO', label: 'Medio Riesgo', accentBg: '#f97316', accentText: '#fff' },
                    { nivel: 'todos',    label: 'Todos',         accentBg: '#e6eeff', accentText: '#002662' },
                  ] as const).map(({ nivel, label, accentBg, accentText }) => (
                    <div key={nivel} className="flex flex-col gap-1.5">
                      <span style={{ fontSize: 11, color: '#b9c9ed', fontFamily: 'JetBrains Mono' }}>
                        {label}
                      </span>
                      <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.2)' }}>
                        <a
                          href={`${API_URL}/api/v1/reporte/exportar?nivel=${nivel}&formato=xlsx`}
                          target="_blank" rel="noreferrer"
                          className="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold no-underline transition-opacity hover:opacity-80"
                          style={{ background: accentBg, color: accentText, borderRight: '1px solid rgba(255,255,255,0.25)' }}
                          title="Descargar Excel con formato (.xlsx)">
                          <span className="material-symbols-outlined text-[16px]">table_chart</span>
                          Excel
                        </a>
                        <a
                          href={`${API_URL}/api/v1/reporte/exportar?nivel=${nivel}&formato=csv`}
                          target="_blank" rel="noreferrer"
                          className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold no-underline transition-opacity hover:opacity-80"
                          style={{ background: 'rgba(255,255,255,0.12)', color: '#e6eeff' }}
                          title="Descargar datos planos (.csv)">
                          <span className="material-symbols-outlined text-[14px]">grid_on</span>
                          CSV
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>

        <footer className="py-3 px-margin-desktop flex justify-between items-center bg-surface-dim border-t border-outline-variant flex-shrink-0">
          <p className="text-xs text-on-surface-variant">Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.</p>
          <div className="flex gap-4">
            {[
              { label: 'Ética AI',  action: () => onNav('configuracion') },
              { label: 'Soporte',   action: () => onNav('agente')        },
              { label: 'Docs',      action: () => onNav('configuracion') },
            ].map(({ label, action }) => (
              <button key={label}
                onClick={action}
                className="text-xs text-on-surface-variant hover:text-primary"
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}>
                {label}
              </button>
            ))}
          </div>
        </footer>
      </main>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
