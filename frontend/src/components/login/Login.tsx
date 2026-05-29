import { useState } from 'react'
import './Login.css'
import { login, guardarSesion } from '../../services/loginService'

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [shake, setShake] = useState(false)

  const triggerError = () => {
    setHasError(true)
    setShake(true)
    setTimeout(() => {
      setHasError(false)
      setShake(false)
    }, 500)
  }

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      triggerError()
      return
    }
    setLoading(true)
    try {
      const result = await login(email, password)
      if (result.ok) {
        guardarSesion(result.usuario)
        onLogin()
      } else {
        triggerError()
      }
    } catch {
      triggerError()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">

      {/* Blobs decorativos — sin Tailwind */}
      <div className="login-bg-blob-1" />
      <div className="login-bg-blob-2" />

      {/* Contenido principal */}
      <main style={{
        position: 'relative',
        zIndex: 10,
        width: '100%',
        maxWidth: 440,
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem'
      }}>

        {/* Logo */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '0.5rem' }}>
          <div style={{
            background: '#fff',
            padding: '1rem',
            borderRadius: '0.75rem',
            boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
            marginBottom: '0.5rem'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: '#002662' }}>security</span>
          </div>
          <h1 style={{ fontFamily: 'Hanken Grotesk, sans-serif', fontSize: 32, fontWeight: 700, color: '#fff', margin: 0 }}>
            FraudIA Claims
          </h1>
          <p style={{ fontSize: 14, color: 'rgba(219,234,254,0.8)', margin: 0 }}>
            Detector Inteligente de Riesgos
          </p>
        </div>

        {/* Tarjeta */}
        <div style={{
          background: '#fff',
          borderRadius: '1rem',
          padding: '2rem',
          boxShadow: '0 8px 32px rgba(0,38,98,0.18)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem'
        }}>

          {/* Email */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: '#434652', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Correo electrónico
            </label>
            <div className={shake ? 'animate-shake' : ''} style={{ position: 'relative' }}>
              <span className="material-symbols-outlined" style={{
                position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                color: '#747783', fontSize: 20
              }}>badge</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder="correo@ejemplo.com"
                className={hasError ? 'border-error' : ''}
                style={{
                  width: '100%', paddingLeft: 44, paddingRight: 16,
                  paddingTop: 14, paddingBottom: 14,
                  background: '#eff4ff', border: '1px solid #c4c6d3',
                  borderRadius: '0.5rem', fontSize: 15, color: '#121c2a',
                  outline: 'none', boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          {/* Contraseña */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: '#434652', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Contraseña
            </label>
            <div className={shake ? 'animate-shake' : ''} style={{ position: 'relative' }}>
              <span className="material-symbols-outlined" style={{
                position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                color: '#747783', fontSize: 20
              }}>lock</span>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder="••••••••"
                className={hasError ? 'border-error' : ''}
                style={{
                  width: '100%', paddingLeft: 44, paddingRight: 44,
                  paddingTop: 14, paddingBottom: 14,
                  background: '#eff4ff', border: '1px solid #c4c6d3',
                  borderRadius: '0.5rem', fontSize: 15, color: '#121c2a',
                  outline: 'none', boxSizing: 'border-box'
                }}
              />
              <span
                className="material-symbols-outlined"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  color: '#747783', fontSize: 20, cursor: 'pointer'
                }}
              >
                {showPassword ? 'visibility_off' : 'visibility'}
              </span>
            </div>
          </div>

          {/* Botón */}
          <button
            onClick={handleLogin}
            disabled={loading}
            style={{
              width: '100%', padding: '1rem',
              background: loading ? '#6b8fd4' : '#002662',
              color: '#fff', border: 'none', borderRadius: '0.5rem',
              fontSize: 16, fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: '0.5rem', transition: 'background 0.2s'
            }}
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined" style={{ animation: 'spin 1s linear infinite' }}>sync</span>
                Procesando...
              </>
            ) : (
              <>
                Iniciar sesión
                <span className="material-symbols-outlined">arrow_forward</span>
              </>
            )}
          </button>

          {/* Divisor */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #c4c6d3' }} />
            <span style={{ fontSize: 12, color: '#747783', fontFamily: 'JetBrains Mono, monospace' }}>O</span>
            <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #c4c6d3' }} />
          </div>

          {/* Demo */}
          <button
            onClick={() => { setEmail('analista@fraudia.com'); setPassword('analista123') }}
            style={{
              width: '100%', padding: '0.75rem',
              background: '#dee9fc', color: '#0053cf',
              border: 'none', borderRadius: '0.5rem',
              fontSize: 16, fontWeight: 600, cursor: 'pointer'
            }}>
            Acceso demo
          </button>
        </div>

        {/* Footer */}
        <footer style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <div className="glass-panel" style={{
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            padding: '0.75rem 1.5rem', borderRadius: '999px', color: 'rgba(255,255,255,0.9)'
          }}>
            <span className="material-symbols-outlined" style={{ color: '#82cfff' }}>info</span>
            <p style={{ margin: 0, fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
              Este sistema detecta alertas, no acusa fraude
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <a href="#" style={{ fontSize: 12, color: '#bfdbfe', textDecoration: 'none' }}>Ética AI</a>
            <span style={{ color: 'rgba(147,197,253,0.3)' }}>•</span>
            <a href="#" style={{ fontSize: 12, color: '#bfdbfe', textDecoration: 'none' }}>Soporte Técnico</a>
          </div>
        </footer>

      </main>
    </div>
  )
}
