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

MODEL_PATH  = Path("/app/backend/ai_data_core/data/processed/fraud_model.pkl")
SCALER_PATH = Path("/app/backend/ai_data_core/data/processed/label_encoders.pkl")
CSV_PATH    = Path("/app/backend/ai_data_core/data/synthetic/siniestros_scored.csv")


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


def _entrenar_con_df(df: pd.DataFrame) -> dict:
    """Lógica interna de entrenamiento a partir de un DataFrame ya cargado."""
    X, encoders = preparar_features(df)
    y = df[TARGET].astype(int)

    print(f"   Dataset: {len(df)} filas | Fraudes: {y.sum()} ({y.mean()*100:.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if MODELO_NOMBRE == "XGBoost":
        modelo = XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            scale_pos_weight=4, random_state=42, eval_metric="logloss", verbosity=0,
        )
    else:
        modelo = RandomForestClassifier(
            n_estimators=100, max_depth=6, class_weight="balanced", random_state=42,
        )

    modelo.fit(X_train, y_train)
    y_pred      = modelo.predict(X_test)
    y_pred_prob = modelo.predict_proba(X_test)[:, 1]

    metricas = {
        "modelo":     MODELO_NOMBRE,
        "precision":  round(float(precision_score(y_test, y_pred, zero_division=0)), 3),
        "recall":     round(float(recall_score(y_test, y_pred, zero_division=0)), 3),
        "f1_score":   round(float(f1_score(y_test, y_pred, zero_division=0)), 3),
        "auc_roc":    round(float(roc_auc_score(y_test, y_pred_prob)), 3),
        "train_size": len(X_train),
        "test_size":  len(X_test),
        "total_filas": len(df),
    }
    print(f"   ✅ {MODELO_NOMBRE} | Precision: {metricas['precision']} | Recall: {metricas['recall']} | AUC-ROC: {metricas['auc_roc']}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH,  "wb") as f: pickle.dump(modelo, f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(encoders, f)
    print(f"   💾 Modelo guardado en {MODEL_PATH}")
    return metricas


def entrenar_modelo() -> dict:
    """
    Entrena el modelo. Intenta CSV primero; si no existe, falla con mensaje claro.
    Usar entrenar_modelo_desde_bd() para entrenar desde MySQL.
    """
    print("🤖 Cargando dataset para entrenamiento...")
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset CSV no encontrado en {CSV_PATH}. "
            "Usa el endpoint con soporte de BD o sube el archivo siniestros_scored.csv."
        )
    df = pd.read_csv(CSV_PATH)

    return _entrenar_con_df(df)


def entrenar_modelo_desde_bd(db_session) -> dict:
    """
    Entrena el modelo usando datos directamente de MySQL.
    Funciona en Railway y cualquier entorno sin archivos CSV.
    """
    from sqlalchemy import text as sql_text
    print("🤖 Cargando datos desde la base de datos MySQL...")
    rows = db_session.execute(sql_text("""
        SELECT
            s.monto_reclamado,
            s.monto_estimado,
            COALESCE(s.dias_desde_inicio_poliza, 0)        AS dias_desde_inicio_poliza,
            COALESCE(s.dias_desde_fin_poliza, 0)           AS dias_desde_fin_poliza,
            COALESCE(s.dias_entre_ocurrencia_reporte, 0)   AS dias_entre_ocurrencia_reporte,
            COALESCE(s.historial_siniestros_asegurado, 0)  AS historial_siniestros_asegurado,
            COALESCE(s.tiene_doc_inconsistente, 0)         AS tiene_doc_inconsistente,
            s.ramo, s.cobertura, s.estado, s.sucursal,
            COALESCE(sc.score_normalizado, 0)              AS score_riesgo,
            COALESCE(p.suma_asegurada, 0)                  AS suma_asegurada,
            COALESCE(s.etiqueta_fraude_simulada, 0)        AS etiqueta_fraude_simulada
        FROM siniestros s
        LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        LEFT JOIN polizas p        ON s.id_poliza    = p.id_poliza
    """)).mappings().all()

    df = pd.DataFrame([dict(r) for r in rows])
    if len(df) < 20:
        raise ValueError(f"Solo {len(df)} registros en BD. Se necesitan ≥20 para entrenar.")
    return _entrenar_con_df(df)


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
