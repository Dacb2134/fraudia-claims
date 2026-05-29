import './Dashboard.css'

const casos = [
  { id: '#SN-9821', score: 94, nivel: 'Muy Alto', motivo: 'Posible colisión simulada (Fotos editadas)', color: '#ba1a1a' },
  { id: '#SN-9815', score: 88, nivel: 'Muy Alto', motivo: 'Siniestro duplicado en otra compañía', color: '#ba1a1a' },
  { id: '#SN-9802', score: 56, nivel: 'Medio', motivo: 'Mecánica de accidente poco clara', color: '#FFB800' },
]

export default function Dashboard({ onVerDetalle, onLogout }: { onVerDetalle: () => void, onLogout: () => void }) {
  return (
    <div className="dashboard-layout">

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>FraudIA Claims</h2>
          <p>Intelligent Detector</p>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <a href="#" className="nav-link active">
            <span className="material-symbols-outlined">dashboard</span>
            Dashboard
          </a>
          <a href="#" className="nav-link">
            <span className="material-symbols-outlined">assignment</span>
            Gestión de Casos
          </a>
          <a href="#" className="nav-link">
            <span className="material-symbols-outlined">analytics</span>
            Reportes
          </a>
          <a href="#" className="nav-link">
            <span className="material-symbols-outlined">settings</span>
            Configuración
          </a>
          <button onClick={onLogout} className="nav-link" style={{ background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', color: '#ba1a1a' }}>
  <span className="material-symbols-outlined">logout</span>
  Cerrar Sesión
</button>
        </nav>
        <div className="ai-status">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span className="material-symbols-outlined" style={{ color: '#002662', fontSize: 18 }}>smart_toy</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#002662', fontFamily: 'JetBrains Mono' }}>AI Status</span>
          </div>
          <p style={{ fontSize: 12, color: '#434652', margin: 0 }}>Model v4.2 Active</p>
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
            <button className="icon-btn">
              <span className="material-symbols-outlined">help</span>
            </button>
            <div className="user-info">
              <div style={{ textAlign: 'right' }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: '#002662', margin: 0 }}>Analista de Riesgos</p>
                <p style={{ fontSize: 12, color: '#434652', margin: 0, opacity: 0.7 }}>Sénior</p>
              </div>
              <div style={{
                width: 40, height: 40, borderRadius: '50%',
                background: '#002662', display: 'flex',
                alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700
              }}>A</div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="content-area">

          {/* KPI Cards */}
          <section className="kpi-grid">
            <div className="kpi-card">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="kpi-label">Total Siniestros</span>
                <span className="material-symbols-outlined" style={{ color: 'rgba(0,38,98,0.3)' }}>description</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
                <span className="kpi-value">1,284</span>
                <span style={{ fontSize: 12, color: '#0053cf', fontWeight: 700, marginBottom: 8 }}>↑ 12%</span>
              </div>
              <span className="kpi-sub">vs. mes anterior</span>
            </div>

            <div className="kpi-card" style={{ borderBottom: '4px solid #ba1a1a' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="kpi-label">% Alto Riesgo</span>
                <span className="material-symbols-outlined" style={{ color: '#ba1a1a' }}>warning</span>
              </div>
              <span className="kpi-value" style={{ color: '#ba1a1a' }}>8.4%</span>
              <span className="kpi-sub">108 casos críticos</span>
            </div>

            <div className="kpi-card" style={{ borderBottom: '4px solid #FFB800' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="kpi-label">% Medio Riesgo</span>
                <span className="material-symbols-outlined" style={{ color: '#FFB800' }}>error_outline</span>
              </div>
              <span className="kpi-value" style={{ color: '#FFB800' }}>15.2%</span>
              <span className="kpi-sub">Requieren revisión</span>
            </div>

            <div className="kpi-card" style={{ borderBottom: '4px solid #00A344' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="kpi-label">% Bajo Riesgo</span>
                <span className="material-symbols-outlined" style={{ color: '#00A344' }}>check_circle</span>
              </div>
              <span className="kpi-value" style={{ color: '#00A344' }}>76.4%</span>
              <span className="kpi-sub">Procesamiento fluido</span>
            </div>

            <div className="kpi-card" style={{ background: '#003a8f' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="kpi-label" style={{ color: '#86a9ff' }}>Ahorro Estimado</span>
                <span className="material-symbols-outlined" style={{ color: '#86a9ff' }}>savings</span>
              </div>
              <span className="kpi-value" style={{ color: '#fff' }}>$4.2M</span>
              <span style={{ fontSize: 12, color: '#86a9ff', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: 4, display: 'inline-block' }}>Prevención IA</span>
            </div>
          </section>

          {/* Charts */}
          <section className="charts-grid">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="chart-card">
                <h3>Distribución de Riesgo</h3>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
                  <div style={{ position: 'relative', width: 160, height: 160 }}>
                    <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                      <circle cx="80" cy="80" r="70" fill="transparent" stroke="#d9e3f6" strokeWidth="20" />
                      <circle cx="80" cy="80" r="70" fill="transparent" stroke="#ba1a1a" strokeWidth="20" strokeDasharray="440" strokeDashoffset="110" />
                      <circle cx="80" cy="80" r="70" fill="transparent" stroke="#0053cf" strokeWidth="20" strokeDasharray="440" strokeDashoffset="250" />
                    </svg>
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: 18, fontWeight: 700, color: '#002662' }}>1.2k</span>
                      <span style={{ fontSize: 10, color: '#434652' }}>CASOS</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="chart-card">
                <h3>Alertas por Día</h3>
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', minHeight: 200 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: 160, gap: 4, padding: '0 8px' }}>
                    {[
                      { h: '25%', color: '#d9e3f6' },
                      { h: '40%', color: '#d9e3f6' },
                      { h: '75%', color: '#002662' },
                      { h: '100%', color: '#ba1a1a' },
                      { h: '80%', color: '#002662' },
                      { h: '50%', color: '#d9e3f6' },
                      { h: '33%', color: '#d9e3f6' },
                    ].map((bar, i) => (
                      <div key={i} style={{ flex: 1, height: bar.h, background: bar.color, borderRadius: '4px 4px 0 0' }} />
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', fontSize: 11, color: '#434652', fontFamily: 'JetBrains Mono' }}>
                    {['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'].map(d => <span key={d}>{d}</span>)}
                  </div>
                </div>
              </div>

              <div className="chart-card" style={{ gridColumn: 'span 2' }}>
                <h3>Top 5 Proveedores bajo Alerta</h3>
                {[
                  { nombre: 'Clínica San Juan', pct: 84, color: '#ba1a1a' },
                  { nombre: 'Talleres Unidos S.A.', pct: 62, color: '#0053cf' },
                  { nombre: 'Farmacia Vital', pct: 45, color: '#0053cf' },
                ].map((p, i) => (
                  <div key={i} style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                      <span>{p.nombre}</span>
                      <span style={{ fontWeight: 700 }}>{p.pct}% Riesgo</span>
                    </div>
                    <div style={{ background: '#d9e3f6', height: 8, borderRadius: 999, overflow: 'hidden' }}>
                      <div style={{ width: `${p.pct}%`, height: '100%', background: p.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '1.5rem', borderBottom: '1px solid #c4c6d3' }}>
                <h3 style={{ margin: 0 }}>Concentración de Siniestros</h3>
              </div>
              <div style={{ flex: 1, background: '#d0dbed', display: 'flex', alignItems: 'flex-end', minHeight: 300, position: 'relative' }}>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '0.5rem' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 48, color: '#002662', opacity: 0.3 }}>map</span>
                  <span style={{ fontSize: 12, color: '#434652' }}>Mapa geográfico</span>
                </div>
                <div style={{ margin: '1rem', background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)', padding: '1rem', borderRadius: '0.75rem', width: '100%' }}>
                  <p style={{ fontWeight: 700, fontSize: 12, color: '#002662', margin: '0 0 4px' }}>Zona Central</p>
                  <p style={{ fontSize: 12, color: '#434652', margin: 0 }}>Zona con mayor densidad de duplicados detectados por IA.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Table */}
          <section className="table-section">
            <div className="table-header">
              <div>
                <h3>Casos Priorizados por la IA</h3>
                <p>Ordenado por severidad de fraude potencial</p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: '#e6eeff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>filter_list</span>
                  Filtrar
                </button>
                <button style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: '#002662', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>download</span>
                  Exportar
                </button>
              </div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>ID Siniestro</th>
                    <th>Score Riesgo</th>
                    <th>Nivel</th>
                    <th>Motivo Principal</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {casos.map((caso) => (
                    <tr key={caso.id}>
                      <td style={{ fontWeight: 700 }}>{caso.id}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 48, height: 6, background: '#d9e3f6', borderRadius: 999, overflow: 'hidden' }}>
                            <div style={{ width: `${caso.score}%`, height: '100%', background: caso.color }} />
                          </div>
                          <span style={{ fontSize: 12, fontWeight: 700, color: caso.color }}>{caso.score}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${caso.nivel === 'Muy Alto' ? 'badge-alto' : 'badge-medio'}`}>
                          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                            {caso.nivel === 'Muy Alto' ? 'report' : 'schedule'}
                          </span>
                          {caso.nivel}
                        </span>
                      </td>
                      <td style={{ color: '#434652' }}>{caso.motivo}</td>
                      <td>
                        <button className="btn-ver" onClick={onVerDetalle}>Ver Detalles</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #c4c6d3', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#eff4ff' }}>
              <span style={{ fontSize: 12, color: '#434652' }}>Mostrando 3 de 108 casos críticos</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={{ padding: 8, border: '1px solid #c4c6d3', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>‹</button>
                <button style={{ padding: 8, border: '1px solid #c4c6d3', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>›</button>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <footer className="dashboard-footer">
          <p style={{ margin: 0 }}>Este sistema sugiere revisión, no determina fraude. © 2024 FraudIA Claims.</p>
          <div>
            <a href="#">Ética AI</a>
            <a href="#">Soporte Técnico</a>
            <a href="#">Documentación</a>
          </div>
        </footer>
      </main>

      {/* Floating AI Button */}
      <button className="ai-fab">
        <span className="material-symbols-outlined" style={{ fontSize: 28 }}>smart_toy</span>
      </button>
    </div>
  )
}
