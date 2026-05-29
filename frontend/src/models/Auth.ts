export interface Usuario {
  id: number
  nombre: string
  email: string
  rol: 'admin' | 'analista' | 'supervisor'
}

export interface LoginResponse {
  ok: boolean
  usuario: Usuario
}
