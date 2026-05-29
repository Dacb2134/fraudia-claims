export interface ChatRequest {
  pregunta: string
  contexto_siniestro?: string
}

export interface ChatResponse {
  pregunta: string
  respuesta: string
  modelo: string
}

export interface ChatMessage {
  role: 'user' | 'ai'
  text: string
}
