import { apiFetch } from './api'
import type { LoginResponse, Usuario } from '../models'

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function guardarSesion(usuario: Usuario): void {
  localStorage.setItem('usuario', JSON.stringify(usuario))
}

export function obtenerSesion(): Usuario | null {
  const data = localStorage.getItem('usuario')
  return data ? (JSON.parse(data) as Usuario) : null
}

export function cerrarSesion(): void {
  localStorage.removeItem('usuario')
}
