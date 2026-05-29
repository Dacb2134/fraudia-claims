"""
src/explainability/explain_score.py
Módulo de explicabilidad del score de riesgo.

IMPLEMENTACIÓN REAL:
  - Explicación por reglas:  backend/src/engine/rules_evaluator.py  (alertas_activadas)
  - Explicación por IA:      backend/src/api/v1/chat.py             (Gemini 2.0 Flash)
  - Endpoint de recálculo:   POST /api/v1/siniestros/{id}/recalcular

El sistema genera dos tipos de explicación:

1. EXPLICACIÓN DETERMINÍSTICA (siempre disponible)
   Cada siniestro incluye:
   - score_normalizado:  puntaje final 0-100
   - nivel_riesgo:       VERDE / AMARILLO / ROJO
   - alertas_activadas:  lista de señales disparadas con descripción
   - reglas_criticas:    lista de RF-XX activadas (RF-01 a RF-07)
   - score_reglas:       componente del motor de reglas (60%)
   - score_ml:           componente del modelo XGBoost (40%)

   Ejemplo de respuesta:
   {
     "score_normalizado": 67,
     "nivel_riesgo": "AMARILLO",
     "alertas_activadas": "S-03: Asegurado con 4 siniestros previos | S-07: Proveedor en LISTA RESTRICTIVA",
     "reglas_criticas": ["RF-03"],
     "score_reglas": 60,
     "score_ml": 78,
     "modo": "hibrido"
   }

2. EXPLICACIÓN EN LENGUAJE NATURAL (vía Agente IA)
   El Agente Gemini 2.0 Flash genera una narrativa explicativa cuando:
   - Se abre el detalle de un siniestro (auto-explicación)
   - El analista pregunta "¿Por qué este caso es alto riesgo?"

Uso del endpoint:
    POST /api/v1/siniestros/{id}/recalcular
    → Recalcula y devuelve explicación completa en tiempo real

    POST /api/v1/chat
    → body: {"pregunta": "¿Por qué SIN-0001 es de alto riesgo?", "contexto_siniestro": "SIN-0001"}
    → El agente explica con lenguaje natural para el analista
"""


def explicar_score(resultado: dict) -> str:
    """
    Convierte el resultado del motor de reglas en un texto explicativo.

    Args:
        resultado: dict retornado por calcular_score_hibrido()

    Returns:
        Texto explicativo para el analista
    """
    score = resultado.get("score_normalizado", 0)
    nivel = resultado.get("nivel_riesgo", "VERDE")
    alertas = resultado.get("alertas_activadas", "Sin alertas detectadas")
    reglas = resultado.get("reglas_criticas", [])
    modo = resultado.get("modo", "reglas")

    nivel_texto = {
        "ROJO":     "ALTO RIESGO — Revisión especializada obligatoria",
        "AMARILLO": "RIESGO MEDIO — Escalar a Unidad Antifraude para revisión documental",
        "VERDE":    "BAJO RIESGO — Continuar flujo normal",
    }.get(nivel, "DESCONOCIDO")

    lineas = [
        f"Score de riesgo: {score}/100 — {nivel_texto}",
        f"Modo de cálculo: {modo}",
        "",
        "Señales activadas:",
    ]

    for alerta in alertas.split(" | "):
        if alerta.strip():
            lineas.append(f"  • {alerta.strip()}")

    if reglas:
        lineas.append("")
        lineas.append(f"Reglas críticas: {', '.join(reglas)}")

    return "\n".join(lineas)
