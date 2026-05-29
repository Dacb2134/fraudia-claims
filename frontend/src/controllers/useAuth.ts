import { useState } from 'react'
import { login as apiLogin, guardarSesion, obtenerSesion, cerrarSesion } from '../services/authService'
import type { Usuario } from '../models'

export function useAuth() {
  const [usuario, setUsuario] = useState<Usuario | null>(obtenerSesion)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function login(email: string, password: string): Promise<boolean> {
    setLoading(true)
    setError(null)
    try {
      const { usuario: u } = await apiLogin(email, password)
      guardarSesion(u)
      setUsuario(u)
      return true
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al iniciar sesión')
      return false
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    cerrarSesion()
    setUsuario(null)
  }

  return { usuario, loading, error, login, logout }
}
