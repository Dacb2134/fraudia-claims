import { useState } from 'react'
import './Login.css'
import { login, guardarSesion } from '../../services/authService'

const DEMO_ROLES = [
  {
    id: 'analista',
    label: 'Analista de Riesgos',
    email: 'analista@fraudia.com',
    pass: 'analista123',
    icon: 'manage_search',
    color: '#3b82f6',
    bg: 'rgba(59,130,246,0.12)',
    acceso: 'Dashboard · Gestión de Casos · Agente IA',
  },
  {
    id: 'supervisor',
    label: 'Supervisor',
    email: 'supervisor@fraudia.com',
    pass: 'supervisor123',
    icon: 'supervisor_account',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    acceso: 'Dashboard · Reportes · Configuración · Agente IA',
  },
  {
    id: 'admin',
    label: 'Administrador',
    email: 'admin@fraudia.com',
    pass: 'admin123',
    icon: 'admin_panel_settings',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.12)',
    acceso: 'Acceso completo al sistema',
  },
]

const STATS = [
  { icon: 'assignment_late', value: '500+', label: 'Siniestros analizados' },
  { icon: 'rule',            value: '13',   label: 'Señales de fraude' },
  { icon: 'speed',           value: '<1s',  label: 'Score explicable' },
  { icon: 'psychology',      value: 'IA',   label: 'Motor híbrido' },
]

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email,       setEmail]       = useState('')
  const [password,    setPassword]    = useState('')
  const [showPass,    setShowPass]    = useState(false)
  const [loading,     setLoading]     = useState(false)
  const [loadingRole, setLoadingRole] = useState<string | null>(null)
  const [error,       setError]       = useState(false)
  const [shake,       setShake]       = useState(false)

  function triggerError() {
    setError(true); setShake(true)
    setTimeout(() => { setError(false); setShake(false) }, 600)
  }

  async function doLogin(em: string, pw: string, roleId?: string) {
    if (roleId) setLoadingRole(roleId); else setLoading(true)
    try {
      const res = await login(em, pw)
      if (res.ok) { guardarSesion(res.usuario); onLogin() }
      else triggerError()
    } catch { triggerError() }
    finally { setLoading(false); setLoadingRole(null) }
  }

  function handleSubmit() {
    if (!email.trim() || !password.trim()) { triggerError(); return }
    doLogin(email, password)
  }

  const anyLoading = loading || loadingRole !== null

  return (
    <div className="lp-root">
      {/* Fondo animado */}
      <div className="lp-bg" />
      <div className="lp-grid" />
      <div className="lp-orb lp-orb-1" />
      <div className="lp-orb lp-orb-2" />

      <div className="lp-wrap">

        {/* ── Columna izquierda: branding ── */}
        <div className="lp-brand">
          <div className="lp-brand-icon">
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: '#fff', fontVariationSettings: "'FILL' 1" }}>security</span>
          </div>
          <h1 className="lp-brand-title">FraudIA Claims</h1>
          <p className="lp-brand-sub">Detector Inteligente de Posibles Fraudes en Siniestros</p>
          <p className="lp-brand-desc">
            Sistema híbrido de IA que combina <strong>reglas de negocio</strong> y <strong>Machine Learning</strong> para
            detectar señales de riesgo en siniestros de seguros. Cada score es explicable y trazable.
          </p>

          {/* Stats */}
          <div className="lp-stats">
            {STATS.map(s => (
              <div key={s.label} className="lp-stat">
                <span className="material-symbols-outlined lp-stat-icon" style={{ fontVariationSettings: "'FILL' 1" }}>{s.icon}</span>
                <span className="lp-stat-value">{s.value}</span>
                <span className="lp-stat-label">{s.label}</span>
              </div>
            ))}
          </div>

          <div className="lp-ethics">
            <span className="material-symbols-outlined" style={{ fontSize: 14, color: '#60a5fa' }}>shield</span>
            <span>Genera alertas de revisión — nunca acusa automáticamente</span>
          </div>
        </div>

        {/* ── Columna derecha: formulario ── */}
        <div className="lp-card">

          <div className="lp-card-header">
            <h2 className="lp-card-title">Iniciar sesión</h2>
            <p className="lp-card-sub">Accede con tus credenciales institucionales</p>
          </div>

          {/* Form */}
          <div className="lp-form">
            <div className="lp-field">
              <label className="lp-label" htmlFor="lp-email">Correo electrónico</label>
              <div className={`lp-input-wrap ${shake ? 'lp-shake' : ''}`}>
                <span className="material-symbols-outlined lp-input-icon">alternate_email</span>
                <input
                  id="lp-email"
                  type="email"
                  autoComplete="off"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  placeholder="correo@empresa.com"
                  className={`lp-input ${error ? 'lp-input-error' : ''}`}
                />
              </div>
            </div>

            <div className="lp-field">
              <label className="lp-label" htmlFor="lp-pass">Contraseña</label>
              <div className={`lp-input-wrap ${shake ? 'lp-shake' : ''}`}>
                <span className="material-symbols-outlined lp-input-icon">lock</span>
                <input
                  id="lp-pass"
                  type={showPass ? 'text' : 'password'}
                  autoComplete="off"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  placeholder="••••••••"
                  className={`lp-input lp-input-pass ${error ? 'lp-input-error' : ''}`}
                />
                <button
                  type="button"
                  className="lp-eye"
                  onClick={() => setShowPass(v => !v)}
                  tabIndex={-1}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    {showPass ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            {error && (
              <p className="lp-error-msg">
                <span className="material-symbols-outlined" style={{ fontSize: 15 }}>error</span>
                Credenciales incorrectas. Intenta de nuevo.
              </p>
            )}

            <button
              className="lp-btn-primary"
              onClick={handleSubmit}
              disabled={anyLoading}
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined lp-spin">sync</span>
                  Verificando...
                </>
              ) : (
                <>
                  Iniciar sesión
                  <span className="material-symbols-outlined">arrow_forward</span>
                </>
              )}
            </button>
          </div>

          {/* Demo roles */}
          <div className="lp-divider">
            <span className="lp-divider-text">Acceso demo por rol</span>
          </div>

          <div className="lp-roles">
            {DEMO_ROLES.map(r => (
              <button
                key={r.id}
                className="lp-role-card"
                style={{ '--role-color': r.color, '--role-bg': r.bg } as React.CSSProperties}
                onClick={() => doLogin(r.email, r.pass, r.id)}
                disabled={anyLoading}
              >
                {loadingRole === r.id ? (
                  <span className="material-symbols-outlined lp-spin" style={{ color: r.color }}>sync</span>
                ) : (
                  <span className="material-symbols-outlined lp-role-icon" style={{ color: r.color, fontVariationSettings: "'FILL' 1" }}>
                    {r.icon}
                  </span>
                )}
                <div className="lp-role-info">
                  <span className="lp-role-name" style={{ color: r.color }}>{r.label}</span>
                  <span className="lp-role-access">{r.acceso}</span>
                </div>
                <span className="material-symbols-outlined lp-role-arrow">chevron_right</span>
              </button>
            ))}
          </div>

          <div className="lp-card-footer">
            <span>HackIAthon 2026 · Reto Aseguradora del Sur</span>
          </div>

        </div>
      </div>
    </div>
  )
}
