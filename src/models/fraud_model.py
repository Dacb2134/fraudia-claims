"""
src/models/fraud_model.py
Modelo de Machine Learning para predicción de posible fraude.

IMPLEMENTACIÓN REAL: backend/src/ml/fraud_model.py

Este archivo documenta la ubicación del módulo en la arquitectura del proyecto.

Algoritmo:     XGBoost (fallback: RandomForest si XGBoost no disponible)
Target:        etiqueta_fraude_simulada (0=normal, 1=fraude simulado)
Score híbrido: 60% reglas de negocio + 40% predicción ML

Features numéricas (12):
    monto_reclamado, monto_estimado, dias_desde_inicio_poliza,
    dias_desde_fin_poliza, dias_entre_ocurrencia_reporte,
    historial_siniestros_asegurado, suma_asegurada, score_riesgo,
    tiene_doc_inconsistente, ratio_monto, es_borde_vigencia, reporte_tardio

Features categóricas (4):
    ramo, cobertura, estado, sucursal  (codificadas con LabelEncoder)

Métricas en dataset sintético (evaluación):
    Precisión:  1.000  (0 falsos positivos en test set)
    Recall:     0.833  (detecta 83.3% de fraudes)
    F1-Score:   0.909
    AUC-ROC:    0.988

Entrenamiento:
    POST /api/v1/ml/entrenar     → Reentrena desde MySQL (Railway-compatible)
    Estado:    GET /api/v1/ml/estado
    Predicción: POST /api/v1/ml/predecir

Uso directo:
    import sys; sys.path.insert(0, 'backend')
    from src.ml.fraud_model import entrenar_modelo_desde_bd, predecir_probabilidad
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from src.ml.fraud_model import (           # noqa: F401
        entrenar_modelo_desde_bd,
        predecir_probabilidad,
        cargar_modelo,
        MODELO_NOMBRE,
    )
except ImportError:
    pass  # Módulos disponibles al ejecutar desde el contexto del backend
