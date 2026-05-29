import { useState } from 'react'
import Login          from './views/Login/Login'
import Dashboard      from './views/Dashboard/Dashboard'
import Detalle        from './views/Detalle/Detalle'
import AgenteIA       from './views/AgenteIA/AgenteIA'
import GestionCasos   from './views/GestionCasos/GestionCasos'
import Reportes       from './views/Reportes/Reportes'
import Configuracion  from './views/Configuracion/Configuracion'
import { obtenerSesion, cerrarSesion } from './services/authService'

export type Vista = 'login' | 'dashboard' | 'detalle' | 'agente' | 'casos' | 'reportes' | 'configuracion'

export interface NavProps {
  onNav:    (v: string) => void
  onLogout: () => void
}

const VISTA_LABELS: Record<string, string> = {
  dashboard:     'Dashboard',
  casos:         'Gestión de Casos',
  reportes:      'Reportes',
  agente:        'Agente IA',
  configuracion: 'Configuración',
  detalle:       'Detalle de Caso',
}

function App() {
  const [vista,      setVista]      = useState<Vista>(() =>
    obtenerSesion() !== null ? 'dashboard' : 'login'
  )
  const [siniestroId, setSiniestroId] = useState<string>('')

  function handleVerDetalle(id: string) { setSiniestroId(id); setVista('detalle') }
  function handleLogout()  { cerrarSesion(); setVista('login') }
  function handleNav(v: string) { setVista(v as Vista) }

  const nav: NavProps = { onNav: handleNav, onLogout: handleLogout }

  if (vista === 'login') {
    return <Login onLogin={() => setVista('dashboard')} />
  }

  const usuario = obtenerSesion()

  // ── Mobile top bar (shown on all authenticated views, hidden on desktop) ──
  const mobileBar = (
    <header
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 300,
        height: 56,
        background: 'linear-gradient(90deg, #001e5c 0%, #002d8a 100%)',
        display: 'flex', alignItems: 'center',
        padding: '0 16px', gap: 12,
        boxShadow: '0 2px 16px rgba(0,0,20,0.35)',
      }}
      className="mobile-topbar"
    >
      {/* Hamburger — dispatches custom event picked up by Sidebar */}
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('fraudia:toggle-sidebar'))}
        style={{
          background: 'rgba(255,255,255,0.1)', border: 'none',
          borderRadius: 8, color: '#fff', cursor: 'pointer',
          width: 40, height: 40, minWidth: 40,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 22 }}>menu</span>
      </button>

      {/* App name */}
      <span style={{ color: '#fff', fontWeight: 800, fontSize: 16, letterSpacing: '-0.02em', whiteSpace: 'nowrap' }}>
        FraudIA Claims
      </span>

      {/* Current page */}
      <span style={{
        fontSize: 12, color: 'rgba(148,186,255,0.6)',
        fontFamily: 'JetBrains Mono, monospace',
        flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        paddingLeft: 4,
      }}>
        / {VISTA_LABELS[vista] ?? vista}
      </span>

      {/* Role badge */}
      {usuario?.rol && (
        <span style={{
          fontSize: 10, fontWeight: 700,
          color: usuario.rol === 'admin' ? '#fca5a5'
               : usuario.rol === 'supervisor' ? '#fde68a'
               : '#93c5fd',
          background: 'rgba(255,255,255,0.08)',
          padding: '3px 8px', borderRadius: 6,
          fontFamily: 'JetBrains Mono, monospace',
          textTransform: 'uppercase', flexShrink: 0,
        }}>
          {usuario.rol}
        </span>
      )}
    </header>
  )

  if (vista === 'detalle' && siniestroId) {
    return <>{mobileBar}<Detalle siniestroId={siniestroId} onVolver={() => setVista('dashboard')} {...nav} /></>
  }
  if (vista === 'agente')        return <>{mobileBar}<AgenteIA       {...nav} /></>
  if (vista === 'casos')         return <>{mobileBar}<GestionCasos   {...nav} onVerDetalle={handleVerDetalle} /></>
  if (vista === 'reportes')      return <>{mobileBar}<Reportes       {...nav} onVerDetalle={handleVerDetalle} /></>
  if (vista === 'configuracion') return <>{mobileBar}<Configuracion  {...nav} /></>

  return <>{mobileBar}<Dashboard onVerDetalle={handleVerDetalle} {...nav} /></>
}

export default App
