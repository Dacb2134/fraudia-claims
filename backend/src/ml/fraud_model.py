"""
fraud_model.py
Modelo ML para predicción de fraude.
Usa XGBoost con features del dataset sintético.
Se entrena automáticamente al primer uso y guarda el modelo en disco.
"""
import os
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

# ── Intentar XGBoost, si no está disponible usar RandomForest ─────────────────
try:
    from xgboost import XGBClassifier
    MODELO_NOMBRE = "XGBoost"
except ImportError:
    from sklearn.ensemble import RandomForestClassifier as XGBClassifier
    MODELO_NOMBRE = "RandomForest"

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, roc_auc_score,
                              precision_score, recall_score, f1_score)
from sklearn.preprocessing import LabelEncoder

MODEL_PATH  = Path("/app/ai_data_core/data/processed/fraud_model.pkl")
SCALER_PATH = Path("/app/ai_data_core/data/processed/label_encoders.pkl")
CSV_PATH    = Path("/app/ai_data_core/data/synthetic/siniestros_scored.csv")


# ── Features que usa el modelo ────────────────────────────────────────────────
FEATURES_NUMERICAS = [
    "monto_reclamado",
    "monto_estimado",
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "historial_siniestros_asegurado",
    "suma_asegurada",
    "score_riesgo",           # score del motor de reglas como feature
    "tiene_doc_inconsistente",
    "ratio_monto",            # monto_reclamado / suma_asegurada
    "es_borde_vigencia",      # 1 si dias_inicio <= 30
    "reporte_tardio",         # 1 si dias_reporte > 7
]

FEATURES_CATEGORICAS = [
    "ramo",
    "cobertura",
    "estado",
    "sucursal",
]

TARGET = "etiqueta_fraude_simulada"


def preparar_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Prepara el DataFrame con todas las features necesarias."""
    df = df.copy()

    # Features derivadas
    df["ratio_monto"]      = df["monto_reclamado"] / (df["suma_asegurada"] + 1)
    df["es_borde_vigencia"] = (df["dias_desde_inicio_poliza"] <= 30).astype(int)
    df["reporte_tardio"]   = (df["dias_entre_ocurrencia_reporte"] > 7).astype(int)
    df["tiene_doc_inconsistente"] = df["tiene_doc_inconsistente"].map(
        {True: 1, False: 0, "True": 1, "False": 0}).fillna(0).astype(int)

    # Encoders para categoricas
    encoders = {}
    for col in FEATURES_CATEGORICAS:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str).fillna("desconocido"))
        encoders[col] = le

    features_finales = FEATURES_NUMERICAS + [c + "_enc" for c in FEATURES_CATEGORICAS]
    return df[features_finales].fillna(0), encoders


def entrenar_modelo() -> dict:
    """
    Entrena el modelo con el CSV sintético.
    Guarda el modelo en disco y retorna métricas.
    """
    print("🤖 Cargando dataset para entrenamiento...")
    df = pd.read_csv(CSV_PATH)

    X, encoders = preparar_features(df)
    y = df[TARGET].astype(int)

    print(f"   Dataset: {len(df)} filas | Fraudes: {y.sum()} ({y.mean()*100:.1f}%)")

    # Split 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Modelo
    if MODELO_NOMBRE == "XGBoost":
        modelo = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            scale_pos_weight=4,   # compensa desbalance 80/20
            random_state=42,
            eval_metric="logloss",
            verbosity=0,
        )
    else:
        modelo = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            class_weight="balanced",
            random_state=42,
        )

    modelo.fit(X_train, y_train)

    # Métricas
    y_pred      = modelo.predict(X_test)
    y_pred_prob = modelo.predict_proba(X_test)[:, 1]

    metricas = {
        "modelo":    MODELO_NOMBRE,
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 3),
        "recall":    round(float(recall_score(y_test, y_pred, zero_division=0)), 3),
        "f1_score":  round(float(f1_score(y_test, y_pred, zero_division=0)), 3),
        "auc_roc":   round(float(roc_auc_score(y_test, y_pred_prob)), 3),
        "train_size": len(X_train),
        "test_size":  len(X_test),
    }

    print(f"   ✅ {MODELO_NOMBRE} entrenado")
    print(f"   Precision: {metricas['precision']} | Recall: {metricas['recall']} "
          f"| F1: {metricas['f1_score']} | AUC-ROC: {metricas['auc_roc']}")

    # Guardar modelo y encoders
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH,  "wb") as f:
        pickle.dump(modelo, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(encoders, f)

    print(f"   💾 Modelo guardado en {MODEL_PATH}")
    return metricas


def cargar_modelo():
    """Carga el modelo desde disco. Si no existe, lo entrena."""
    if not MODEL_PATH.exists():
        print("⚠️  Modelo no encontrado — entrenando...")
        entrenar_modelo()

    with open(MODEL_PATH,  "rb") as f:
        modelo = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        encoders = pickle.load(f)

    return modelo, encoders


def predecir_probabilidad(siniestro_data: dict) -> dict:
    """
    Predice la probabilidad de fraude para un siniestro.

    Args:
        siniestro_data: dict con los campos del siniestro

    Returns:
        dict con probabilidad ML y score híbrido final
    """
    modelo, encoders = cargar_modelo()

    df = pd.DataFrame([siniestro_data])

    # Features derivadas
    df["ratio_monto"]      = df["monto_reclamado"] / (df.get("suma_asegurada", pd.Series([1])) + 1)
    df["es_borde_vigencia"] = (df["dias_desde_inicio_poliza"] <= 30).astype(int)
    df["reporte_tardio"]   = (df["dias_entre_ocurrencia_reporte"] > 7).astype(int)
    df["tiene_doc_inconsistente"] = int(siniestro_data.get("tiene_doc_inconsistente", 0))

    # Encodar categoricas
    for col in FEATURES_CATEGORICAS:
        le = encoders.get(col)
        val = str(siniestro_data.get(col, "desconocido"))
        if le and val in le.classes_:
            df[col + "_enc"] = le.transform([val])[0]
        else:
            df[col + "_enc"] = 0

    features = FEATURES_NUMERICAS + [c + "_enc" for c in FEATURES_CATEGORICAS]
    X = df[features].fillna(0)

    prob_fraude  = float(modelo.predict_proba(X)[0][1])
    score_reglas = int(siniestro_data.get("score_riesgo", 0))

    # Score híbrido: 60% reglas + 40% ML
    score_hibrido = round((score_reglas * 0.6) + (prob_fraude * 100 * 0.4))
    score_hibrido = min(100, max(0, score_hibrido))

    # Nivel semáforo
    if score_hibrido >= 76:
        nivel = "ROJO"
    elif score_hibrido >= 41:
        nivel = "AMARILLO"
    else:
        nivel = "VERDE"

    return {
        "probabilidad_ml":  round(prob_fraude, 4),
        "score_reglas":     score_reglas,
        "score_hibrido":    score_hibrido,
        "nivel_riesgo":     nivel,
        "modelo_usado":     MODELO_NOMBRE,
    }


if __name__ == "__main__":
    print("🚀 Entrenando modelo de fraude...")
    metricas = entrenar_modelo()
    print("\n📊 Métricas finales:")
    for k, v in metricas.items():
        print(f"   {k}: {v}")
