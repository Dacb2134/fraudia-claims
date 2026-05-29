export interface HistorialMsg {
  role: 'user' | 'model'
  text: string
}

export interface ChatRequest {
  pregunta: string
  contexto_siniestro?: string
  historial?: HistorialMsg[]  // memoria de sesión multi-turn
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
