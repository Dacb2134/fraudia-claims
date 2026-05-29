import { useState } from 'react'
import Login from './components/login/Login'
import Dashboard from './components/dashboard/Dashboard'
import Detalle from './components/detalle/Detalle'
import { obtenerSesion, cerrarSesion } from './services/loginService'

type Vista = 'login' | 'dashboard' | 'detalle'

function App() {
  const [vista, setVista] = useState<Vista>(() =>
    obtenerSesion() !== null ? 'dashboard' : 'login'
  )

  const handleLogout = () => {
    cerrarSesion()
    setVista('login')
  }

  if (vista === 'login') {
    return <Login onLogin={() => setVista('dashboard')} />
  }

  if (vista === 'detalle') {
    return <Detalle onVolver={() => setVista('dashboard')} />
  }

  return <Dashboard onVerDetalle={() => setVista('detalle')} onLogout={handleLogout} />
}

export default App
