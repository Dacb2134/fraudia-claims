"""
src/ai_agent/claims_agent.py
Agente IA conversacional para análisis de siniestros.

IMPLEMENTACIÓN REAL: backend/src/api/v1/chat.py

Modelo:    Google Gemini 2.0 Flash (gemini-2.0-flash)
Contexto:  Datos reales de la BD MySQL en cada consulta
Memoria:   Historial de 8 turnos de conversación

El agente responde las 12 preguntas obligatorias del HackIAthon 2026:
  1.  ¿Cuáles son los 10 siniestros con mayor riesgo de posible fraude?
  2.  ¿Por qué este siniestro fue marcado como alto riesgo?
  3.  ¿Qué proveedores concentran más alertas?
  4.  ¿Qué ramos tienen mayor porcentaje de casos sospechosos?
  5.  ¿Qué ciudades presentan mayor concentración de alertas?
  6.  ¿Qué asegurados tienen mayor frecuencia de reclamos?
  7.  ¿Qué documentos faltan en los casos críticos?
  8.  ¿Qué casos tienen montos atípicos?
  9.  ¿Qué siniestros ocurrieron cerca del inicio de la póliza?
  10. ¿Qué patrones se repiten en los reclamos sospechosos?
  11. Genera un resumen ejecutivo de los casos críticos.
  12. Recomienda qué casos debería revisar primero el analista.

Capacidades adicionales (no requeridas en el reto):
  - Análisis de archivos adjuntos (PDF, imagen, CSV, TXT)
  - Conversación multi-turn con memoria de contexto
  - Explicación automática al abrir un siniestro

Endpoints:
    POST /api/v1/chat
        body: {"pregunta": str, "historial": [...], "contexto_siniestro": str}
        → respuesta en lenguaje natural con datos reales de la BD

    POST /api/v1/chat/archivo
        form: {"pregunta": str, "archivo": file}
        → análisis del archivo adjunto con contexto del sistema

Principios inviolables del agente:
    - NUNCA acusar de fraude — solo "requiere revisión" o "señales de riesgo"
    - NUNCA inventar datos — basarse en la BD real
    - SIEMPRE indicar que la decisión final es del analista humano
    - NUNCA rechazar automáticamente un siniestro
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from src.api.v1.chat import router as chat_router  # noqa: F401
except ImportError:
    pass  # Módulos disponibles al ejecutar desde el contexto del backend
