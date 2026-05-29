import { useState, useEffect } from 'react'
import Sidebar from '../../components/shared/Sidebar'
import { apiFetch } from '../../services/api'
import type { NavProps } from '../../App'

interface ModeloEstado {
  modelo_entrenado: boolean
  tipo_modelo: string
  mensaje: string
}

export default function Configuracion({ onNav, onLogout }: NavProps) {
  const [modelo,  setModelo]  = useState<ModeloEstado | null>(null)
  const [loading, setLoading] = useState(true)
  const [entrenar, setEntrenar] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')

  useEffect(() => {
    apiFetch<ModeloEstado>('/api/v1/ml/estado')
      .then(setModelo)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  async function handleEntrenar() {
    setEntrenar('loading')
    try {
      await apiFetch('/api/v1/ml/entrenar', { method: 'POST' })
      setEntrenar('ok')
      const estado = await apiFetch<ModeloEstado>('/api/v1/ml/estado')
      setModelo(estado)
    } catch {
      setEntrenar('error')
    }
  }

  const INFO_SISTEMA = [
    { label: 'Versión del sistema',   value: 'FraudIA Claims v1.0.0' },
    { label: 'Backend',               value: 'FastAPI + Python 3.11'  },
    { label: 'Base de datos',         value: 'MySQL 8.0'              },
    { label: 'Motor de reglas',       value: 'ReasonScore v2.4'       },
    { label: 'Agente IA',             value: 'Google Gemini'          },
    { label: 'Semáforo',              value: 'Verde 0-40 · Amarillo 41-75 · Rojo 76-100' },
  ]

  const SEÑALES_FRAUDE = [
    { codigo: 'S-01', señal: 'Reclamo borde de vigencia',   max: '8 pts'  },
    { codigo: 'S-02', señal: 'Demora denuncia robo',         max: '8 pts'  },
    { codigo: 'S-03', señal: 'Alta frecuencia asegurado',    max: '8 pts'  },
    { codigo: 'S-06', señal: 'Proveedor recurrente',         max: '10 pts' },
    { codigo: 'S-07', señal: 'Documentos incompletos',       max: '4 pts'  },
    { codigo: 'S-10', señal: 'Documentos inconsistentes',    max: '10 pts' },
    { codigo: 'S-11', señal: 'Reporte tardío',               max: '5 pts'  },
    { codigo: 'S-12', señal: 'Narrativas similares',         max: '8 pts'  },
    { codigo: 'S-13', señal: 'Monto cercano suma asegurada', max: '4 pts'  },
  ]

  return (
    <div className="bg-background text-on-surface flex min-h-screen overflow-hidden">
      <Sidebar vistaActiva="configuracion" onNav={onNav} onLogout={onLogout} />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="flex items-center px-margin-desktop h-16 bg-surface-container-lowest shadow-sm flex-shrink-0">
          <h2 className="font-title-md text-title-md font-black text-primary">Configuración del Sistema</h2>
        </header>

        <div className="flex-1 overflow-y-auto p-margin-desktop space-y-gutter">

          {/* Estado del Modelo */}
          <section>
            <h3 className="font-headline-lg text-headline-lg text-primary mb-4">Estado del Modelo ML</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              <div className="bg-white rounded-xl border border-outline-variant/30 shadow-sm p-6">
                {loading ? (
                  <div className="flex items-center gap-3 text-on-surface-variant">
                    <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite' }}>sync</span>
                    Consultando modelo…
                  </div>
                ) : modelo ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${modelo.modelo_entrenado ? 'bg-green-500' : 'bg-orange-400'} animate-pulse`}/>
                      <span className="font-medium text-on-surface">
                        {modelo.modelo_entrenado ? 'Modelo entrenado y activo' : 'Modelo no entrenado'}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-surface-container-low rounded-lg p-3">
                        <p className="text-on-surface-variant text-xs mb-1">Algoritmo</p>
                        <p className="font-bold text-primary">{modelo.tipo_modelo}</p>
                      </div>
                      <div className="bg-surface-container-low rounded-lg p-3">
                        <p className="text-on-surface-variant text-xs mb-1">Estado</p>
                        <p className="font-bold text-on-surface">{modelo.mensaje}</p>
                      </div>
                    </div>
                    <button
                      onClick={handleEntrenar}
                      disabled={entrenar === 'loading'}
                      className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50">
                      <span className="material-symbols-outlined text-[18px]"
                        style={entrenar === 'loading' ? { animation: 'spin 1s linear infinite' } : {}}>
                        {entrenar === 'ok' ? 'check_circle' : entrenar === 'error' ? 'error' : 'model_training'}
                      </span>
                      {entrenar === 'loading' ? 'Entrenando…' : entrenar === 'ok' ? 'Modelo actualizado' : entrenar === 'error' ? 'Error al entrenar' : 'Reentrenar Modelo'}
                    </button>
                    {entrenar === 'ok' && (
                      <p className="text-xs text-green-600 text-center">✓ Modelo reentrenado exitosamente con el dataset sintético.</p>
                    )}
                  </div>
                ) : (
                  <p className="text-on-surface-variant text-sm">No se pudo conectar con el modelo.</p>
                )}
              </div>

              {/* Info del sistema */}
              <div className="bg-white rounded-xl border border-outline-variant/30 shadow-sm p-6">
                <h4 className="font-medium text-on-surface mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">info</span>
                  Información del Sistema
                </h4>
                <div className="space-y-2">
                  {INFO_SISTEMA.map(({ label, value }) => (
                    <div key={label} className="flex justify-between py-2 border-b border-outline-variant/15 text-sm">
                      <span className="text-on-surface-variant">{label}</span>
                      <span className="font-medium text-on-surface text-right">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Señales de fraude configuradas */}
          <section>
            <h3 className="font-headline-lg text-headline-lg text-primary mb-4">Señales de Riesgo Configuradas</h3>
            <div className="bg-white rounded-xl border border-outline-variant/30 shadow-sm overflow-hidden">
              <div className="p-4 bg-surface-container-low border-b border-outline-variant/20">
                <p className="text-sm text-on-surface-variant">
                  Estas señales son las reglas activas en el motor de detección. El score final combina estas reglas (60%) con el modelo XGBoost (40%).
                </p>
              </div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low/30">
                    <th className="px-5 py-3 font-label-sm text-label-sm text-on-surface-variant">Código</th>
                    <th className="px-5 py-3 font-label-sm text-label-sm text-on-surface-variant">Señal de Riesgo</th>
                    <th className="px-5 py-3 font-label-sm text-label-sm text-on-surface-variant">Puntuación máx.</th>
                    <th className="px-5 py-3 font-label-sm text-label-sm text-on-surface-variant">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/15">
                  {SEÑALES_FRAUDE.map(s => (
                    <tr key={s.codigo} className="hover:bg-surface-container-low/40 transition-colors">
                      <td className="px-5 py-3">
                        <span className="font-label-sm text-label-sm font-bold text-primary bg-surface-container px-2 py-0.5 rounded">{s.codigo}</span>
                      </td>
                      <td className="px-5 py-3 text-sm text-on-surface">{s.señal}</td>
                      <td className="px-5 py-3 text-sm font-bold text-on-surface">{s.max}</td>
                      <td className="px-5 py-3">
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 px-2.5 py-1 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500"/>
                          Activa
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Aviso ético */}
          <section className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-5">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-primary mt-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>policy</span>
              <div>
                <h4 className="font-medium text-on-surface mb-2">Principios de uso ético</h4>
                <ul className="text-sm text-on-surface-variant space-y-1">
                  <li>• Este sistema genera <strong>alertas de revisión</strong>, no acusaciones de fraude.</li>
                  <li>• Toda decisión final debe ser tomada por un <strong>analista humano calificado</strong>.</li>
                  <li>• Se trabaja exclusivamente con <strong>datos sintéticos</strong>, sin información personal real.</li>
                  <li>• El score es una herramienta de <strong>priorización</strong>, no de condena automática.</li>
                </ul>
              </div>
            </div>
          </section>
        </div>

        <footer className="py-3 px-margin-desktop flex justify-between items-center bg-surface-dim border-t border-outline-variant flex-shrink-0">
          <p className="text-xs text-on-surface-variant">Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.</p>
        </footer>
      </main>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
