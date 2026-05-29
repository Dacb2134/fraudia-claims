import { useState, useRef, useEffect } from 'react'
import './AgenteIA.css'
import Sidebar from '../../components/shared/Sidebar'
import { sendChat, sendChatConArchivo } from '../../services/chatService'
import type { ChatMessage } from '../../models'
import type { NavProps } from '../../App'

const STORAGE_KEY = 'fraudia_chat_messages'

const SUGERENCIAS = [
  '¿Cuáles son los 10 casos más riesgosos?',
  '¿Qué proveedores concentran más alertas?',
  '¿Qué casos tienen montos atípicos?',
  'Genera un resumen ejecutivo de casos críticos',
  '¿Qué ramos tienen más casos sospechosos?',
  '¿Qué asegurados tienen mayor frecuencia de reclamos?',
]

const NOTIFICACIONES = [
  { id: 1, texto: '60 casos en nivel ROJO requieren atención',   tiempo: 'Ahora',   tipo: 'error'   },
  { id: 2, texto: 'PROV-026 tiene 26 alertas rojas esta semana', tiempo: '5 min',   tipo: 'warning' },
  { id: 3, texto: 'Modelo de IA: necesita entrenamiento',         tiempo: '1 hora',  tipo: 'info'    },
]

const AYUDA_TIPS = [
  { icono: 'send',           tip: 'Escribe tu pregunta y presiona Enter para enviar' },
  { icono: 'smart_toy',      tip: 'Usa las sugerencias del panel derecho para consultas frecuentes' },
  { icono: 'description',    tip: '"Genera un resumen ejecutivo" crea un informe completo de casos críticos' },
  { icono: 'add_circle',     tip: '"Nuevo Chat" borra la conversación actual y empieza una nueva' },
  { icono: 'search',         tip: 'Usa la barra de búsqueda para encontrar mensajes anteriores' },
  { icono: 'warning',        tip: 'El agente NUNCA acusa de fraude — solo indica señales de riesgo' },
]

// ─── Renderizador de Markdown simple ────────────────────────────────────────
function renderMarkdown(text: string): string {
  return text
    // Headers
    .replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    .replace(/^### (.+)$/gm,  '<h3 class="md-h3">$1</h3>')
    .replace(/^## (.+)$/gm,   '<h2 class="md-h2">$2</h2>'.replace('$2', '$1'))
    // Bold + italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,         '<em>$1</em>')
    // Numbered lists — group them
    .replace(/^(\d+)\. (.+)$/gm, '<li class="md-li-num"><span class="md-num">$1.</span> $2</li>')
    // Bullet lists
    .replace(/^[*-] (.+)$/gm, '<li class="md-li">$1</li>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="md-hr"/>')
    // Wrap consecutive <li> blocks
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, m => `<ul class="md-ul">${m}</ul>`)
    // Paragraphs: blank lines become breaks
    .replace(/\n{2,}/g, '</p><p class="md-p">')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
    // Wrap in initial paragraph
    .replace(/^/, '<p class="md-p">')
    .replace(/$/, '</p>')
    // Clean empty paragraphs
    .replace(/<p class="md-p"><\/p>/g, '')
    .replace(/<p class="md-p">(<h[234]|<ul|<hr)/g, '$1')
    .replace(/(<\/h[234]>|<\/ul>|<hr[^>]*\/>)<\/p>/g, '$1')
}

// ─── Componente ──────────────────────────────────────────────────────────────
export default function AgenteIA({ onNav, onLogout }: NavProps) {
  const [messages,       setMessages]       = useState<ChatMessage[]>([])
  const [input,          setInput]          = useState('')
  const [loading,        setLoading]        = useState(false)
  const [archivoAdjunto, setArchivoAdjunto] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [resumenLoading, setResumenLoading] = useState(false)
  const [busqueda,       setBusqueda]       = useState('')
  const [showNotif,      setShowNotif]      = useState(false)
  const [showHelp,       setShowHelp]       = useState(false)
  const chatEndRef   = useRef<HTMLDivElement>(null)
  const textareaRef  = useRef<HTMLTextAreaElement>(null)

  // Cargar historial al montar
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) setMessages(JSON.parse(saved))
    } catch {}
  }, [])

  // Guardar historial en cada cambio
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    }
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function nuevaConversacion() {
    setMessages([])
    localStorage.removeItem(STORAGE_KEY)
  }

  async function enviar(pregunta?: string) {
    const texto = (pregunta ?? input).trim()
    if (!texto || loading) return
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const labelArchivo = archivoAdjunto ? ` 📎 ${archivoAdjunto.name}` : ''
    setMessages(prev => [...prev, { role: 'user', text: texto + labelArchivo }])
    setLoading(true)

    try {
      let res
      if (archivoAdjunto) {
        res = await sendChatConArchivo(texto, archivoAdjunto)
        setArchivoAdjunto(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
      } else {
        // Construir historial de la sesión para multi-turn memory
        // Enviamos los últimos 8 mensajes (4 intercambios user↔ai)
        const historialActual = messages
          .slice(-8)
          .filter(m => m.role === 'user' || m.role === 'ai')
          .map(m => ({ role: (m.role === 'user' ? 'user' : 'model') as 'user' | 'model', text: m.text }))

        res = await sendChat({ pregunta: texto, historial: historialActual })
      }
      setMessages(prev => [...prev, { role: 'ai', text: res.respuesta }])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error desconocido'
      const esQuota = msg.includes('429') || msg.toLowerCase().includes('quota') || msg.toLowerCase().includes('límite')
      const textoError = esQuota
        ? '⚠️ El agente IA está temporalmente no disponible por límite de uso de la API. Espera unos minutos y vuelve a intentarlo.'
        : `⚠️ No se pudo conectar con el agente. Verifica que el backend esté activo y la API key configurada.`
      setMessages(prev => [...prev, { role: 'ai', text: textoError }])
    } finally {
      setLoading(false)
    }
  }

  function seleccionarArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) setArchivoAdjunto(file)
  }

  async function generarResumen() {
    setResumenLoading(true)
    try {
      const res = await sendChat({
        pregunta: 'Genera un resumen ejecutivo completo de los casos críticos actuales. Incluye: total de casos ROJO, montos en riesgo, top proveedores con alertas, y los 3 casos prioritarios con sus señales de riesgo. Usa formato con títulos y listas.',
      })
      setMessages(prev => [...prev,
        { role: 'user', text: 'Generar resumen ejecutivo de casos críticos' },
        { role: 'ai',   text: res.respuesta },
      ])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error al generar el resumen.' }])
    } finally {
      setResumenLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar() }
  }

  function autoResize(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = e.target.scrollHeight + 'px'
  }

  // Filtrar mensajes según búsqueda
  const msgFiltrados = busqueda.trim()
    ? messages.filter(m => m.text.toLowerCase().includes(busqueda.toLowerCase()))
    : messages

  const msgsParaMostrar = busqueda.trim() ? msgFiltrados : messages

  return (
    <div className="agente-layout">
      <Sidebar vistaActiva="agente" onNav={onNav} onLogout={onLogout} />

      <main className="agente-main">

        {/* ── TopBar ── */}
        <header className="agente-header">
          <div className="flex items-center gap-3">
            <h2 className="agente-header-title">Agente IA</h2>
            {messages.length > 0 && (
              <span className="text-xs text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-full font-label-sm">
                {messages.length} mensajes
              </span>
            )}
          </div>

          <div className="agente-header-right">
            {/* Buscar en historial */}
            <div className={`search-box ${busqueda ? 'ring-2 ring-secondary/40' : ''}`}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: busqueda ? '#0053cf' : '#747783' }}>search</span>
              <input
                placeholder="Buscar en el historial..."
                type="text"
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
              />
              {busqueda && (
                <button
                  onClick={() => setBusqueda('')}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#747783', padding: 0, lineHeight: 1 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                </button>
              )}
            </div>

            {/* Nuevo chat */}
            <button
              onClick={nuevaConversacion}
              className="icon-btn"
              title="Nueva conversación"
              style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, fontFamily: 'JetBrains Mono', color: '#434652', background: 'none', border: '1px solid #c4c6d3', borderRadius: 8, padding: '4px 10px', cursor: 'pointer' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>add_circle</span>
              Nuevo chat
            </button>

            {/* Notificaciones */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => { setShowNotif(v => !v); setShowHelp(false) }}
                className="icon-btn"
                title="Notificaciones"
                style={{ position: 'relative' }}>
                <span className="material-symbols-outlined">notifications</span>
                <span style={{ position: 'absolute', top: 4, right: 4, width: 8, height: 8, borderRadius: '50%', background: '#ba1a1a', border: '2px solid white' }}/>
              </button>
              {showNotif && (
                <div style={{
                  position: 'absolute', top: '100%', right: 0, marginTop: 8,
                  background: 'white', borderRadius: 12, border: '1px solid #c4c6d3',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.12)', width: 300, zIndex: 200,
                }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid #c4c6d3', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: '#002662' }}>Alertas del Sistema</span>
                    <button onClick={() => setShowNotif(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#747783' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                    </button>
                  </div>
                  {NOTIFICACIONES.map(n => (
                    <div key={n.id} style={{ padding: '10px 16px', borderBottom: '1px solid #f0f2fa', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18, color: n.tipo === 'error' ? '#ba1a1a' : n.tipo === 'warning' ? '#f97316' : '#0053cf', marginTop: 1, fontVariationSettings: "'FILL' 1" }}>
                        {n.tipo === 'error' ? 'crisis_alert' : n.tipo === 'warning' ? 'warning' : 'info'}
                      </span>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: 12, color: '#121c2a', margin: 0, lineHeight: 1.4 }}>{n.texto}</p>
                        <p style={{ fontSize: 10, color: '#747783', margin: '2px 0 0', fontFamily: 'JetBrains Mono' }}>{n.tiempo}</p>
                      </div>
                    </div>
                  ))}
                  <div style={{ padding: '8px 16px' }}>
                    <button
                      onClick={() => { onNav('reportes'); setShowNotif(false) }}
                      style={{ width: '100%', padding: '6px', background: '#e6eeff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12, color: '#002662', fontWeight: 600 }}>
                      Ver todos los reportes →
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Ayuda */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => { setShowHelp(v => !v); setShowNotif(false) }}
                className="icon-btn"
                title="Ayuda">
                <span className="material-symbols-outlined">help</span>
              </button>
              {showHelp && (
                <div style={{
                  position: 'absolute', top: '100%', right: 0, marginTop: 8,
                  background: 'white', borderRadius: 12, border: '1px solid #c4c6d3',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.12)', width: 320, zIndex: 200,
                }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid #c4c6d3', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: '#002662' }}>¿Cómo usar el Agente IA?</span>
                    <button onClick={() => setShowHelp(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#747783' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                    </button>
                  </div>
                  <div style={{ padding: 16 }}>
                    {AYUDA_TIPS.map((t, i) => (
                      <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 10 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#002662', marginTop: 1 }}>{t.icono}</span>
                        <p style={{ fontSize: 12, color: '#434652', margin: 0, lineHeight: 1.5 }}>{t.tip}</p>
                      </div>
                    ))}
                  </div>
                  <div style={{ padding: '8px 16px', borderTop: '1px solid #f0f2fa', background: '#eff4ff', borderRadius: '0 0 12px 12px' }}>
                    <p style={{ fontSize: 11, color: '#747783', margin: 0, textAlign: 'center' }}>
                      Este agente NO determina fraude. Genera alertas de revisión.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="user-chip">
              <div className="user-text">
                <p className="user-name">Analista de Riesgos</p>
                <p className="user-role">Senior Investigator</p>
              </div>
              <div className="user-avatar">A</div>
            </div>
          </div>
        </header>

        {/* Indicador de búsqueda activa */}
        {busqueda && (
          <div style={{ background: '#e6eeff', padding: '8px 2rem', fontSize: 12, color: '#002662', borderBottom: '1px solid #c4c6d3', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>search</span>
            {msgFiltrados.length} resultado{msgFiltrados.length !== 1 ? 's' : ''} para "{busqueda}"
            <button onClick={() => setBusqueda('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: '#434652' }}>
              Limpiar búsqueda
            </button>
          </div>
        )}

        {/* ── Chat + Panel ── */}
        <div className="agente-body">

          {/* Área de mensajes */}
          <div className="chat-area">

            {/* Bienvenida */}
            {messages.length === 0 && (
              <div className="chat-welcome">
                <div className="chat-welcome-icon ai-glow">
                  <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1", fontSize: 40, color: '#fff' }}>smart_toy</span>
                </div>
                <h3 className="chat-welcome-title">Hola, Analista. ¿En qué puedo ayudarte hoy?</h3>
                <p className="chat-welcome-sub">Analizo miles de reclamos en tiempo real para identificar patrones inusuales y conexiones de fraude ocultas.</p>
                <p style={{ fontSize: 11, color: '#747783', marginTop: 8, fontStyle: 'italic' }}>Las conversaciones se guardan automáticamente en tu dispositivo.</p>
              </div>
            )}

            {/* Mensajes (filtrados si hay búsqueda) */}
            {msgsParaMostrar.map((msg, i) => (
              <div key={i} className={`chat-row ${msg.role === 'user' ? 'chat-row-user' : 'chat-row-ai'}`}>
                {msg.role === 'ai' && (
                  <div className="chat-avatar-ai">
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1", fontSize: 16, color: '#fff' }}>smart_toy</span>
                  </div>
                )}
                <div className={`chat-bubble ${msg.role === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user'}`}>
                  {msg.role === 'ai' ? (
                    <div
                      className="markdown-body"
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                    />
                  ) : (
                    <p style={{ margin: 0 }}>{msg.text}</p>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="chat-avatar-user">
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>person</span>
                  </div>
                )}
              </div>
            ))}

            {/* Loading dots */}
            {loading && (
              <div className="chat-row chat-row-ai">
                <div className="chat-avatar-ai">
                  <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1", fontSize: 16, color: '#fff' }}>smart_toy</span>
                </div>
                <div className="chat-bubble chat-bubble-ai chat-loading">
                  <span /><span /><span />
                </div>
              </div>
            )}

            {/* Sin resultados de búsqueda */}
            {busqueda && msgFiltrados.length === 0 && (
              <div style={{ textAlign: 'center', padding: '3rem', color: '#747783' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 40, display: 'block', marginBottom: 8 }}>search_off</span>
                No hay mensajes que contengan "{busqueda}"
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* ── Panel derecho ── */}
          <aside className="agente-panel">

            <div>
              <h4 className="panel-title">Sugerencias Inteligentes</h4>
              <div className="suggestions-list">
                {SUGERENCIAS.map(s => (
                  <button key={s} className="suggestion-btn" onClick={() => enviar(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="panel-tools">
              <h4 className="panel-title">Herramientas</h4>
              <button
                className="btn-resumen"
                onClick={generarResumen}
                disabled={resumenLoading}>
                <span className="material-symbols-outlined">description</span>
                {resumenLoading ? 'Generando…' : 'Generar Resumen Ejecutivo'}
              </button>
              <p className="btn-resumen-hint">IA redactará un resumen con los hallazgos principales.</p>

              {messages.length > 0 && (
                <button
                  onClick={nuevaConversacion}
                  style={{
                    width: '100%', marginTop: 12, padding: '10px', borderRadius: 12,
                    border: '1px solid #c4c6d3', background: 'none', cursor: 'pointer',
                    fontSize: 13, color: '#434652', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>delete_sweep</span>
                  Nueva conversación
                </button>
              )}
            </div>

            <div className="panel-footer">
              <p>Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.</p>
            </div>
          </aside>
        </div>

        {/* ── Input ── */}
        <footer className="agente-footer">
          {/* Indicador de archivo adjunto */}
          {archivoAdjunto && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
              background: '#e6eeff', borderRadius: 8, marginBottom: 8,
              fontSize: 12, color: '#002662',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>description</span>
              <span style={{ fontWeight: 600 }}>{archivoAdjunto.name}</span>
              <span style={{ color: '#747783' }}>({(archivoAdjunto.size / 1024).toFixed(0)} KB)</span>
              <button
                onClick={() => { setArchivoAdjunto(null); if (fileInputRef.current) fileInputRef.current.value = '' }}
                style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#ba1a1a' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
              </button>
            </div>
          )}
          <div className="input-wrap">
            <div className="input-box">
              {/* Input de archivo oculto */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.csv,image/*"
                style={{ display: 'none' }}
                onChange={seleccionarArchivo}
              />
              <button
                className="input-icon-btn"
                title="Adjuntar PDF, TXT, CSV o imagen"
                onClick={() => fileInputRef.current?.click()}
                style={archivoAdjunto ? { color: '#0053cf' } : {}}>
                <span className="material-symbols-outlined">attach_file</span>
              </button>
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={autoResize}
                onKeyDown={handleKeyDown}
                placeholder={archivoAdjunto ? `Pregunta sobre "${archivoAdjunto.name}"…` : 'Pregunta sobre pólizas, siniestros o proveedores… (Enter para enviar)'}
                className="input-textarea"
              />
            </div>
            <button
              className="send-btn"
              onClick={() => enviar()}
              disabled={loading || !input.trim()}>
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
          <p className="input-disclaimer">
            Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.
          </p>
        </footer>
      </main>
    </div>
  )
}
