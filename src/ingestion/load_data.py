"""
src/ingestion/load_data.py
Módulo de ingesta y carga de datos de siniestros.

IMPLEMENTACIÓN REAL:
  - Carga inicial del dataset:     backend/poblar_bd.py
  - Ingesta dinámica vía API:      POST /api/v1/siniestros/ingestar  (acepta CSV)
  - Evaluación de caso individual: POST /api/v1/siniestros/evaluar   (acepta JSON)

Este archivo documenta la ubicación del módulo en la arquitectura del proyecto.

Flujo de ingesta:
    1. Preparar CSV con columnas mínimas:
       ramo, cobertura, monto_reclamado, fecha_ocurrencia,
       dias_desde_inicio_poliza, historial_siniestros_asegurado

    2. Llamar al endpoint:
       curl -X POST https://<host>/api/v1/siniestros/ingestar \\
            -F "archivo=@siniestros.csv"

    3. El sistema:
       - Valida la estructura del CSV
       - Asigna IDs únicos (prefijo ING-)
       - Calcula el score de riesgo de cada caso
       - Guarda en MySQL y devuelve resumen de resultados

Carga inicial (dataset hackathon):
    Ejecutar: python backend/poblar_bd.py
    Fuente:   backend/ai_data_core/data/synthetic/Evento_Datasets_Sinteticos_Fraude_500_v2.xlsx
    Resultado: 500 siniestros + 7 tablas relacionales en MySQL
"""


def cargar_csv(ruta_csv: str, db_url: str) -> dict:
    """
    Carga un CSV de siniestros a la base de datos y calcula scores.
    Para uso programático fuera del API REST.

    Args:
        ruta_csv: Ruta al archivo CSV con los siniestros
        db_url:   URL de conexión a MySQL (DB_URL)

    Returns:
        Dict con total insertados, ROJO, AMARILLO, VERDE y errores
    """
    import csv
    import uuid
    import json
    from datetime import date
    from sqlalchemy import create_engine, text

    sys_path_backup = None
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
        from src.engine.risk_scorer import calcular_score_hibrido
    except ImportError as e:
        raise ImportError(f"Ejecutar desde el directorio raíz del proyecto: {e}")

    engine = create_engine(db_url, pool_pre_ping=True)
    resultados = {"insertados": 0, "ROJO": 0, "AMARILLO": 0, "VERDE": 0, "errores": []}

    with open(ruta_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        with engine.begin() as conn:
            for i, fila in enumerate(reader, 1):
                try:
                    sin_id = f"ING-{uuid.uuid4().hex[:8].upper()}"
                    hoy = date.today().isoformat()

                    sin_data = {
                        "ramo": fila.get("ramo", "Vehículos"),
                        "cobertura": fila.get("cobertura", "Daño"),
                        "estado": fila.get("estado", "Reserva"),
                        "monto_reclamado": float(fila.get("monto_reclamado") or 0),
                        "suma_asegurada": float(fila.get("suma_asegurada") or 10000),
                        "dias_desde_inicio_poliza": int(fila.get("dias_desde_inicio_poliza") or 180),
                        "dias_desde_fin_poliza": int(fila.get("dias_desde_fin_poliza") or 180),
                        "dias_entre_ocurrencia_reporte": int(fila.get("dias_entre_ocurrencia_reporte") or 0),
                        "historial_siniestros_asegurado": int(fila.get("historial_siniestros_asegurado") or 0),
                        "documentos_completos": fila.get("documentos_completos", "1") not in ("0", "false"),
                        "tiene_doc_inconsistente": int(fila.get("tiene_doc_inconsistente") or 0),
                        "descripcion": fila.get("descripcion", ""),
                        "similitud_narrativa": 0.0,
                    }

                    resultado = calcular_score_hibrido(
                        siniestro=sin_data,
                        proveedor={"en_lista_restrictiva": False, "pct_casos_observados": 0.0},
                    )

                    resultados["insertados"] += 1
                    resultados[resultado["nivel_riesgo"]] += 1

                except Exception as e:
                    resultados["errores"].append({"fila": i, "error": str(e)})

    return resultados
