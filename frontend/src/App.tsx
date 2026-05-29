import { useState } from 'react'
import Login from './views/Login/Login'
import Dashboard from './views/Dashboard/Dashboard'
import Detalle from './views/Detalle/Detalle'
import { obtenerSesion, cerrarSesion } from './services/authService'

type Vista = 'login' | 'dashboard' | 'detalle'

function App() {
  const [vista, setVista]           = useState<Vista>(() =>
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

  if (vista === 'login') {
    return <Login onLogin={() => setVista('dashboard')} />
  }

  if (vista === 'detalle' && siniestroId) {
    return (
      <Detalle
        siniestroId={siniestroId}
        onVolver={() => setVista('dashboard')}
      />
    )
  }

  return (
    <Dashboard
      onVerDetalle={handleVerDetalle}
      onLogout={handleLogout}
    />
  )
}

export default App
