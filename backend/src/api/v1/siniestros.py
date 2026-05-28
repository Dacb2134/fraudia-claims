from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from src.core.database import get_db
from src.api.schemas import SiniestroResponse
from src.engine.rules_evaluator import ReglasNegocioEngine

router = APIRouter()

@router.get('/', response_model=List[SiniestroResponse])
def get_siniestros(db: Session = Depends(get_db)):
    # 1. Consultar siniestros crudos desde MySQL usando SQL nativo para mayor velocidad
    query = text("""
        SELECT 
            s.id_siniestro, s.cobertura, s.monto_reclamado, s.estado, s.fecha_ocurrencia, s.fecha_reporte,
            a.reclamos_ultimos_12_meses
        FROM siniestros s
        JOIN asegurados a ON s.id_asegurado = a.id_asegurado
        LIMIT 50;
    """)
    resultados = db.execute(query).mappings().all()
    
    siniestros_evaluados = []
    
    # 2. Pasar cada siniestro por el Motor de Reglas
    for fila in resultados:
        # Extraer datos para el motor
        siniestro_data = dict(fila)
        historial = fila['reclamos_ultimos_12_meses']
        
        # Instanciar y ejecutar el motor determinista
        motor = ReglasNegocioEngine(siniestro_data=siniestro_data, historial_asegurado=historial)
        resultado_reglas = motor.ejecutar_motor()
        
        # 3. Formatear la respuesta para el Frontend (Contrato JSON)
        siniestros_evaluados.append({
            "id_siniestro": fila["id_siniestro"],
            "cobertura": fila["cobertura"],
            "monto_reclamado": float(fila["monto_reclamado"]),
            "score_riesgo": resultado_reglas["score_riesgo"],
            "nivel_riesgo": resultado_reglas["nivel_riesgo"],
            "explicacion_ia": f"Alertas activadas: {resultado_reglas['alertas_activadas']}"
        })
        
    # Ordenar para que los de mayor riesgo (Rojos) salgan primero en el dashboard
    siniestros_evaluados.sort(key=lambda x: x["score_riesgo"], reverse=True)
        
    return siniestros_evaluados
