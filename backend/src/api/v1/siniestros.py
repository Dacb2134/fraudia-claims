"""
GET  /api/v1/siniestros                   — lista priorizada con filtros
GET  /api/v1/siniestros/{id}              — detalle de un siniestro
POST /api/v1/siniestros/{id}/recalcular   — recalcula score en tiempo real
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from src.core.database import get_db
from src.engine.risk_scorer import calcular_score_hibrido

router = APIRouter()


@router.get("/")
def get_siniestros(
    db:          Session = Depends(get_db),
    nivel_riesgo: Optional[str] = Query(None, description="VERDE, AMARILLO o ROJO"),
    ramo:         Optional[str] = Query(None, description="Vehículos, Salud, Hogar, Vida, Generales"),
    sucursal:     Optional[str] = Query(None),
    page:         int = Query(1, ge=1),
    page_size:    int = Query(50, ge=1, le=500),
):
    """
    Lista de siniestros ordenados por score de riesgo descendente.
    Soporta filtros por nivel de riesgo, ramo y sucursal.
    """
    offset = (page - 1) * page_size

    # Construir filtros dinámicos
    filtros = []
    params  = {"limit": page_size, "offset": offset}

    if nivel_riesgo:
        filtros.append("sc.nivel_riesgo = :nivel_riesgo")
        params["nivel_riesgo"] = nivel_riesgo.upper()

    if ramo:
        filtros.append("s.ramo = :ramo")
        params["ramo"] = ramo

    if sucursal:
        filtros.append("s.sucursal = :sucursal")
        params["sucursal"] = sucursal

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    # Query principal
    query = text(f"""
        SELECT
            s.id_siniestro,
            s.id_asegurado,
            s.ramo,
            s.cobertura,
            s.fecha_ocurrencia,
            s.fecha_reporte,
            s.monto_reclamado,
            s.estado,
            s.sucursal,
            s.documentos_completos,
            s.tiene_doc_inconsistente,
            s.dias_entre_ocurrencia_reporte,
            s.historial_siniestros_asegurado,
            s.id_proveedor_beneficiario AS proveedor,
            sc.score_normalizado,
            sc.nivel_riesgo,
            sc.alertas_activadas
        FROM siniestros s
        LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        {where}
        ORDER BY sc.score_normalizado DESC
        LIMIT :limit OFFSET :offset
    """)

    # Total para paginación
    count_query = text(f"""
        SELECT COUNT(*) FROM siniestros s
        LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        {where}
    """)

    rows  = db.execute(query, params).mappings().all()
    total = db.execute(count_query, {k: v for k, v in params.items()
                                     if k not in ("limit", "offset")}).scalar()

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     -(-total // page_size),  # ceil division
        "data": [
            {
                "id_siniestro":                 row["id_siniestro"],
                "id_asegurado":                 row["id_asegurado"],
                "ramo":                         row["ramo"],
                "cobertura":                    row["cobertura"],
                "fecha_ocurrencia":             str(row["fecha_ocurrencia"]),
                "fecha_reporte":                str(row["fecha_reporte"]),
                "monto_reclamado":              float(row["monto_reclamado"]),
                "estado":                       row["estado"],
                "sucursal":                     row["sucursal"],
                "documentos_completos":         bool(row["documentos_completos"]),
                "tiene_doc_inconsistente":      bool(row["tiene_doc_inconsistente"]),
                "dias_reporte":                 row["dias_entre_ocurrencia_reporte"],
                "historial_siniestros":         row["historial_siniestros_asegurado"],
                "proveedor":                    row["proveedor"],
                "score_riesgo":                 row["score_normalizado"] or 0,
                "nivel_riesgo":                 row["nivel_riesgo"] or "VERDE",
                "alertas_activadas":            row["alertas_activadas"] or "",
            }
            for row in rows
        ],
    }


@router.get("/{id_siniestro}")
def get_siniestro_detalle(
    id_siniestro: str,
    db: Session = Depends(get_db),
):
    """Detalle completo de un siniestro con todas sus alertas."""

    row = db.execute(text("""
        SELECT
            s.*,
            sc.score_normalizado,
            sc.nivel_riesgo,
            sc.alertas_activadas,
            sc.reglas_criticas,
            sc.calculado_en,
            p.suma_asegurada,
            p.prima,
            p.fecha_inicio AS poliza_inicio,
            p.fecha_fin    AS poliza_fin,
            pr.tipo        AS tipo_proveedor,
            pr.en_lista_restrictiva,
            pr.pct_casos_observados
        FROM siniestros s
        LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        LEFT JOIN polizas p        ON s.id_poliza    = p.id_poliza
        LEFT JOIN proveedores pr   ON s.id_proveedor_beneficiario = pr.id_proveedor
        WHERE s.id_siniestro = :id
    """), {"id": id_siniestro}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Siniestro {id_siniestro} no encontrado")

    return {
        "id_siniestro":            row["id_siniestro"],
        "id_asegurado":            row["id_asegurado"],
        "id_poliza":               row["id_poliza"],
        "ramo":                    row["ramo"],
        "cobertura":               row["cobertura"],
        "fecha_ocurrencia":        str(row["fecha_ocurrencia"]),
        "fecha_reporte":           str(row["fecha_reporte"]),
        "monto_reclamado":         float(row["monto_reclamado"]),
        "monto_estimado":          float(row["monto_estimado"]),
        "monto_pagado":            float(row["monto_pagado"]),
        "estado":                  row["estado"],
        "sucursal":                row["sucursal"],
        "descripcion":             row["descripcion"],
        "documentos_completos":    bool(row["documentos_completos"]),
        "tiene_doc_inconsistente": bool(row["tiene_doc_inconsistente"]),
        "dias_reporte":            row["dias_entre_ocurrencia_reporte"],
        "historial_siniestros":    row["historial_siniestros_asegurado"],
        "poliza": {
            "suma_asegurada": float(row["suma_asegurada"] or 0),
            "prima":          float(row["prima"] or 0),
            "fecha_inicio":   str(row["poliza_inicio"]),
            "fecha_fin":      str(row["poliza_fin"]),
        },
        "proveedor": {
            "id":                   row["id_proveedor_beneficiario"],
            "tipo":                 row["tipo_proveedor"],
            "en_lista_restrictiva": bool(row["en_lista_restrictiva"]),
            "pct_casos_observados": float(row["pct_casos_observados"] or 0),
        },
        "score": {
            "valor":             row["score_normalizado"] or 0,
            "nivel":             row["nivel_riesgo"] or "VERDE",
            "alertas":           row["alertas_activadas"] or "",
            "reglas_criticas":   row["reglas_criticas"] or [],
            "calculado_en":      str(row["calculado_en"]) if row["calculado_en"] else None,
        },
    }


@router.post("/{id_siniestro}/recalcular")
def recalcular_score(id_siniestro: str, db: Session = Depends(get_db)):
    """
    Recalcula el score de riesgo en tiempo real aplicando el motor de reglas.
    Útil para la demo: muestra explicación detallada de cada señal activada.
    """
    row = db.execute(text("""
        SELECT
            s.*,
            p.suma_asegurada,
            p.fecha_inicio AS poliza_inicio,
            p.fecha_fin    AS poliza_fin,
            pr.en_lista_restrictiva,
            pr.pct_casos_observados
        FROM siniestros s
        LEFT JOIN polizas p     ON s.id_poliza = p.id_poliza
        LEFT JOIN proveedores pr ON s.id_proveedor_beneficiario = pr.id_proveedor
        WHERE s.id_siniestro = :id
    """), {"id": id_siniestro}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Siniestro {id_siniestro} no encontrado")

    siniestro_data = dict(row)
    proveedor_data = {
        "en_lista_restrictiva": row["en_lista_restrictiva"],
        "pct_casos_observados": row["pct_casos_observados"],
    }

    resultado = calcular_score_hibrido(siniestro=siniestro_data, proveedor=proveedor_data)

    # Persistir el score recalculado
    try:
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
            "id":      id_siniestro,
        })
        db.commit()
    except Exception:
        db.rollback()

    return {
        "id_siniestro":      id_siniestro,
        "score_normalizado": resultado["score_normalizado"],
        "nivel_riesgo":      resultado["nivel_riesgo"],
        "alertas_activadas": resultado["alertas_activadas"],
        "reglas_criticas":   resultado["reglas_criticas"],
        "total_alertas":     resultado["total_alertas"],
        "modo":              resultado["modo"],
        "detalle_senales":   [a for a in resultado["alertas_activadas"].split(" | ") if a],
    }
