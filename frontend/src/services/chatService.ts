import { apiFetch, API_URL } from './api'
import type { ChatRequest, ChatResponse } from '../models'

export const sendChat = (req: ChatRequest): Promise<ChatResponse> =>
  apiFetch<ChatResponse>('/api/v1/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

export async function sendChatConArchivo(
  pregunta: string,
  archivo: File,
): Promise<ChatResponse> {
  const form = new FormData()
  form.append('pregunta', pregunta)
  form.append('archivo', archivo)

  const res = await fetch(`${API_URL}/api/v1/chat/archivo`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<ChatResponse>
}
