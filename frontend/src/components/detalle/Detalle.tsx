import './Detalle.css'

const factoresRiesgo = [
  { icon: 'timer_off', texto: 'Reporte tardío > 30 días', pts: '+25 pts', color: '#ba1a1a', bg: 'rgba(255,218,214,0.2)', border: '#ba1a1a' },
  { icon: 'hub', texto: 'Proveedor recurrente en alertas', pts: '+35 pts', color: '#ba1a1a', bg: 'rgba(255,218,214,0.1)', border: 'rgba(186,26,26,0.5)' },
  { icon: 'payments', texto: 'Monto superior al promedio (2.5x)', pts: '+15 pts', color: '#434652', bg: 'rgba(222,233,252,0.3)', border: '#c4c6d3' },
  { icon: 'distance', texto: 'Geolocalización inconsistente', pts: '+10 pts', color: '#434652', bg: 'rgba(222,233,252,0.3)', border: '#c4c6d3' },
]

const timeline = [
  { titulo: 'Ocurrencia del Siniestro', fecha: '12 Abr, 2024 - 14:30 hrs', desc: 'Choque lateral reportado por el asegurado.', color: '#002662', textColor: '#121c2a' },
  { titulo: 'Reporte a la Aseguradora', fecha: '14 May, 2024 - 09:15 hrs', desc: 'Alerta: Retraso de 32 días en la notificación.', color: 'rgba(0,38,98,0.4)', textColor: '#ba1a1a' },
  { titulo: 'Inspección de Taller', fecha: '16 May, 2024 - 11:00 hrs', desc: 'Ingreso a Taller "AutoExpert" (Flag: Reincidencia).', color: 'rgba(0,38,98,0.4)', textColor: '#121c2a' },
  { titulo: 'Detección de Anomalía', fecha: '18 May, 2024 - 10:45 hrs', desc: 'AI FraudIA activa bloqueo preventivo del pago.', color: '#ba1a1a', textColor: '#ba1a1a' },
]

const documentos = [
  { icon: 'check_circle', iconColor: '#0053cf', texto: 'Factura de Reparación', status: 'Completo', statusColor: '#434652' },
  { icon: 'error', iconColor: '#ba1a1a', texto: 'Fotografías del Siniestro', status: 'Inconsistente', statusColor: '#ba1a1a' },
  { icon: 'check_circle', iconColor: '#0053cf', texto: 'Declaración Jurada', status: 'Completo', statusColor: '#434652' },
  { icon: 'pending', iconColor: '#747783', texto: 'Reporte Policial', status: 'No requerido', statusColor: '#434652' },
]

export default function Detalle({ onVolver }: { onVolver: () => void }) {
  return (
    <div className="detalle-layout">

      {/* Header */}
      <header className="detalle-header">
        <div className="detalle-header-left">
          <span className="material-symbols-outlined" style={{ color: '#002662' }}>menu</span>
          <span style={{ fontSize: 18, fontWeight: 900, color: '#002662' }}>FraudIA Claims</span>
          <div className="detalle-nav-tabs" style={{ marginLeft: '1rem' }}>
            <button className="tab-inactive">Dashboard</button>
            <button className="tab-active">Gestión de Casos</button>
            <button className="tab-inactive">Reportes</button>
          </div>
        </div>
        <div className="detalle-header-right">
          <span className="material-symbols-outlined" style={{ color: '#434652', cursor: 'pointer' }}>notifications</span>
          <span className="material-symbols-outlined" style={{ color: '#434652', cursor: 'pointer' }}>help</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: 12, color: '#434652', fontFamily: 'JetBrains Mono' }}>Analista de Riesgos</span>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 12 }}>A</div>
          </div>
        </div>
      </header>

      <div className="detalle-body">

        {/* Sidebar */}
        <aside className="detalle-sidebar">
          <h2>FraudIA</h2>
          <p>Intelligent Detector</p>
          <a href="#" className="sidebar-nav-link">
            <span className="material-symbols-outlined">dashboard</span>
            Dashboard
          </a>
          <a href="#" className="sidebar-nav-link active">
            <span className="material-symbols-outlined">assignment</span>
            Gestión de Casos
          </a>
          <a href="#" className="sidebar-nav-link">
            <span className="material-symbols-outlined">analytics</span>
            Reportes
          </a>
          <a href="#" className="sidebar-nav-link">
            <span className="material-symbols-outlined">settings</span>
            Configuración
          </a>
        </aside>

        {/* Main */}
        <main className="detalle-main">

          {/* Breadcrumb */}
          <nav className="breadcrumb">
            <span>Casos</span>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
            <span className="breadcrumb-active">Siniestro #CLM-98234</span>
          </nav>

          {/* Hero */}
          <section className="hero-grid">
            <div className="hero-card">
              <div className="hero-card-left">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="badge-alto-riesgo">
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                    ALTO RIESGO
                  </span>
                  <h1 className="hero-title">Detalle de Siniestro</h1>
                </div>
                <p className="hero-subtitle">
                  Siniestro automotriz reportado el 14 de Mayo, 2024. Analizado mediante motor neuronal v4.2.
                </p>
                <div className="hero-actions">
                  <button className="btn-primary">Iniciar Auditoría</button>
<button className="btn-outline" onClick={onVolver}>Cerrar Caso</button>
                </div>
              </div>

              {/* Score */}
              <div className="score-circle">
                <div style={{ position: 'relative', width: 160, height: 160 }}>
                  <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="80" cy="80" r="70" fill="transparent" stroke="#ffdad6" strokeWidth="12" />
                    <circle cx="80" cy="80" r="70" fill="transparent" stroke="#ba1a1a" strokeWidth="12"
                      strokeDasharray="440" strokeDashoffset="66" strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontFamily: 'Hanken Grotesk', fontSize: 48, fontWeight: 700, color: '#ba1a1a', lineHeight: 1 }}>85</span>
                    <span style={{ fontSize: 12, color: '#434652', fontFamily: 'JetBrains Mono' }}>/ 100</span>
                  </div>
                </div>
                <span style={{ fontSize: 18, fontWeight: 600, color: '#ba1a1a' }}>Puntuación de Riesgo</span>
              </div>
            </div>

            {/* AI Card */}
            <div className="ai-card">
              <div className="ai-card-header">
                <span className="material-symbols-outlined">auto_awesome</span>
                Explicación IA
              </div>
              <p>
                "Este caso fue marcado como alto riesgo debido a la combinación de un monto inusual con una red de proveedores previamente vinculados a inconsistencias. Se detectó una demora de 32 días en el reporte, lo cual correlaciona históricamente con un 78% de probabilidad de fraude por manipulación de evidencia."
              </p>
              <div className="ai-card-footer">
                <span>Confianza del modelo: 94%</span>
                <span className="material-symbols-outlined" style={{ fontSize: 18, cursor: 'help' }}>info</span>
              </div>
            </div>
          </section>

          {/* Risk Factors & Timeline */}
          <div className="two-col-grid">

            {/* Risk Factors */}
            <div className="section-card">
              <h2>
                <span className="material-symbols-outlined" style={{ color: '#ba1a1a' }}>list_alt</span>
                Factores de Riesgo Detectados
              </h2>
              {factoresRiesgo.map((f, i) => (
                <div key={i} className="risk-factor" style={{ background: f.bg, borderLeft: `4px solid ${f.border}` }}>
                  <div className="risk-factor-left">
                    <span className="material-symbols-outlined" style={{ color: f.color }}>{f.icon}</span>
                    {f.texto}
                  </div>
                  <span className="risk-factor-pts" style={{ color: f.color }}>{f.pts}</span>
                </div>
              ))}
            </div>

            {/* Timeline */}
            <div className="section-card">
              <h2>
                <span className="material-symbols-outlined" style={{ color: '#002662' }}>timeline</span>
                Línea de Tiempo del Evento
              </h2>
              <div className="timeline">
                {timeline.map((item, i) => (
                  <div key={i} className="timeline-item">
                    <span className="timeline-dot" style={{ background: item.color }} />
                    <h4 style={{ color: item.textColor }}>{item.titulo}</h4>
                    <p className="time" style={{ color: item.textColor === '#ba1a1a' ? '#ba1a1a' : '#434652' }}>{item.fecha}</p>
                    <p style={{ color: item.textColor }}>{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Network & Documents */}
          <div className="three-col-grid">

            {/* Network Graph */}
            <div className="section-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0 }}>
                  <span className="material-symbols-outlined" style={{ color: '#002662' }}>account_tree</span>
                  Red de Relaciones (Grafo)
                </h2>
                <button style={{ background: 'none', border: 'none', color: '#002662', cursor: 'pointer', fontSize: 12, fontFamily: 'JetBrains Mono', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>zoom_in</span>
                  Expandir Mapa
                </button>
              </div>
              <div className="network-area">
                <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                  <line x1="50%" y1="50%" x2="25%" y2="30%" stroke="#002662" strokeWidth="2" strokeDasharray="5,5" />
                  <line x1="50%" y1="50%" x2="75%" y2="35%" stroke="#ba1a1a" strokeWidth="2" />
                  <line x1="75%" y1="35%" x2="80%" y2="70%" stroke="#ba1a1a" strokeWidth="2" />
                </svg>

                {/* Nodo central */}
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', boxShadow: '0 4px 12px rgba(0,38,98,0.3)' }}>
                    <span className="material-symbols-outlined">person</span>
                  </div>
                  <span style={{ background: '#fff', padding: '2px 8px', borderRadius: 4, marginTop: 8, fontSize: 12, fontFamily: 'JetBrains Mono', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>Asegurado</span>
                </div>

                {/* Nodo hogar */}
                <div style={{ position: 'absolute', top: '30%', left: '25%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#fff', border: '2px solid #002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#002662' }}>
                    <span className="material-symbols-outlined">home</span>
                  </div>
                  <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono', marginTop: 4, color: '#434652' }}>Hogar Decl.</span>
                </div>

                {/* Nodo taller */}
                <div style={{ position: 'absolute', top: '35%', left: '75%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#ffdad6', border: '2px solid #ba1a1a', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ba1a1a' }}>
                    <span className="material-symbols-outlined">build</span>
                  </div>
                  <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono', marginTop: 4, color: '#ba1a1a', fontWeight: 700 }}>AutoExpert</span>
                </div>

                {/* Nodo caso */}
                <div style={{ position: 'absolute', top: '70%', left: '80%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#fff', border: '2px solid #c4c6d3', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#434652' }}>
                    <span className="material-symbols-outlined">assignment</span>
                  </div>
                  <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono', marginTop: 4, color: '#434652' }}>Caso #CLM-882</span>
                </div>
              </div>
            </div>

            {/* Documents */}
            <div className="section-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <h2>
                <span className="material-symbols-outlined" style={{ color: '#002662' }}>task_alt</span>
                Estatus Documental
              </h2>
              {documentos.map((doc, i) => (
                <div key={i} className="doc-item">
                  <div className="doc-item-left">
                    <span className="material-symbols-outlined" style={{ color: doc.iconColor }}>{doc.icon}</span>
                    {doc.texto}
                  </div>
                  <span className="doc-status" style={{ color: doc.statusColor, fontWeight: doc.statusColor === '#ba1a1a' ? 700 : 400 }}>
                    {doc.status}
                  </span>
                </div>
              ))}
              <div className="auditor-note">
                <p>Nota del Auditor:</p>
                <p>"Las fotos presentan metadatos de ubicación que no coinciden con la dirección del reporte. Solicitar aclaración."</p>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="detalle-footer">
        <span style={{ fontWeight: 600, color: '#121c2a' }}>FraudIA Claims</span>
        <p style={{ margin: 0 }}>Este sistema sugiere revisión, no determina fraude. © 2024 FraudIA Claims.</p>
        <div>
          <a href="#">Ética AI</a>
          <a href="#">Soporte Técnico</a>
          <a href="#">Documentación</a>
        </div>
      </footer>

      {/* AI FAB */}
      <button className="ai-fab">
        <span className="material-symbols-outlined" style={{ fontSize: 28 }}>smart_toy</span>
        <span className="ai-fab-dot" />
      </button>
    </div>
  )
}
