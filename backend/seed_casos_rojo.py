"""
seed_casos_rojo.py
Actualiza los primeros 8 siniestros con condiciones que disparan RF-01
(Pérdida Total por Robo) y los llevan a nivel ROJO (score ≥ 76).

Uso:
  docker-compose exec api python seed_casos_rojo.py
  python seed_casos_rojo.py          (Railway Shell)
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("Falta DB_URL en .env")

engine = create_engine(DB_URL, pool_pre_ping=True)

# Combinación que produce score_bruto = 73 → normalizado = 81 → ROJO
# RF-01(+20) S-11(+10) S-07(+10) S-03(+8) S-01(+8) S-02(+8) S-12(+5) S-08(+4) = 73
CAMPOS_ROJO = {
    "cobertura":                     "Robo Total",               # RF-01 + S-02
    "estado":                        "Pérdida Total por Robo",   # RF-01
    "tiene_doc_inconsistente":        1,                         # S-11: +10
    "documentos_completos":           0,                         # S-08: +4
    "historial_siniestros_asegurado": 5,                         # S-03: +8
    "dias_desde_inicio_poliza":       5,                         # S-01 ≤10: +8
    "dias_desde_fin_poliza":          60,
    "dias_entre_ocurrencia_reporte":  12,                        # S-12: +5, S-02 robo >4d: +8
}


def main():
    from src.engine.risk_scorer import calcular_score_hibrido

    with engine.begin() as conn:
        # 1. Encontrar proveedor en lista restrictiva (S-07: +10)
        prov_id = conn.execute(text(
            "SELECT id_proveedor FROM proveedores WHERE en_lista_restrictiva = 1 LIMIT 1"
        )).scalar()

        if not prov_id:
            print("⚠️  Sin proveedor restrictivo — marcando el primero como restrictivo...")
            prov_id = conn.execute(text(
                "SELECT id_proveedor FROM proveedores ORDER BY id_proveedor LIMIT 1"
            )).scalar()
            if prov_id:
                conn.execute(text(
                    "UPDATE proveedores SET en_lista_restrictiva = 1 WHERE id_proveedor = :id"
                ), {"id": prov_id})

        if not prov_id:
            print("❌ No hay proveedores en la BD. Pobla primero con poblar_bd.py")
            return

        print(f"✅ Proveedor restrictivo: {prov_id}")

        # 2. Tomar los primeros 8 siniestros
        ids = [r[0] for r in conn.execute(text(
            "SELECT id_siniestro FROM siniestros ORDER BY id_siniestro LIMIT 8"
        )).fetchall()]

        if not ids:
            print("❌ No hay siniestros en la BD")
            return

        print(f"📋 Siniestros a actualizar: {ids}")

        # 3. Actualizar campos en siniestros
        for sin_id in ids:
            conn.execute(text("""
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
                "cobertura": CAMPOS_ROJO["cobertura"],
                "estado":    CAMPOS_ROJO["estado"],
                "tiene_doc": CAMPOS_ROJO["tiene_doc_inconsistente"],
                "docs":      CAMPOS_ROJO["documentos_completos"],
                "historial": CAMPOS_ROJO["historial_siniestros_asegurado"],
                "dias_ini":  CAMPOS_ROJO["dias_desde_inicio_poliza"],
                "dias_fin":  CAMPOS_ROJO["dias_desde_fin_poliza"],
                "dias_rep":  CAMPOS_ROJO["dias_entre_ocurrencia_reporte"],
                "proveedor": prov_id,
                "id":        sin_id,
            })

        print(f"✅ {len(ids)} siniestros actualizados")

        # 4. Recalcular score de cada uno
        print("\n🔄 Recalculando scores...")
        for sin_id in ids:
            row = conn.execute(text("""
                SELECT s.*, p.suma_asegurada,
                       pr.en_lista_restrictiva, pr.pct_casos_observados
                FROM siniestros s
                LEFT JOIN polizas p       ON s.id_poliza                 = p.id_poliza
                LEFT JOIN proveedores pr  ON s.id_proveedor_beneficiario = pr.id_proveedor
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

            # Actualizar score en BD
            try:
                reglas_json = json.dumps(resultado.get("reglas_criticas", []), ensure_ascii=False)
                conn.execute(text("""
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
                    "reglas":  reglas_json,
                    "id":      sin_id,
                })
            except Exception:
                conn.execute(text("""
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

            nivel = resultado["nivel_riesgo"]
            score = resultado["score_normalizado"]
            icono = "🔴" if nivel == "ROJO" else "🟡" if nivel == "AMARILLO" else "🟢"
            print(f"  {sin_id}: {score} pts → {icono} {nivel}")

    print(f"\n🎉 ¡Listo! {len(ids)} casos actualizados. Recarga el Dashboard.")


if __name__ == "__main__":
    main()
