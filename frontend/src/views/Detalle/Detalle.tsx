import { useRef, useEffect, useState } from 'react'
import './Detalle.css'
import { useSiniestroDetalle } from '../../controllers/useSiniestroDetalle'
import { obtenerSesion } from '../../services/authService'
import Sidebar from '../../components/shared/Sidebar'

function renderMarkdown(text: string): string {
  return text
    .replace(/^#### (.+)$/gm, '<h4 style="font-size:12px;font-weight:700;color:#002662;margin:8px 0 4px">$1</h4>')
    .replace(/^### (.+)$/gm,  '<h3 style="font-size:13px;font-weight:700;color:#002662;margin:10px 0 5px;border-left:3px solid #002662;padding-left:6px">$1</h3>')
    .replace(/^## (.+)$/gm,   '<h2 style="font-size:14px;font-weight:700;color:#002662;margin:12px 0 6px">$1</h2>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,     '<strong style="color:#002662">$1</strong>')
    .replace(/\*(.+?)\*/g,         '<em>$1</em>')
    .replace(/^(\d+)\. (.+)$/gm,   '<li style="display:flex;gap:6px;margin-bottom:4px"><span style="color:#002662;font-weight:700;min-width:16px;font-size:11px">$1.</span><span>$2</span></li>')
    .replace(/^[*-] (.+)$/gm,      '<li style="display:flex;gap:6px;margin-bottom:4px"><span style="color:#002662;font-weight:700">•</span><span>$1</span></li>')
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #c4c6d3;margin:8px 0"/>')
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, m => `<ul style="list-style:none;padding:0;margin:6px 0">${m}</ul>`)
    .replace(/\n{2,}/g, '</p><p style="margin:0 0 8px">')
    .replace(/`([^`]+)`/g, '<code style="background:#e6eeff;color:#002662;padding:1px 4px;border-radius:3px;font-size:11px">$1</code>')
    .replace(/^/, '<p style="margin:0 0 8px">')
    .replace(/$/, '</p>')
    .replace(/<p style="margin:0 0 8px"><\/p>/g, '')
}

const NIVEL_COLOR = { ROJO: '#ba1a1a', AMARILLO: '#FFB800', VERDE: '#00A344' }
const NIVEL_LABEL = { ROJO: 'ALTO RIESGO', AMARILLO: 'MEDIO RIESGO', VERDE: 'BAJO RIESGO' }
const NIVEL_CARD_STYLE = {
  ROJO:     { border: '1px solid #ffdad6', boxShadow: '0 0 20px rgba(186,26,26,0.15)' },
  AMARILLO: { border: '1px solid #ffe4a0', boxShadow: '0 0 20px rgba(255,184,0,0.15)' },
  VERDE:    { border: '1px solid #b8f0cd', boxShadow: '0 0 20px rgba(0,163,68,0.1)' },
}

function formatDate(d: string) {
  if (!d) return '—'
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  return dt.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatMonto(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(2)}K`
  return `$${n.toFixed(2)}`
}

export default function Detalle({
  siniestroId,
  onVolver,
  onNav,
  onLogout,
}: {
  siniestroId: string
  onVolver: () => void
  onNav?: (v: string) => void
  onLogout?: () => void
}) {
  const {
    detalle, loading, error,
    aiExplanation, aiExplLoading,
    chatOpen, setChatOpen,
    messages, chatInput, setChatInput,
    chatLoading, sendMessage,
  } = useSiniestroDetalle(siniestroId)

  const usuario    = obtenerSesion()
  const chatEndRef = useRef<HTMLDivElement>(null)
  const [auditoria,       setAuditoria]       = useState(false)
  const [auditConfirmada, setAuditConfirmada] = useState(false)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: '1rem', color: '#434652' }}>
        <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 36, color: '#002662' }}>sync</span>
        Cargando siniestro {siniestroId}...
      </div>
    )
  }

  if (error || !detalle) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: '1rem' }}>
        <span className="material-symbols-outlined" style={{ fontSize: 48, color: '#ba1a1a' }}>error</span>
        <p style={{ color: '#ba1a1a' }}>{error ?? 'Siniestro no encontrado'}</p>
        <button className="btn-outline" onClick={onVolver}>Volver al Dashboard</button>
      </div>
    )
  }

  const nivel  = detalle.score.nivel
  const score  = detalle.score.valor
  const circum = 2 * Math.PI * 70
  const offset = circum * (1 - score / 100)

  // Timeline dinámico
  const timeline = [
    {
      titulo: 'Ocurrencia del Siniestro',
      fecha:  formatDate(detalle.fecha_ocurrencia),
      desc:   `${detalle.cobertura} · Ramo ${detalle.ramo}`,
      color:  '#002662',
      textColor: '#121c2a',
    },
    {
      titulo: 'Reporte a la Aseguradora',
      fecha:  formatDate(detalle.fecha_reporte),
      desc:   detalle.dias_reporte > 30
        ? `⚠ Alerta: Retraso de ${detalle.dias_reporte} días en la notificación.`
        : `Notificación oportuna (${detalle.dias_reporte} días).`,
      color:     detalle.dias_reporte > 30 ? '#ba1a1a' : 'rgba(0,38,98,0.5)',
      textColor: detalle.dias_reporte > 30 ? '#ba1a1a' : '#121c2a',
    },
    ...(detalle.proveedor?.id ? [{
      titulo: 'Asignación de Proveedor',
      fecha:  '',
      desc:   `Proveedor: ${detalle.proveedor.id} (${detalle.proveedor.tipo ?? 'N/A'})${detalle.proveedor.en_lista_restrictiva ? ' · ⚠ En lista restrictiva' : ''}`,
      color:     detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : 'rgba(0,38,98,0.4)',
      textColor: detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#121c2a',
    }] : []),
    ...(detalle.score.calculado_en ? [{
      titulo: 'Análisis IA FraudIA',
      fecha:  formatDate(detalle.score.calculado_en),
      desc:   `Score calculado: ${score}/100 · Nivel ${nivel}`,
      color:     NIVEL_COLOR[nivel],
      textColor: NIVEL_COLOR[nivel],
    }] : []),
  ]

  // Parsear reglas_criticas (backend envía string JSON o array)
  const reglas: Array<{ regla: string; codigo: string; clasificacion: string }> = (() => {
    const raw = detalle.score.reglas_criticas
    if (!raw) return []
    if (Array.isArray(raw)) return raw as Array<{ regla: string; codigo: string; clasificacion: string }>
    try { return JSON.parse(raw as string) } catch { return [] }
  })()

  // Alertas separadas por " | "
  const alertas = detalle.score.alertas
    ? detalle.score.alertas.split('|').map(a => a.trim()).filter(Boolean)
    : []

  // Documentos
  const documentos = [
    {
      icon:        detalle.documentos_completos ? 'check_circle' : 'pending',
      iconColor:   detalle.documentos_completos ? '#0053cf' : '#747783',
      texto:       'Expediente Documental',
      status:      detalle.documentos_completos ? 'Completo' : 'Incompleto',
      statusColor: detalle.documentos_completos ? '#434652' : '#ba1a1a',
    },
    {
      icon:        detalle.tiene_doc_inconsistente ? 'error' : 'check_circle',
      iconColor:   detalle.tiene_doc_inconsistente ? '#ba1a1a' : '#0053cf',
      texto:       'Consistencia Documental',
      status:      detalle.tiene_doc_inconsistente ? 'Inconsistente' : 'Verificado',
      statusColor: detalle.tiene_doc_inconsistente ? '#ba1a1a' : '#434652',
    },
    {
      icon:        'receipt_long',
      iconColor:   '#0053cf',
      texto:       'Póliza',
      status:      `Vigente ${formatDate(detalle.poliza.fecha_inicio)} – ${formatDate(detalle.poliza.fecha_fin)}`,
      statusColor: '#434652',
    },
    {
      icon:        detalle.proveedor?.en_lista_restrictiva ? 'error' : 'check_circle',
      iconColor:   detalle.proveedor?.en_lista_restrictiva ? '#ba1a1a' : '#0053cf',
      texto:       'Estado de Proveedor',
      status:      detalle.proveedor?.en_lista_restrictiva ? 'Lista restrictiva' : 'Sin restricciones',
      statusColor: detalle.proveedor?.en_lista_restrictiva ? '#ba1a1a' : '#434652',
    },
  ]

  return (
    <div className="detalle-layout">

      {/* Header */}
      <header className="detalle-header">
        <div className="detalle-header-left">
          <button
            onClick={onVolver}
            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, color: '#434652', fontSize: 13, fontFamily: 'JetBrains Mono', padding: '6px 0' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>arrow_back</span>
            Volver
          </button>
          <span style={{ color: '#c4c6d3' }}>·</span>
          <span style={{ fontSize: 18, fontWeight: 900, color: '#002662' }}>FraudIA Claims</span>
          <span style={{ color: '#c4c6d3' }}>·</span>
          <span style={{ fontSize: 13, color: '#434652', fontFamily: 'JetBrains Mono' }}>
            Detalle — {detalle.id_siniestro}
          </span>
        </div>
        <div className="detalle-header-right">
          <span
            className="material-symbols-outlined"
            style={{ color: '#434652', cursor: 'pointer', fontSize: 22 }}
            onClick={() => onNav?.('configuracion')}
            title="Configuración">
            help
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: 12, color: '#434652', fontFamily: 'JetBrains Mono' }}>
              {usuario?.nombre ?? 'Analista'}
            </span>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 12 }}>
              {usuario?.nombre?.charAt(0).toUpperCase() ?? 'A'}
            </div>
          </div>
        </div>
      </header>

      <div className="detalle-body">

        {/* Sidebar compartido */}
        <Sidebar
          vistaActiva="casos"
          onNav={onNav ?? (() => {})}
          onLogout={onLogout ?? (() => {})}
        />

        {/* Main */}
        <main className="detalle-main">

          {/* Breadcrumb */}
          <nav className="breadcrumb">
            <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#434652', fontSize: 12, fontFamily: 'JetBrains Mono', padding: 0 }} onClick={onVolver}>
              Casos
            </button>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
            <span className="breadcrumb-active">{detalle.id_siniestro}</span>
          </nav>

          {/* Hero */}
          <section className="hero-grid">
            <div className="hero-card" style={NIVEL_CARD_STYLE[nivel]}>
              <div className="hero-card-left">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="badge-nivel" style={{ background: NIVEL_COLOR[nivel] }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                    {NIVEL_LABEL[nivel]}
                  </span>
                </div>
                <h1 className="hero-title">Detalle de Siniestro</h1>
                <p className="hero-subtitle">
                  {detalle.ramo} — {detalle.cobertura} · Sucursal {detalle.sucursal}
                </p>
                <div className="detalle-meta-grid">
                  <div className="meta-item">
                    <span className="meta-label">Asegurado</span>
                    <span className="meta-value">{detalle.id_asegurado}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Estado</span>
                    <span className="meta-value">{detalle.estado}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Monto Reclamado</span>
                    <span className="meta-value" style={{ color: '#002662', fontWeight: 700 }}>
                      {formatMonto(detalle.monto_reclamado)}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Historial Siniestros</span>
                    <span className="meta-value" style={{ color: detalle.historial_siniestros >= 3 ? '#ba1a1a' : '#121c2a' }}>
                      {detalle.historial_siniestros} previos
                    </span>
                  </div>
                </div>
                <div className="hero-actions">
                  <button className="btn-primary" onClick={() => setChatOpen(true)}>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>smart_toy</span>
                    Consultar Agente IA
                  </button>
                  <button className="btn-outline" onClick={onVolver}>Volver al Dashboard</button>
                  {!auditConfirmada ? (
                    <button
                      onClick={() => setAuditoria(true)}
                      style={{
                        padding: '10px 20px', borderRadius: 10, cursor: 'pointer', fontSize: 14, fontWeight: 600,
                        border: '1.5px solid #ba1a1a', background: 'rgba(186,26,26,0.05)', color: '#ba1a1a',
                        display: 'flex', alignItems: 'center', gap: 6,
                      }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>gavel</span>
                      Iniciar Auditoría
                    </button>
                  ) : (
                    <span style={{ fontSize: 12, color: '#00A344', fontFamily: 'JetBrains Mono', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check_circle</span>
                      Escalado a Unidad Antifraude
                    </span>
                  )}
                </div>
              </div>

              {/* Score circle */}
              <div className="score-circle">
                <div style={{ position: 'relative', width: 160, height: 160 }}>
                  <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="80" cy="80" r="70" fill="transparent" stroke={`${NIVEL_COLOR[nivel]}33`} strokeWidth="12" />
                    <circle cx="80" cy="80" r="70" fill="transparent" stroke={NIVEL_COLOR[nivel]} strokeWidth="12"
                      strokeDasharray={circum} strokeDashoffset={offset} strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontFamily: 'Hanken Grotesk', fontSize: 48, fontWeight: 700, color: NIVEL_COLOR[nivel], lineHeight: 1 }}>
                      {score}
                    </span>
                    <span style={{ fontSize: 12, color: '#434652', fontFamily: 'JetBrains Mono' }}>/ 100</span>
                  </div>
                </div>
                <span style={{ fontSize: 16, fontWeight: 600, color: NIVEL_COLOR[nivel] }}>Puntuación de Riesgo</span>
                <span style={{ fontSize: 11, color: '#434652', fontFamily: 'JetBrains Mono' }}>
                  Calculado: {formatDate(detalle.score.calculado_en ?? '')}
                </span>
              </div>
            </div>

            {/* AI Explanation Card */}
            <div className="ai-card">
              <div className="ai-card-header">
                <span className="material-symbols-outlined">auto_awesome</span>
                Explicación IA
              </div>
              {aiExplLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', opacity: 0.7 }}>
                  <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 18 }}>sync</span>
                  Analizando con Gemini...
                </div>
              ) : aiExplanation ? (
                <p>"{aiExplanation}"</p>
              ) : (
                <p style={{ opacity: 0.7 }}>
                  "Siniestro {detalle.id_siniestro} clasificado como nivel {nivel} con score {score}/100.
                  {alertas.length > 0 ? ` Alertas: ${alertas.slice(0, 2).join('; ')}.` : ''}
                  Usa el chat IA para obtener un análisis detallado."
                </p>
              )}
              <div className="ai-card-footer">
                <span>Confianza: {score}% · Gemini</span>
                <button
                  onClick={() => setChatOpen(true)}
                  style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#c6e7ff', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', fontFamily: 'JetBrains Mono' }}
                >
                  Consultar agente →
                </button>
              </div>
            </div>
          </section>

          {/* Risk Factors & Timeline */}
          <div className="two-col-grid">

            {/* Factores de riesgo */}
            <div className="section-card">
              <h2>
                <span className="material-symbols-outlined" style={{ color: '#ba1a1a' }}>list_alt</span>
                Factores de Riesgo Detectados
              </h2>

              {/* Reglas críticas (parseadas del backend) */}
              {reglas.map((r, i) => (
                <div key={i} className="risk-factor" style={{ background: 'rgba(255,218,214,0.2)', borderLeft: '4px solid #ba1a1a' }}>
                  <div className="risk-factor-left">
                    <span className="material-symbols-outlined" style={{ color: '#ba1a1a' }}>report</span>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#ba1a1a', fontWeight: 700 }}>{r.codigo}</span>
                      <span style={{ fontSize: 13 }}>{r.regla}</span>
                    </div>
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#ba1a1a' }}>{r.clasificacion}</span>
                </div>
              ))}

              {/* Alertas del motor de reglas */}
              {alertas.map((alerta, i) => (
                <div key={`a-${i}`} className="risk-factor" style={{ background: 'rgba(222,233,252,0.3)', borderLeft: '4px solid #c4c6d3' }}>
                  <div className="risk-factor-left">
                    <span className="material-symbols-outlined" style={{ color: '#434652' }}>warning</span>
                    <span style={{ fontSize: 13 }}>{alerta}</span>
                  </div>
                </div>
              ))}

              {alertas.length === 0 && reglas.length === 0 && (
                <p style={{ color: '#434652', fontSize: 13 }}>No se detectaron alertas críticas.</p>
              )}

              {/* Info del proveedor */}
              {detalle.proveedor?.pct_casos_observados > 0 && (
                <div className="risk-factor" style={{ background: 'rgba(222,233,252,0.3)', borderLeft: '4px solid #c4c6d3', marginTop: '0.5rem' }}>
                  <div className="risk-factor-left">
                    <span className="material-symbols-outlined" style={{ color: '#434652' }}>hub</span>
                    <span style={{ fontSize: 13 }}>
                      Proveedor con {(detalle.proveedor.pct_casos_observados * 100).toFixed(0)}% de casos observados
                    </span>
                  </div>
                </div>
              )}
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
                    {item.fecha && <p className="time">{item.fecha}</p>}
                    <p style={{ color: item.textColor === '#ba1a1a' ? '#ba1a1a' : '#434652' }}>{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Network & Documents */}
          <div className="three-col-grid">

            {/* Grafo de relaciones */}
            <div className="section-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0 }}>
                  <span className="material-symbols-outlined" style={{ color: '#002662' }}>account_tree</span>
                  Red de Relaciones
                </h2>
              </div>
              <div className="network-area">
                <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                  <line x1="50%" y1="50%" x2="25%" y2="30%" stroke="#002662" strokeWidth="2" strokeDasharray="5,5" />
                  {detalle.proveedor?.id && (
                    <line x1="50%" y1="50%" x2="75%" y2="35%"
                      stroke={detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#002662'} strokeWidth="2" />
                  )}
                </svg>

                {/* Asegurado (nodo central) */}
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', boxShadow: '0 4px 12px rgba(0,38,98,0.3)' }}>
                    <span className="material-symbols-outlined">person</span>
                  </div>
                  <span style={{ background: '#fff', padding: '2px 8px', borderRadius: 4, marginTop: 8, fontSize: 11, fontFamily: 'JetBrains Mono', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                    {detalle.id_asegurado}
                  </span>
                </div>

                {/* Póliza */}
                <div style={{ position: 'absolute', top: '30%', left: '25%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#fff', border: '2px solid #002662', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#002662' }}>
                    <span className="material-symbols-outlined">receipt_long</span>
                  </div>
                  <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono', marginTop: 4, color: '#434652' }}>Póliza</span>
                </div>

                {/* Proveedor */}
                {detalle.proveedor?.id && (
                  <div style={{ position: 'absolute', top: '35%', left: '75%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{
                      width: 56, height: 56, borderRadius: '50%',
                      background: detalle.proveedor.en_lista_restrictiva ? '#ffdad6' : '#e6eeff',
                      border: `2px solid ${detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#002662'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#002662',
                    }}>
                      <span className="material-symbols-outlined">build</span>
                    </div>
                    <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono', marginTop: 4, color: detalle.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#434652', fontWeight: detalle.proveedor.en_lista_restrictiva ? 700 : 400 }}>
                      {detalle.proveedor.id}
                    </span>
                  </div>
                )}
              </div>

              {/* Datos póliza */}
              <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: '#434652' }}>Suma asegurada: </span>
                  <span style={{ fontWeight: 700, color: '#002662' }}>{formatMonto(detalle.poliza.suma_asegurada)}</span>
                </div>
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: '#434652' }}>Prima: </span>
                  <span style={{ fontWeight: 700 }}>{formatMonto(detalle.poliza.prima)}</span>
                </div>
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: '#434652' }}>Monto est.: </span>
                  <span style={{ fontWeight: 700 }}>{formatMonto(detalle.monto_estimado)}</span>
                </div>
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: '#434652' }}>Monto pagado: </span>
                  <span style={{ fontWeight: 700 }}>{formatMonto(detalle.monto_pagado)}</span>
                </div>
              </div>
            </div>

            {/* Documentos */}
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
              {detalle.descripcion && (
                <div className="auditor-note">
                  <p>Descripción del caso:</p>
                  <p>"{detalle.descripcion}"</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="detalle-footer">
        <span style={{ fontWeight: 600, color: '#121c2a' }}>FraudIA Claims</span>
        <p style={{ margin: 0 }}>Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.</p>
        <div>
          <button onClick={() => onNav?.('configuracion')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#434652', fontSize: 12 }}>Ética AI</button>
          <button onClick={() => onNav?.('agente')}        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#434652', fontSize: 12 }}>Soporte Técnico</button>
          <button onClick={() => onNav?.('configuracion')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#434652', fontSize: 12 }}>Documentación</button>
        </div>
      </footer>

      {/* Modal Auditoría */}
      {auditoria && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          zIndex: 400, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            background: '#fff', borderRadius: 16, padding: '2rem',
            maxWidth: 420, width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(186,26,26,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 28, color: '#ba1a1a' }}>gavel</span>
              </div>
              <div>
                <h3 style={{ margin: 0, color: '#002662', fontSize: 18 }}>Iniciar Auditoría Formal</h3>
                <p style={{ margin: 0, fontSize: 12, color: '#747783', fontFamily: 'JetBrains Mono' }}>{detalle.id_siniestro}</p>
              </div>
            </div>
            <p style={{ fontSize: 14, color: '#434652', margin: '0 0 1.5rem', lineHeight: 1.6 }}>
              Este caso será escalado a la <strong>Unidad Antifraude</strong> para revisión especializada.
              La acción quedará registrada en el sistema de auditoría.
            </p>
            <div style={{ background: '#fff8e6', border: '1px solid #FFB800', borderRadius: 8, padding: '10px 14px', marginBottom: '1.5rem', fontSize: 12, color: '#856404' }}>
              <strong>Score de riesgo:</strong> {score}/100 · Nivel {nivel}
              {reglas.length > 0 && <><br/><strong>Reglas críticas:</strong> {reglas.map(r => r.codigo).join(', ')}</>}
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => setAuditoria(false)}
                style={{ flex: 1, padding: '12px', border: '1px solid #c4c6d3', borderRadius: 10, background: 'none', cursor: 'pointer', fontSize: 14 }}>
                Cancelar
              </button>
              <button
                onClick={() => { setAuditoria(false); setAuditConfirmada(true) }}
                style={{ flex: 1, padding: '12px', background: '#ba1a1a', color: '#fff', border: 'none', borderRadius: 10, cursor: 'pointer', fontSize: 14, fontWeight: 700 }}>
                Confirmar Escalamiento
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Panel */}
      {chatOpen && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="material-symbols-outlined" style={{ color: '#c6e7ff' }}>smart_toy</span>
              <span style={{ fontWeight: 700, fontSize: 14 }}>Agente IA FraudIA</span>
            </div>
            <button onClick={() => setChatOpen(false)} style={{ background: 'none', border: 'none', color: '#c6e7ff', cursor: 'pointer', fontSize: 20, lineHeight: 1 }}>×</button>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-msg chat-msg-ai">
                Hola. Soy el agente IA de FraudIA. Puedo analizar el siniestro <strong>{siniestroId}</strong> y responder tus preguntas. ¿En qué te ayudo?
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role === 'ai' ? 'chat-msg-ai' : 'chat-msg-user'}`}
                style={{ fontSize: 13, lineHeight: 1.6 }}>
                {m.role === 'ai' ? (
                  <div dangerouslySetInnerHTML={{ __html: renderMarkdown(m.text) }} />
                ) : (
                  m.text
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="chat-msg chat-msg-ai" style={{ opacity: 0.6 }}>
                <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 14, verticalAlign: 'middle' }}>sync</span>
                {' '}Analizando...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              className="chat-input"
              type="text"
              placeholder="Escribe tu pregunta..."
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
            />
            <button className="chat-send-btn" onClick={sendMessage} disabled={chatLoading || !chatInput.trim()}>
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>send</span>
            </button>
          </div>
        </div>
      )}

      {/* AI FAB */}
      <button className="ai-fab" onClick={() => setChatOpen(!chatOpen)}>
        <span className="material-symbols-outlined" style={{ fontSize: 28 }}>smart_toy</span>
        {!chatOpen && <span className="ai-fab-dot" />}
      </button>
    </div>
  )
}
