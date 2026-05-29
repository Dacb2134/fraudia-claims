// frontend/src/services/loginService.ts
// Servicio de autenticación — consume POST /api/v1/auth/login

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: "admin" | "analista" | "supervisor";
}

export interface LoginResponse {
  ok: boolean;
  usuario: Usuario;
}

// ── Login ─────────────────────────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error al iniciar sesión");
  }

  return res.json();
}

// ── Guardar y leer sesión en localStorage ─────────────────────────────────────
export function guardarSesion(usuario: Usuario): void {
  localStorage.setItem("usuario", JSON.stringify(usuario));
}

export function obtenerSesion(): Usuario | null {
  const data = localStorage.getItem("usuario");
  return data ? JSON.parse(data) : null;
}

export function cerrarSesion(): void {
  localStorage.removeItem("usuario");
}

export function estaLogueado(): boolean {
  return obtenerSesion() !== null;
}
