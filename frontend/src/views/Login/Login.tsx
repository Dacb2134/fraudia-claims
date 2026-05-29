import { useState } from 'react'
import './Login.css'
import { login, guardarSesion } from '../../services/authService'

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail]           = useState('')
  const [password, setPassword]     = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading]       = useState(false)
  const [hasError, setHasError]     = useState(false)
  const [shake, setShake]           = useState(false)

  const triggerError = () => {
    setHasError(true); setShake(true)
    setTimeout(() => { setHasError(false); setShake(false) }, 500)
  }

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) { triggerError(); return }
    setLoading(true)
    try {
      const result = await login(email, password)
      if (result.ok) { guardarSesion(result.usuario); onLogin() }
      else triggerError()
    } catch { triggerError() }
    finally { setLoading(false) }
  }

  return (
    <div className="login-page">
      <div className="login-bg" />
      <div className="login-grid" />
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />
      <div className="login-orb login-orb-3" />

      <main className="login-main">

        <div className="login-logo-wrap">
          <div className="login-logo-icon">
            <span className="material-symbols-outlined" style={{ fontSize: 36, color: '#fff', position: 'relative' }}>security</span>
          </div>
          <h1 className="login-title">FraudIA Claims</h1>
          <p className="login-subtitle">Detector Inteligente de Riesgos</p>
        </div>

        <div className="login-card">

          <div>
            <label className="login-label" htmlFor="email">Correo electrónico</label>
            <div className={`login-input-wrap ${shake ? 'animate-shake' : ''}`}>
              <span className="material-symbols-outlined login-input-icon">alternate_email</span>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                placeholder="correo@ejemplo.com"
                className={`login-input${hasError ? ' error' : ''}`}
                autoComplete="email"
              />
            </div>
          </div>

          <div>
            <label className="login-label" htmlFor="password">Contraseña</label>
            <div className={`login-input-wrap ${shake ? 'animate-shake' : ''}`}>
              <span className="material-symbols-outlined login-input-icon">lock</span>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                placeholder="••••••••"
                className={`login-input has-toggle${hasError ? ' error' : ''}`}
                autoComplete="current-password"
              />
              <button
                className="login-input-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  {showPassword ? 'visibility_off' : 'visibility'}
                </span>
              </button>
            </div>
          </div>

          <button className="login-btn-primary" onClick={handleLogin} disabled={loading}>
            {loading ? (
              <>
                <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite', fontSize: 18 }}>sync</span>
                Procesando...
              </>
            ) : (
              <>
                Iniciar sesión
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>arrow_forward</span>
              </>
            )}
          </button>

          <div className="login-divider">
            <hr /><span>Demo</span><hr />
          </div>

          {/* Cuentas demo por rol */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { rol: 'Analista', email: 'analista@fraudia.com', pass: 'analista123', color: '#3b82f6', icon: 'manage_search' },
              { rol: 'Supervisor', email: 'supervisor@fraudia.com', pass: 'supervisor123', color: '#f59e0b', icon: 'supervisor_account' },
              { rol: 'Admin', email: 'admin@fraudia.com', pass: 'admin123', color: '#ef4444', icon: 'admin_panel_settings' },
            ].map(({ rol, email, pass, color, icon }) => (
              <button
                key={rol}
                className="login-btn-demo"
                onClick={() => { setEmail(email); setPassword(pass) }}
                style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', textAlign: 'left' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 18, color, fontVariationSettings: "'FILL' 1" }}>{icon}</span>
                <span style={{ flex: 1 }}>
                  <span style={{ fontWeight: 700, color: 'rgba(148,186,255,0.9)', fontSize: 13 }}>{rol}</span>
                  <span style={{ display: 'block', fontSize: 11, color: 'rgba(148,186,255,0.4)', fontFamily: 'JetBrains Mono' }}>{email}</span>
                </span>
                <span style={{ fontSize: 11, color: 'rgba(148,186,255,0.35)', fontFamily: 'JetBrains Mono' }}>{pass}</span>
              </button>
            ))}
          </div>
        </div>

        <footer className="login-footer">
          <div className="login-badge">
            <span className="material-symbols-outlined" style={{ fontSize: 16, color: '#60a5fa' }}>shield</span>
            Este sistema detecta alertas, no acusa fraude
          </div>
          <div className="login-links">
            <a href="#">Ética AI</a>
            <span>•</span>
            <a href="#">HackIAthon 2026</a>
          </div>
        </footer>

      </main>
    </div>
  )
}
