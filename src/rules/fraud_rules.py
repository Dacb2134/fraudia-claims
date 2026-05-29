"""
src/rules/fraud_rules.py
Motor de reglas de negocio para detección de posibles fraudes.

IMPLEMENTACIÓN REAL: backend/src/engine/rules_evaluator.py
                     backend/src/engine/risk_scorer.py

Este archivo documenta la ubicación del módulo en la arquitectura del proyecto.
La lógica se encuentra en el backend FastAPI por diseño de arquitectura full-stack.

Uso directo (fuera de la API):
    import sys; sys.path.insert(0, 'backend')
    from src.engine.rules_evaluator import ReglasNegocioEngine
    from src.engine.risk_scorer import calcular_score_hibrido

    siniestro = {
        'cobertura': 'Daño', 'estado': 'Reserva',
        'monto_reclamado': 5000, 'dias_desde_inicio_poliza': 20,
        'historial_siniestros_asegurado': 3, 'documentos_completos': False,
        'tiene_doc_inconsistente': 0, 'dias_entre_ocurrencia_reporte': 2,
    }
    proveedor = {'en_lista_restrictiva': False, 'pct_casos_observados': 0.0}

    resultado = calcular_score_hibrido(siniestro=siniestro, proveedor=proveedor)
    print(resultado['score_normalizado'], resultado['nivel_riesgo'])

Señales implementadas (13 + 7 reglas críticas):
    S-01  Siniestro borde de vigencia (≤30 días)          → hasta 8 pts
    S-02  Demora denuncia robo (>48h)                     → hasta 8 pts
    S-03  Alta frecuencia asegurado (≥3 siniestros)        → hasta 8 pts
    S-04  Frecuencia solo RC (>2 eventos)                  → hasta 6 pts
    S-07  Proveedor en lista restrictiva                   → hasta 10 pts
    S-08  Documentos incompletos                           → hasta 4 pts
    S-09  Dinámica sospechosa (análisis texto)             → hasta 6 pts
    S-10  Daño severo sin tercero identificado             → hasta 5 pts
    S-11  Documentos inconsistentes/adulterados            → hasta 10 pts
    S-12  Reporte tardío (>7 días)                         → hasta 5 pts
    S-13  Narrativa clonada (TF-IDF ≥85%)                 → hasta 8 pts
    S-14  Monto ≥95% suma asegurada                       → hasta 5 pts
    RF-01 Pérdida Total por Robo (CRÍTICA)                → +20 pts

Score máximo referencial: 90 pts → normalizado 0-100
Semáforo: VERDE 0-40 | AMARILLO 41-75 | ROJO 76-100
"""

# Re-export para compatibilidad con la estructura esperada del hackathon
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from src.engine.rules_evaluator import ReglasNegocioEngine  # noqa: F401
    from src.engine.risk_scorer import calcular_score_hibrido    # noqa: F401
except ImportError:
    pass  # Módulos disponibles al ejecutar desde el contexto del backend
