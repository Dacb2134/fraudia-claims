import './Dashboard.css'
import { useDashboard } from '../../controllers/useDashboard'
import { obtenerSesion } from '../../services/authService'

const nivelColor = { ROJO: '#ba1a1a', AMARILLO: '#FFB800', VERDE: '#00A344' }
const nivelLabel = { ROJO: 'Alto', AMARILLO: 'Medio', VERDE: 'Bajo' }
const nivelBadge = { ROJO: 'badge-alto', AMARILLO: 'badge-medio', VERDE: 'badge-bajo' }
const nivelIcon  = { ROJO: 'report', AMARILLO: 'schedule', VERDE: 'check_circle' }

function formatMonto(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

export default function Dashboard({
  onVerDetalle,
  onLogout,
}: {
  onVerDetalle: (id: string) => void
  onLogout: () => void
}) {
  const { stats, casos, filtro, setFiltro, loading, error } = useDashboard()
  const usuario = obtenerSesion()

  const total    = stats?.resumen.total_siniestros ?? 0
  const pctRojo  = total ? ((stats?.semaforo.rojo.total    ?? 0) / total * 100).toFixed(1) : '0'
  const pctAma   = total ? ((stats?.semaforo.amarillo.total ?? 0) / total * 100).toFixed(1) : '0'
  const pctVerde = total ? ((stats?.semaforo.verde.total   ?? 0) / total * 100).toFixed(1) : '0'

  // Donut SVG
  const circumference = 2 * Math.PI * 70
  const rojoOffset    = circumference * (1 - (stats?.semaforo.rojo.total    ?? 0) / (total || 1))
  const amarOffset    = circumference * (1 - (stats?.semaforo.amarillo.total ?? 0) / (total || 1))

  const inicialNombre = usuario?.nombre?.charAt(0).toUpperCase() ?? 'A'
  const rolLabel      = usuario?.rol === 'admin' ? 'Administrador'
    : usuario?.rol === 'supervisor' ? 'Supervisor' : 'Analista de Riesgos'

  return (
    <div className="dashboard-layout">

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>FraudIA Claims</h2>
          <p>Intelligent Detector</p>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {([
            { icon: 'dashboard', label: 'Dashboard', active: true as boolean },
            { icon: 'assignment', label: 'Gestión de Casos', active: false as boolean },
            { icon: 'analytics', label: 'Reportes', active: false as boolean },
            { icon: 'settings', label: 'Configuración', active: false as boolean },
          ]).map(({ icon, label, active }) => (
            <a key={label} href="#" className={`nav-link${active ? ' active' : ''}`}>
              <span className="material-symbols-outlined">{icon}</span>
              {label}
            </a>
          ))}
          <button onClick={onLogout} className="nav-link" style={{
            background: 'none', border: 'none', cursor: 'pointer',
            width: '100%', textAlign: 'left', color: '#ba1a1a', marginTop: '1rem',
          }}>
            <span className="material-symbols-outlined">logout</span>
            Cerrar Sesión
          </button>
        </nav>
        <div className="ai-status">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span className="material-symbols-outlined" style={{ color: '#002662', fontSize: 18 }}>smart_toy</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#002662', fontFamily: 'JetBrains Mono' }}>AI Status</span>
          </div>
          <p style={{ fontSize: 12, color: '#434652', margin: 0 }}>Gemini · Motor v4.2 Activo</p>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">

        {/* Header */}
        <header className="top-header">
          <h1 className="header-title">Resumen Ejecutivo</h1>
          <div className="header-right">
            <div className="search-bar">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>search</span>
              <input placeholder="Buscar siniestro..." type="text" />
            </div>
            <button className="icon-btn">
              <span className="material-symbols-outlined">notifications</span>
              <span className="notif-dot" />
            </button>
            <div className="user-info">
              <div style={{ textAlign: 'right' }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: '#002662', margin: 0 }}>{usuario?.nombre ?? rolLabel}</p>
                <p style={{ fontSize: 12, color: '#434652', margin: 0, opacity: 0.7 }}>{rolLabel}</p>
              </div>
              <div style={{
                width: 40, height: 40, borderRadius: '50%', background: '#002662',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontWeight: 700,
              }}>{inicialNombre}</div>
            </div>
          </div>
        </header>

        <div className="content-area">

          {error && (
            <div style={{ padding: '1rem 1.5rem', background: '#ffdad6', borderRadius: 8, color: '#ba1a1a', fontSize: 14 }}>
              <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', marginRight: 8 }}>error</span>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, gap: '1rem', color: '#434652' }}>
              <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 32, color: '#002662' }}>sync</span>
              Cargando datos...
            </div>
          ) : (
            <>
              {/* KPI Cards */}
              <section className="kpi-grid">
                <div className="kpi-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="kpi-label">Total Siniestros</span>
                    <span className="material-symbols-outlined" style={{ color: 'rgba(0,38,98,0.3)' }}>description</span>
                  </div>
                  <span className="kpi-value">{total.toLocaleString()}</span>
                  <span className="kpi-sub">Score promedio: {stats?.resumen.score_promedio}</span>
                </div>

                <div className="kpi-card" style={{ borderBottom: '4px solid #ba1a1a' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="kpi-label">% Alto Riesgo</span>
                    <span className="material-symbols-outlined" style={{ color: '#ba1a1a' }}>warning</span>
                  </div>
                  <span className="kpi-value" style={{ color: '#ba1a1a' }}>{pctRojo}%</span>
                  <span className="kpi-sub">{stats?.semaforo.rojo.total} casos críticos</span>
                </div>

                <div className="kpi-card" style={{ borderBottom: '4px solid #FFB800' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="kpi-label">% Medio Riesgo</span>
                    <span className="material-symbols-outlined" style={{ color: '#FFB800' }}>error_outline</span>
                  </div>
                  <span className="kpi-value" style={{ color: '#FFB800' }}>{pctAma}%</span>
                  <span className="kpi-sub">Requieren revisión</span>
                </div>

                <div className="kpi-card" style={{ borderBottom: '4px solid #00A344' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="kpi-label">% Bajo Riesgo</span>
                    <span className="material-symbols-outlined" style={{ color: '#00A344' }}>check_circle</span>
                  </div>
                  <span className="kpi-value" style={{ color: '#00A344' }}>{pctVerde}%</span>
                  <span className="kpi-sub">Procesamiento fluido</span>
                </div>

                <div className="kpi-card" style={{ background: '#003a8f' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="kpi-label" style={{ color: '#86a9ff' }}>Monto en Riesgo</span>
                    <span className="material-symbols-outlined" style={{ color: '#86a9ff' }}>savings</span>
                  </div>
                  <span className="kpi-value" style={{ color: '#fff' }}>
                    {formatMonto(stats?.resumen.monto_total_riesgo ?? 0)}
                  </span>
                  <span style={{ fontSize: 12, color: '#86a9ff', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: 4, display: 'inline-block' }}>
                    Prevención IA
                  </span>
                </div>
              </section>

              {/* Charts */}
              <section className="charts-grid">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

                  {/* Donut distribución */}
                  <div className="chart-card">
                    <h3>Distribución de Riesgo</h3>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
                      <div style={{ position: 'relative', width: 160, height: 160 }}>
                        <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                          <circle cx="80" cy="80" r="70" fill="transparent" stroke="#d9e3f6" strokeWidth="20" />
                          <circle cx="80" cy="80" r="70" fill="transparent" stroke="#ba1a1a" strokeWidth="20"
                            strokeDasharray={circumference} strokeDashoffset={rojoOffset} />
                          <circle cx="80" cy="80" r="70" fill="transparent" stroke="#FFB800" strokeWidth="20"
                            strokeDasharray={circumference} strokeDashoffset={amarOffset} />
                        </svg>
                        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                          <span style={{ fontSize: 18, fontWeight: 700, color: '#002662' }}>{total.toLocaleString()}</span>
                          <span style={{ fontSize: 10, color: '#434652' }}>CASOS</span>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: 11 }}>
                      {[
                        { color: '#ba1a1a', label: `Rojo ${pctRojo}%` },
                        { color: '#FFB800', label: `Amarillo ${pctAma}%` },
                        { color: '#00A344', label: `Verde ${pctVerde}%` },
                      ].map(({ color, label }) => (
                        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                          <span style={{ color: '#434652' }}>{label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Por ramo */}
                  <div className="chart-card">
                    <h3>Siniestros por Ramo</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                      {stats?.por_ramo.map((r) => {
                        const pct = total ? Math.round(r.total / total * 100) : 0
                        return (
                          <div key={r.ramo}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                              <span style={{ color: '#434652' }}>{r.ramo}</span>
                              <span style={{ fontWeight: 700, color: '#002662' }}>{r.total}</span>
                            </div>
                            <div style={{ background: '#d9e3f6', height: 6, borderRadius: 999, overflow: 'hidden' }}>
                              <div style={{ width: `${pct}%`, height: '100%', background: '#002662' }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Top proveedores */}
                  <div className="chart-card" style={{ gridColumn: 'span 2' }}>
                    <h3>Top Proveedores bajo Alerta</h3>
                    {stats?.top_proveedores.map((p) => {
                      const pct = p.total_alertas ? Math.round(p.alertas_rojas / p.total_alertas * 100) : 0
                      return (
                        <div key={p.proveedor} style={{ marginBottom: '1rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                            <span>{p.proveedor}</span>
                            <span style={{ fontWeight: 700 }}>
                              {p.alertas_rojas} alertas rojas / {p.total_alertas} total
                            </span>
                          </div>
                          <div style={{ background: '#d9e3f6', height: 8, borderRadius: 999, overflow: 'hidden' }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: pct > 60 ? '#ba1a1a' : '#0053cf' }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Por sucursal */}
                <div className="chart-card" style={{ display: 'flex', flexDirection: 'column' }}>
                  <h3>Siniestros por Sucursal</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                    {stats?.por_sucursal.slice(0, 6).map((s) => (
                      <div key={s.sucursal} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                        <span style={{ color: '#434652' }}>{s.sucursal}</span>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, color: '#002662' }}>{s.total}</span>
                          {s.rojos > 0 && (
                            <span style={{ color: '#ba1a1a', fontSize: 11 }}>({s.rojos} críticos)</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Top asegurados */}
                  {stats?.top_asegurados && stats.top_asegurados.length > 0 && (
                    <>
                      <h3 style={{ marginTop: '1.5rem' }}>Top Asegurados</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {stats.top_asegurados.slice(0, 5).map((a) => (
                          <div key={a.id_asegurado} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span style={{ color: '#434652', fontFamily: 'JetBrains Mono' }}>{a.id_asegurado}</span>
                            <span style={{ fontWeight: 700, color: a.score_max >= 76 ? '#ba1a1a' : '#002662' }}>
                              Score {a.score_max} · {a.total_siniestros} casos
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </section>

              {/* Tabla de siniestros */}
              <section className="table-section">
                <div className="table-header">
                  <div>
                    <h3>Casos Priorizados por la IA</h3>
                    <p>Ordenado por severidad de fraude potencial</p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {([undefined, 'ROJO', 'AMARILLO', 'VERDE'] as const).map((n) => (
                      <button
                        key={n ?? 'todos'}
                        onClick={() => setFiltro(n)}
                        style={{
                          padding: '6px 14px', border: 'none', borderRadius: 8,
                          cursor: 'pointer', fontSize: 12,
                          background: filtro === n ? '#002662' : '#e6eeff',
                          color: filtro === n ? '#fff' : '#002662', fontWeight: 600,
                        }}
                      >
                        {n ?? 'Todos'}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>ID Siniestro</th>
                        <th>Score</th>
                        <th>Nivel</th>
                        <th>Ramo</th>
                        <th>Monto</th>
                        <th>Sucursal</th>
                        <th>Estado</th>
                        <th>Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {casos.map((caso) => (
                        <tr key={caso.id_siniestro}>
                          <td style={{ fontWeight: 700, fontFamily: 'JetBrains Mono', fontSize: 12 }}>
                            {caso.id_siniestro}
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <div style={{ width: 48, height: 6, background: '#d9e3f6', borderRadius: 999, overflow: 'hidden' }}>
                                <div style={{ width: `${caso.score_riesgo}%`, height: '100%', background: nivelColor[caso.nivel_riesgo] }} />
                              </div>
                              <span style={{ fontSize: 12, fontWeight: 700, color: nivelColor[caso.nivel_riesgo] }}>
                                {caso.score_riesgo}
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className={`badge ${nivelBadge[caso.nivel_riesgo]}`}>
                              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                                {nivelIcon[caso.nivel_riesgo]}
                              </span>
                              {nivelLabel[caso.nivel_riesgo]}
                            </span>
                          </td>
                          <td style={{ color: '#434652' }}>{caso.ramo}</td>
                          <td style={{ fontWeight: 600 }}>{formatMonto(caso.monto_reclamado)}</td>
                          <td style={{ color: '#434652', fontSize: 12 }}>{caso.sucursal}</td>
                          <td style={{ fontSize: 12, color: '#434652' }}>{caso.estado}</td>
                          <td>
                            <button className="btn-ver" onClick={() => onVerDetalle(caso.id_siniestro)}>
                              Ver Detalles
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #c4c6d3', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#eff4ff' }}>
                  <span style={{ fontSize: 12, color: '#434652' }}>
                    Mostrando {casos.length} casos
                    {filtro ? ` · Filtro: ${filtro}` : ' · Todos los niveles'}
                  </span>
                  <span style={{ fontSize: 12, color: '#434652', fontFamily: 'JetBrains Mono' }}>
                    Total en sistema: {total.toLocaleString()}
                  </span>
                </div>
              </section>
            </>
          )}
        </div>

        <footer className="dashboard-footer">
          <p style={{ margin: 0 }}>Este sistema sugiere revisión, no determina fraude. © 2024 FraudIA Claims.</p>
          <div>
            <a href="#">Ética AI</a>
            <a href="#">Soporte Técnico</a>
          </div>
        </footer>
      </main>
    </div>
  )
}
