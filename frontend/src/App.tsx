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
  onNav:      (v: string) => void
  onLogout:   () => void
}

function App() {
  const [vista, setVista]       = useState<Vista>(() =>
    obtenerSesion() !== null ? 'dashboard' : 'login'
  )
  const [siniestroId, setSiniestroId] = useState<string>('')

  function handleVerDetalle(id: string) {
    setSiniestroId(id)
    setVista('detalle')
  }

  function handleLogout() {
    cerrarSesion()
    setVista('login')
  }

  function handleNav(v: string) { setVista(v as Vista) }
  const nav: NavProps = { onNav: handleNav, onLogout: handleLogout }

  if (vista === 'login') {
    return <Login onLogin={() => setVista('dashboard')} />
  }

  if (vista === 'detalle' && siniestroId) {
    return <Detalle siniestroId={siniestroId} onVolver={() => setVista('dashboard')} {...nav} />
  }

  if (vista === 'agente') {
    return <AgenteIA {...nav} />
  }

  if (vista === 'casos')         return <GestionCasos   {...nav} onVerDetalle={handleVerDetalle} />
  if (vista === 'reportes')      return <Reportes       {...nav} onVerDetalle={handleVerDetalle} />
  if (vista === 'configuracion') return <Configuracion  {...nav} />

  return <Dashboard onVerDetalle={handleVerDetalle} {...nav} />
}

export default App
