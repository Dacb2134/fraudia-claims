"""
ai_data_core/agents/memory/chat_history.py
Gestión del historial de conversación para el agente FraudIA.
Mantiene contexto de sesión y permite recuperar conversaciones previas.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class Mensaje:
    """Representa un mensaje individual en el historial."""
    rol:       Literal["user", "assistant", "system"]
    contenido: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens:    int = 0

    def to_dict(self) -> dict:
        return {
            "role":    self.rol,
            "content": self.contenido,
        }

    def __repr__(self) -> str:
        preview = self.contenido[:60] + "..." if len(self.contenido) > 60 else self.contenido
        return f"Mensaje(rol={self.rol}, contenido='{preview}')"


class ChatHistoryManager:
    """
    Gestiona el historial de conversación del agente FraudIA.

    Características:
    - Límite configurable de mensajes para no sobrepasar el contexto del LLM.
    - Inyección automática del system prompt con contexto del siniestro.
    - Exportación del historial para logs y auditoría.
    """

    SYSTEM_PROMPT = """Eres FraudIA, un agente especializado en análisis de siniestros de seguros.
Tu rol es asistir a analistas humanos identificando señales de riesgo.

REGLAS ESTRICTAS:
1. NUNCA afirmes que un siniestro es fraude — usa 'presenta señales de riesgo' o 'requiere revisión'.
2. Basa TODA respuesta en los datos proporcionados, no en suposiciones.
3. Sé conciso y directo. Prioriza las alertas más críticas.
4. El score es una alerta de revisión, NO una acusación.
5. Sugiere siempre que la decisión final la tome un analista humano.

Clasificación de riesgo:
- Score 0-40  → 🟢 VERDE   (flujo normal)
- Score 41-75 → 🟡 AMARILLO (revisión documental)
- Score 76-100→ 🔴 ROJO    (revisión especializada)"""

    def __init__(self, max_mensajes: int = 20, id_siniestro: str | None = None):
        """
        Args:
            max_mensajes:  Número máximo de mensajes a mantener en memoria.
            id_siniestro:  Si se provee, enriquece el system prompt con contexto.
        """
        self.max_mensajes  = max_mensajes
        self.id_siniestro  = id_siniestro
        self._mensajes:  list[Mensaje] = []
        self._inicializar_system_prompt()

    # ── Inicialización ────────────────────────────────────────────────────────

    def _inicializar_system_prompt(self) -> None:
        prompt = self.SYSTEM_PROMPT
        if self.id_siniestro:
            prompt += f"\n\nContexto activo: Siniestro {self.id_siniestro}"
        self._mensajes.append(Mensaje(rol="system", contenido=prompt))

    # ── Escritura ─────────────────────────────────────────────────────────────

    def agregar_usuario(self, texto: str) -> None:
        """Agrega un mensaje del analista humano."""
        self._mensajes.append(Mensaje(rol="user", contenido=texto))
        self._truncar_si_necesario()

    def agregar_asistente(self, texto: str, tokens: int = 0) -> None:
        """Agrega la respuesta del agente IA."""
        self._mensajes.append(Mensaje(rol="assistant", contenido=texto, tokens=tokens))
        self._truncar_si_necesario()

    def _truncar_si_necesario(self) -> None:
        """Mantiene el historial dentro del límite preservando el system prompt."""
        mensajes_sin_system = [m for m in self._mensajes if m.rol != "system"]
        if len(mensajes_sin_system) > self.max_mensajes:
            system_msgs = [m for m in self._mensajes if m.rol == "system"]
            otros_msgs  = [m for m in self._mensajes if m.rol != "system"]
            self._mensajes = system_msgs + otros_msgs[-(self.max_mensajes):]

    # ── Lectura ───────────────────────────────────────────────────────────────

    def obtener_historial(self) -> list[dict]:
        """Retorna el historial en formato compatible con la API de Gemini/OpenAI."""
        return [m.to_dict() for m in self._mensajes]

    def obtener_ultimo_mensaje(self) -> Mensaje | None:
        """Retorna el último mensaje del historial."""
        mensajes_no_system = [m for m in self._mensajes if m.rol != "system"]
        return mensajes_no_system[-1] if mensajes_no_system else None

    def contar_tokens_estimados(self) -> int:
        """Estimación simple: 1 token ≈ 4 caracteres."""
        total_chars = sum(len(m.contenido) for m in self._mensajes)
        return total_chars // 4

    # ── Utilidades ────────────────────────────────────────────────────────────

    def limpiar(self) -> None:
        """Limpia el historial manteniendo solo el system prompt."""
        self._mensajes = []
        self._inicializar_system_prompt()

    def exportar_log(self) -> list[dict]:
        """Exporta el historial completo para auditoría con timestamps."""
        return [
            {
                "rol":       m.rol,
                "contenido": m.contenido,
                "timestamp": m.timestamp,
                "tokens":    m.tokens,
            }
            for m in self._mensajes
        ]

    def __len__(self) -> int:
        return len([m for m in self._mensajes if m.rol != "system"])

    def __repr__(self) -> str:
        return (f"ChatHistoryManager("
                f"mensajes={len(self)}, "
                f"tokens_est={self.contar_tokens_estimados()}, "
                f"siniestro={self.id_siniestro})")


# ── Demo / Test rápido ────────────────────────────────────────────────────────
if __name__ == "__main__":
    manager = ChatHistoryManager(max_mensajes=10, id_siniestro="SIN-00015")
    manager.agregar_usuario("¿Por qué este siniestro tiene score ROJO?")
    manager.agregar_asistente(
        "El siniestro SIN-00015 presenta señales de riesgo elevado: "
        "documentos inconsistentes (+10 pts), proveedor PROV-026 con 69% de casos observados (+5 pts), "
        "y narrativa similar al SIN-00092 con >85% de similitud textual (RF-07)."
    )
    print(manager)
    print(f"Tokens estimados: {manager.contar_tokens_estimados()}")
    print(f"Historial: {len(manager.obtener_historial())} mensajes")