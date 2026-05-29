import { apiFetch } from './api'
import type { ChatRequest, ChatResponse } from '../models'

export const sendChat = (req: ChatRequest): Promise<ChatResponse> =>
  apiFetch<ChatResponse>('/api/v1/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
