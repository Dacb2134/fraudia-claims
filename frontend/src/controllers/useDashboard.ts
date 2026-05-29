import { useState, useEffect } from 'react'
import { fetchStats } from '../services/statsService'
import { fetchSiniestros } from '../services/siniestrosService'
import type { Stats, Siniestro } from '../models'

export function useDashboard() {
  const [stats, setStats]   = useState<Stats | null>(null)
  const [casos, setCasos]   = useState<Siniestro[]>([])
  const [filtro, setFiltro] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([fetchStats(), fetchSiniestros(filtro, 500)])
      .then(([s, c]) => { setStats(s); setCasos(c) })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Error de carga'))
      .finally(() => setLoading(false))
  }, [filtro])

  return { stats, casos, filtro, setFiltro, loading, error }
}
