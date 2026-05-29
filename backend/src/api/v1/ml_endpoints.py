"""
GET  /api/v1/ml/estado      — estado y métricas del modelo
POST /api/v1/ml/entrenar    — entrenar/reentrenar el modelo
POST /api/v1/ml/predecir    — predecir probabilidad de fraude
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.core.database import get_db
from src.ml.fraud_model import (entrenar_modelo_desde_bd, predecir_probabilidad,
                                 MODEL_PATH, MODELO_NOMBRE)

router = APIRouter()


class PredecirRequest(BaseModel):
    id_siniestro: str | None = None   # si se manda, busca en BD
    # O campos directos para predicción sin BD:
    monto_reclamado:               float | None = None
    monto_estimado:                float | None = None
    dias_desde_inicio_poliza:      int   | None = None
    dias_desde_fin_poliza:         int   | None = None
    dias_entre_ocurrencia_reporte: int   | None = None
    historial_siniestros_asegurado: int  | None = None
    suma_asegurada:                float | None = None
    score_riesgo:                  int   | None = None
    tiene_doc_inconsistente:       int   | None = None
    ramo:                          str   | None = None
    cobertura:                     str   | None = None
    estado:                        str   | None = None
    sucursal:                      str   | None = None


@router.get("/estado")
def estado_modelo():
    """Retorna si el modelo está entrenado y sus métricas básicas."""
    existe = MODEL_PATH.exists()
    return {
        "modelo_entrenado": existe,
        "tipo_modelo":      MODELO_NOMBRE,
        "ruta":             str(MODEL_PATH),
        "mensaje":          "Listo" if existe else "Ejecuta POST /ml/entrenar primero",
    }


@router.post("/entrenar")
def entrenar(db: Session = Depends(get_db)):
    """
    Entrena o reentrena el modelo.
    Usa datos de la base de datos MySQL (funciona en Railway sin CSV).
    """
    try:
        metricas = entrenar_modelo_desde_bd(db)
        return {
            "mensaje":  "✅ Modelo entrenado correctamente desde la base de datos",
            "metricas": metricas,
            "fuente":   "MySQL",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error entrenando [{type(e).__name__}]: {e}")


@router.post("/predecir")
def predecir(request: PredecirRequest, db: Session = Depends(get_db)):
    """
    Predice probabilidad de fraude.
    Si se manda id_siniestro, busca los datos en la BD.
    Si no, usa los campos del request directamente.
    """
    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail="Modelo no entrenado. Ejecuta POST /api/v1/ml/entrenar primero."
        )

    # Obtener datos del siniestro
    if request.id_siniestro:
        row = db.execute(text("""
            SELECT s.*, sc.score_normalizado AS score_riesgo, p.suma_asegurada
            FROM siniestros s
            LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
            LEFT JOIN polizas p        ON s.id_poliza    = p.id_poliza
            WHERE s.id_siniestro = :id
        """), {"id": request.id_siniestro}).mappings().first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Siniestro {request.id_siniestro} no encontrado"
            )
        datos = dict(row)
    else:
        # Usar campos del request
        datos = {
            "monto_reclamado":               request.monto_reclamado or 0,
            "monto_estimado":                request.monto_estimado or 0,
            "dias_desde_inicio_poliza":      request.dias_desde_inicio_poliza or 0,
            "dias_desde_fin_poliza":         request.dias_desde_fin_poliza or 0,
            "dias_entre_ocurrencia_reporte": request.dias_entre_ocurrencia_reporte or 0,
            "historial_siniestros_asegurado": request.historial_siniestros_asegurado or 0,
            "suma_asegurada":                request.suma_asegurada or 1,
            "score_riesgo":                  request.score_riesgo or 0,
            "tiene_doc_inconsistente":       request.tiene_doc_inconsistente or 0,
            "ramo":                          request.ramo or "Generales",
            "cobertura":                     request.cobertura or "Daño",
            "estado":                        request.estado or "Reserva",
            "sucursal":                      request.sucursal or "Quito Norte",
        }

    try:
        resultado = predecir_probabilidad(datos)
        if request.id_siniestro:
            resultado["id_siniestro"] = request.id_siniestro
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


@router.get("/importancia-features")
def importancia_features():
    """Retorna qué variables son más importantes para el modelo."""
    import pickle
    from src.ml.fraud_model import SCALER_PATH
    from src.ml.fraud_model import FEATURES_NUMERICAS, FEATURES_CATEGORICAS

    if not MODEL_PATH.exists():
        raise HTTPException(status_code=400, detail="Modelo no entrenado")

    with open(MODEL_PATH, "rb") as f:
        modelo = pickle.load(f)

    feature_names = FEATURES_NUMERICAS + [c + "_enc" for c in FEATURES_CATEGORICAS]

    if hasattr(modelo, "feature_importances_"):
        importancias = modelo.feature_importances_
        resultado = sorted(
            [{"feature": n, "importancia": round(float(v), 4)}
             for n, v in zip(feature_names, importancias)],
            key=lambda x: x["importancia"],
            reverse=True,
        )
        return {"features": resultado}
    else:
        return {"mensaje": "Este modelo no soporta importancia de features"}
