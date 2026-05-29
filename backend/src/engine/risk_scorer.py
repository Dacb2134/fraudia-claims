"""
Orquestador del motor de scoring híbrido.
Combina reglas de negocio (60%) + predicción ML (40%) en un score final 0-100.
"""
from src.engine.rules_evaluator import ReglasNegocioEngine


def calcular_score_hibrido(
    siniestro: dict,
    proveedor: dict | None = None,
    prob_ml: float | None = None,
) -> dict:
    """
    Calcula el score final combinando reglas y ML.

    Args:
        siniestro:  Datos del siniestro (campos de la tabla siniestros + poliza).
        proveedor:  Datos del proveedor/beneficiario (opcional).
        prob_ml:    Probabilidad de fraude del modelo ML [0.0-1.0] (opcional).

    Returns:
        Dict con score_normalizado, nivel_riesgo, alertas_activadas, reglas_criticas.
    """
    # 1. Motor de reglas
    motor  = ReglasNegocioEngine(siniestro=siniestro, proveedor=proveedor)
    result = motor.ejecutar_motor()

    score_reglas = result["score_normalizado"]

    # 2. Score híbrido si hay predicción ML
    if prob_ml is not None:
        score_ml    = round(prob_ml * 100)
        score_final = round(score_reglas * 0.60 + score_ml * 0.40)
        score_final = min(100, max(0, score_final))
        result["score_normalizado"] = score_final
        result["score_reglas"]      = score_reglas
        result["score_ml"]          = score_ml
        result["modo"]              = "hibrido"
    else:
        result["score_reglas"] = score_reglas
        result["score_ml"]     = None
        result["modo"]         = "reglas"

    # Reclasificar con score final
    s = result["score_normalizado"]
    if s >= 76:
        result["nivel_riesgo"] = "ROJO"
    elif s >= 41:
        result["nivel_riesgo"] = "AMARILLO"
    else:
        result["nivel_riesgo"] = "VERDE"

    return result


def calcular_score_final(reglas_activas: list) -> int:
    """Compatibilidad hacia atrás — suma directa de puntos de reglas activas."""
    return min(100, sum(reglas_activas)) if reglas_activas else 0
