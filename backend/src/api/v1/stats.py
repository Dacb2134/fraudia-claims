"""
GET /api/v1/stats
Estadísticas consolidadas para el dashboard principal.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db

router = APIRouter()


@router.get("/")
def get_stats(db: Session = Depends(get_db)):
    """
    Retorna KPIs principales para el dashboard:
    - Total de siniestros y distribución por semáforo
    - Distribución por ramo
    - Top 5 proveedores con más alertas
    - Top 5 asegurados con más siniestros
    - Monto total en riesgo por nivel
    """

    # ── 1. Totales por nivel de riesgo ────────────────────────────────────────
    niveles = db.execute(text("""
        SELECT
            nivel_riesgo,
            COUNT(*) AS total,
            COALESCE(SUM(s.monto_reclamado), 0) AS monto_total
        FROM scores_riesgo sc
        JOIN siniestros s ON sc.id_siniestro = s.id_siniestro
        GROUP BY nivel_riesgo
    """)).mappings().all()

    semaforo = {"VERDE": 0, "AMARILLO": 0, "ROJO": 0}
    montos   = {"VERDE": 0.0, "AMARILLO": 0.0, "ROJO": 0.0}
    for row in niveles:
        semaforo[row["nivel_riesgo"]] = row["total"]
        montos[row["nivel_riesgo"]]   = float(row["monto_total"])

    total_siniestros = sum(semaforo.values())

    # ── 2. Distribución por ramo ──────────────────────────────────────────────
    ramos = db.execute(text("""
        SELECT ramo, COUNT(*) AS total
        FROM siniestros
        GROUP BY ramo
        ORDER BY total DESC
    """)).mappings().all()

    # ── 3. Top 5 proveedores con más siniestros ROJO ──────────────────────────
    top_proveedores = db.execute(text("""
        SELECT
            s.id_proveedor_beneficiario AS proveedor,
            COUNT(*) AS total_alertas,
            SUM(CASE WHEN sc.nivel_riesgo = 'ROJO' THEN 1 ELSE 0 END) AS alertas_rojas
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        WHERE s.id_proveedor_beneficiario IS NOT NULL
        GROUP BY s.id_proveedor_beneficiario
        ORDER BY alertas_rojas DESC, total_alertas DESC
        LIMIT 5
    """)).mappings().all()

    # ── 4. Top 5 asegurados con más siniestros ────────────────────────────────
    top_asegurados = db.execute(text("""
        SELECT
            s.id_asegurado,
            COUNT(*) AS total_siniestros,
            MAX(sc.score_normalizado) AS score_max,
            SUM(s.monto_reclamado) AS monto_total
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        GROUP BY s.id_asegurado
        ORDER BY total_siniestros DESC, score_max DESC
        LIMIT 5
    """)).mappings().all()

    # ── 5. Distribución por sucursal ──────────────────────────────────────────
    sucursales = db.execute(text("""
        SELECT
            s.sucursal,
            COUNT(*) AS total,
            SUM(CASE WHEN sc.nivel_riesgo = 'ROJO' THEN 1 ELSE 0 END) AS rojos
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        GROUP BY s.sucursal
        ORDER BY rojos DESC
    """)).mappings().all()

    # ── 6. Score promedio general ─────────────────────────────────────────────
    score_promedio = db.execute(text("""
        SELECT ROUND(AVG(score_normalizado), 1) AS promedio
        FROM scores_riesgo
    """)).scalar() or 0

    # ── Armar respuesta ───────────────────────────────────────────────────────
    return {
        "resumen": {
            "total_siniestros":   total_siniestros,
            "score_promedio":     float(score_promedio),
            "monto_total_riesgo": sum(montos.values()),
        },
        "semaforo": {
            "verde":    {"total": semaforo["VERDE"],    "monto": montos["VERDE"]},
            "amarillo": {"total": semaforo["AMARILLO"], "monto": montos["AMARILLO"]},
            "rojo":     {"total": semaforo["ROJO"],     "monto": montos["ROJO"]},
        },
        "por_ramo": [
            {"ramo": r["ramo"], "total": r["total"]}
            for r in ramos
        ],
        "top_proveedores": [
            {
                "proveedor":     row["proveedor"],
                "total_alertas": row["total_alertas"],
                "alertas_rojas": row["alertas_rojas"],
            }
            for row in top_proveedores
        ],
        "top_asegurados": [
            {
                "id_asegurado":    row["id_asegurado"],
                "total_siniestros": row["total_siniestros"],
                "score_max":       row["score_max"],
                "monto_total":     float(row["monto_total"]),
            }
            for row in top_asegurados
        ],
        "por_sucursal": [
            {
                "sucursal": row["sucursal"],
                "total":    row["total"],
                "rojos":    row["rojos"],
            }
            for row in sucursales
        ],
    }
