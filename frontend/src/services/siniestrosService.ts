import { apiFetch } from './api'
import type { Siniestro, SiniestroDetalle, SiniestrosResponse } from '../models'

export async function fetchSiniestros(nivel?: string, pageSize = 50): Promise<Siniestro[]> {
  const params = new URLSearchParams({ page_size: String(pageSize) })
  if (nivel) params.set('nivel_riesgo', nivel)
  const res = await apiFetch<SiniestrosResponse>(`/api/v1/siniestros/?${params}`)
  return res.data
}

export const fetchSiniestroDetalle = (id: string): Promise<SiniestroDetalle> =>
  apiFetch<SiniestroDetalle>(`/api/v1/siniestros/${id}`)
