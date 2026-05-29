import { apiFetch } from './api'
import type { Stats } from '../models'

export const fetchStats = (): Promise<Stats> =>
  apiFetch<Stats>('/api/v1/stats/')
