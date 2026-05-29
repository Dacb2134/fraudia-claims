"""
POST /api/v1/admin/seed-casos-rojo  — Activa 8 casos de demo en nivel ROJO
POST /api/v1/admin/reset-scores     — Recalcula todos los scores desde cero
"""
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db
from src.engine.risk_scorer import calcular_score_hibrido

router_admin = APIRouter()

# Campos que combinados producen score_bruto = 73 → normalizado = 81 → ROJO
# RF-01(+20) S-11(+10) S-07(+10) S-03(+8) S-01(+8) S-02(+8) S-12(+5) S-08(+4)
_CAMPOS_ROJO = {
    "cobertura":                     "Robo Total",
    "estado":                        "Pérdida Total por Robo",
    "tiene_doc_inconsistente":        1,
    "documentos_completos":           0,
    "historial_siniestros_asegurado": 5,
    "dias_desde_inicio_poliza":       5,
    "dias_desde_fin_poliza":          60,
    "dias_entre_ocurrencia_reporte":  12,
}


@router_admin.post("/seed-casos-rojo")
def seed_casos_rojo(db: Session = Depends(get_db)):
    """
    Actualiza los primeros 8 siniestros para que lleguen a ROJO.
    Útil para el demo del hackathon — ejecutar una vez.
    """
    # Encontrar proveedor en lista restrictiva
    prov_id = db.execute(text(
        "SELECT id_proveedor FROM proveedores WHERE en_lista_restrictiva = 1 LIMIT 1"
    )).scalar()

    if not prov_id:
        prov_id = db.execute(text(
            "SELECT id_proveedor FROM proveedores ORDER BY id_proveedor LIMIT 1"
        )).scalar()
        if prov_id:
            db.execute(text(
                "UPDATE proveedores SET en_lista_restrictiva = 1 WHERE id_proveedor = :id"
            ), {"id": prov_id})

    # Tomar los primeros 8 siniestros
    ids = [r[0] for r in db.execute(text(
        "SELECT id_siniestro FROM siniestros ORDER BY id_siniestro LIMIT 8"
    )).fetchall()]

    # Actualizar campos
    for sin_id in ids:
        db.execute(text("""
            UPDATE siniestros SET
                cobertura                       = :cobertura,
                estado                          = :estado,
                tiene_doc_inconsistente         = :tiene_doc,
                documentos_completos            = :docs,
                historial_siniestros_asegurado  = :historial,
                dias_desde_inicio_poliza        = :dias_ini,
                dias_desde_fin_poliza           = :dias_fin,
                dias_entre_ocurrencia_reporte   = :dias_rep,
                id_proveedor_beneficiario       = :proveedor
            WHERE id_siniestro = :id
        """), {
            "cobertura": _CAMPOS_ROJO["cobertura"],
            "estado":    _CAMPOS_ROJO["estado"],
            "tiene_doc": _CAMPOS_ROJO["tiene_doc_inconsistente"],
            "docs":      _CAMPOS_ROJO["documentos_completos"],
            "historial": _CAMPOS_ROJO["historial_siniestros_asegurado"],
            "dias_ini":  _CAMPOS_ROJO["dias_desde_inicio_poliza"],
            "dias_fin":  _CAMPOS_ROJO["dias_desde_fin_poliza"],
            "dias_rep":  _CAMPOS_ROJO["dias_entre_ocurrencia_reporte"],
            "proveedor": prov_id,
            "id":        sin_id,
        })

    # Recalcular scores
    resultados = []
    for sin_id in ids:
        row = db.execute(text("""
            SELECT s.*, p.suma_asegurada,
                   pr.en_lista_restrictiva, pr.pct_casos_observados
            FROM siniestros s
            LEFT JOIN polizas p      ON s.id_poliza                 = p.id_poliza
            LEFT JOIN proveedores pr ON s.id_proveedor_beneficiario = pr.id_proveedor
            WHERE s.id_siniestro = :id
        """), {"id": sin_id}).mappings().first()

        if not row:
            continue

        resultado = calcular_score_hibrido(
            siniestro=dict(row),
            proveedor={
                "en_lista_restrictiva": row["en_lista_restrictiva"],
                "pct_casos_observados": row["pct_casos_observados"],
            },
        )

        try:
            db.execute(text("""
                UPDATE scores_riesgo
                SET score_normalizado = :score,
                    nivel_riesgo      = :nivel,
                    alertas_activadas = :alertas,
                    reglas_criticas   = :reglas,
                    calculado_en      = NOW()
                WHERE id_siniestro = :id
            """), {
                "score":   resultado["score_normalizado"],
                "nivel":   resultado["nivel_riesgo"],
                "alertas": resultado["alertas_activadas"],
                "reglas":  json.dumps(resultado.get("reglas_criticas", []), ensure_ascii=False),
                "id":      sin_id,
            })
        except Exception:
            db.execute(text("""
                UPDATE scores_riesgo
                SET score_normalizado = :score,
                    nivel_riesgo      = :nivel,
                    alertas_activadas = :alertas,
                    calculado_en      = NOW()
                WHERE id_siniestro = :id
            """), {
                "score":   resultado["score_normalizado"],
                "nivel":   resultado["nivel_riesgo"],
                "alertas": resultado["alertas_activadas"],
                "id":      sin_id,
            })

        resultados.append({
            "id":    sin_id,
            "score": resultado["score_normalizado"],
            "nivel": resultado["nivel_riesgo"],
        })

    db.commit()

    rojos = sum(1 for r in resultados if r["nivel"] == "ROJO")
    return {
        "mensaje":         f"✅ {len(resultados)} siniestros actualizados · {rojos} llegaron a ROJO",
        "proveedor_usado": prov_id,
        "casos":           resultados,
    }
