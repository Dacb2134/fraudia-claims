const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Stats {
  resumen: {
    total_siniestros: number
    score_promedio: number
    monto_total_riesgo: number
  }
  semaforo: {
    verde:    { total: number; monto: number }
    amarillo: { total: number; monto: number }
    rojo:     { total: number; monto: number }
  }
  por_ramo: { ramo: string; total: number }[]
  top_proveedores: { proveedor: string; total_alertas: number; alertas_rojas: number }[]
  top_asegurados: { id_asegurado: string; total_siniestros: number; score_max: number; monto_total: number }[]
  por_sucursal: { sucursal: string; total: number; rojos: number }[]
}

export interface Siniestro {
  id_siniestro: string
  id_asegurado: string
  ramo: string
  cobertura: string
  fecha_ocurrencia: string
  monto_reclamado: number
  estado: string
  sucursal: string
  score_riesgo: number
  nivel_riesgo: 'VERDE' | 'AMARILLO' | 'ROJO'
  alertas_activadas: string
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/api/v1/stats/`)
  if (!res.ok) throw new Error('Error al cargar estadísticas')
  return res.json()
}

export async function fetchSiniestros(nivel?: string): Promise<Siniestro[]> {
  const url = nivel
    ? `${API_URL}/api/v1/siniestros/?nivel_riesgo=${nivel}&page_size=10`
    : `${API_URL}/api/v1/siniestros/?page_size=10`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Error al cargar siniestros')
  const data = await res.json()
  return data.data
}
