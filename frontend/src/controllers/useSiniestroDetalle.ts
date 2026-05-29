import { useState, useEffect, useRef } from 'react'
import { fetchSiniestroDetalle } from '../services/siniestrosService'
import { sendChat } from '../services/chatService'
import type { SiniestroDetalle, ChatMessage } from '../models'

export function useSiniestroDetalle(id: string) {
  const [detalle, setDetalle]   = useState<SiniestroDetalle | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)

  // Explicación IA auto-cargada
  const [aiExplanation, setAiExplanation]   = useState<string | null>(null)
  const [aiExplLoading, setAiExplLoading]   = useState(false)
  const explanationFetched = useRef(false)

  // Chat interactivo
  const [chatOpen, setChatOpen]         = useState(false)
  const [messages, setMessages]         = useState<ChatMessage[]>([])
  const [chatInput, setChatInput]       = useState('')
  const [chatLoading, setChatLoading]   = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(null)
    explanationFetched.current = false
    fetchSiniestroDetalle(id)
      .then(setDetalle)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Error al cargar siniestro'))
      .finally(() => setLoading(false))
  }, [id])

  // Auto-explicación IA cuando carga el detalle
  useEffect(() => {
    if (!detalle || explanationFetched.current) return
    explanationFetched.current = true
    setAiExplLoading(true)
    sendChat({
      pregunta: `Explica en 3-4 oraciones por qué el siniestro ${detalle.id_siniestro} presenta señales de riesgo ${detalle.score.nivel}. Menciona las alertas más relevantes.`,
      contexto_siniestro: detalle.id_siniestro,
    })
      .then(r => setAiExplanation(r.respuesta))
      .catch(() => setAiExplanation(null))
      .finally(() => setAiExplLoading(false))
  }, [detalle])

  async function sendMessage() {
    const pregunta = chatInput.trim()
    if (!pregunta || chatLoading) return
    setChatInput('')
    setMessages(prev => [...prev, { role: 'user', text: pregunta }])
    setChatLoading(true)
    try {
      const res = await sendChat({ pregunta, contexto_siniestro: id })
      setMessages(prev => [...prev, { role: 'ai', text: res.respuesta }])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error al conectar con el agente IA.' }])
    } finally {
      setChatLoading(false)
    }
  }

  return {
    detalle, loading, error,
    aiExplanation, aiExplLoading,
    chatOpen, setChatOpen,
    messages, chatInput, setChatInput,
    chatLoading, sendMessage,
  }
}
