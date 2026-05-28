"""
poblar_bd.py
Carga el CSV sintético a MySQL.
Ejecutar DENTRO del contenedor: docker-compose exec api python poblar_bd.py
"""
import os
import ast
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("⚠️  Falta DB_URL en .env")

engine = create_engine(DB_URL, pool_pre_ping=True)

CSV_PATH = "/app/ai_data_core/data/synthetic/siniestros_scored.csv"

def poblar():
    df = pd.read_csv(CSV_PATH)
    print(f"📄 CSV cargado: {len(df)} filas | columnas: {list(df.columns)}")

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        # ── Limpiar tablas en orden correcto ──────────────────────────────
        for tabla in ["scores_riesgo", "alertas", "documentos",
                      "siniestros", "vehiculos", "polizas",
                      "asegurados", "proveedores", "usuarios"]:
            conn.execute(text(f"TRUNCATE TABLE {tabla};"))
        print("🗑️  Tablas limpiadas")

        # ── 1. Proveedores ────────────────────────────────────────────────
        proveedores = (
            df[["beneficiario"]]
            .drop_duplicates()
            .rename(columns={"beneficiario": "id_proveedor"})
        )
        proveedores["tipo"]                     = "Taller"
        proveedores["ciudad"]                   = "Quito"
        proveedores["reclamos_asociados"]       = 0
        proveedores["monto_promedio_reclamado"] = 0.0
        proveedores["pct_casos_observados"]     = 0.0
        proveedores["antiguedad_anios"]         = 1
        proveedores["en_lista_restrictiva"]     = 0
        proveedores.to_sql("proveedores", con=conn, if_exists="append", index=False)
        print(f"  ✅ Proveedores: {len(proveedores)}")

        # ── 2. Asegurados ─────────────────────────────────────────────────
        asegurados = (
            df[["id_asegurado", "historial_siniestros_asegurado"]]
            .drop_duplicates(subset=["id_asegurado"])
            .rename(columns={"historial_siniestros_asegurado": "reclamos_12m"})
        )
        asegurados["segmento"]          = "Personal"
        asegurados["antiguedad_meses"]  = 12
        asegurados["ciudad"]            = "Quito"
        asegurados["num_polizas"]       = 1
        asegurados["mora_actual"]       = 0
        asegurados["score_cliente"]     = 80
        asegurados.to_sql("asegurados", con=conn, if_exists="append", index=False)
        print(f"  ✅ Asegurados: {len(asegurados)}")

        # ── 3. Pólizas ────────────────────────────────────────────────────
        polizas = (
            df[["id_poliza", "id_asegurado", "ramo", "suma_asegurada"]]
            .drop_duplicates(subset=["id_poliza"])
        )
        polizas["fecha_inicio"]  = "2022-01-01"
        polizas["fecha_fin"]     = "2026-12-31"
        polizas["prima"]         = 500.0
        polizas["deducible"]     = 0.0
        polizas["canal_venta"]   = "Agente"
        polizas["ciudad"]        = "Quito"
        polizas["estado_poliza"] = "Vigente"
        polizas.to_sql("polizas", con=conn, if_exists="append", index=False)
        print(f"  ✅ Pólizas: {len(polizas)}")

        # ── 4. Siniestros ─────────────────────────────────────────────────
        cols_sin = [
            "id_siniestro", "id_poliza", "id_asegurado", "ramo", "cobertura",
            "fecha_ocurrencia", "fecha_reporte",
            "monto_reclamado", "monto_estimado", "monto_pagado",
            "estado", "sucursal", "descripcion", "documentos_completos",
            "dias_desde_inicio_poliza", "dias_desde_fin_poliza",
            "dias_entre_ocurrencia_reporte", "historial_siniestros_asegurado",
            "etiqueta_fraude_simulada", "tiene_doc_inconsistente",
        ]
        siniestros = df[cols_sin].copy()
        siniestros["id_proveedor_beneficiario"] = df["beneficiario"]
        siniestros = siniestros.rename(columns={
            "historial_siniestros_asegurado": "historial_siniestros_asegurado",
        })
        siniestros.to_sql("siniestros", con=conn, if_exists="append", index=False)
        print(f"  ✅ Siniestros: {len(siniestros)}")

        # ── 5. Scores de riesgo ───────────────────────────────────────────
        scores = df[["id_siniestro", "score_riesgo", "nivel_riesgo",
                     "alertas_activadas", "reglas_criticas",
                     "tiene_doc_inconsistente"]].copy()
        scores = scores.rename(columns={"score_riesgo": "score_normalizado"})
        scores["score_raw"]               = scores["score_normalizado"]
        scores["similitud_max_narrativa"] = 0.0
        scores["id_siniestro_similar"]    = None
        scores["version_modelo"]          = "v1.0"

        # Parsear reglas_criticas (viene como string de lista)
        def safe_json(val):
            try:
                parsed = ast.literal_eval(str(val))
                import json
                return json.dumps(parsed)
            except Exception:
                return "[]"

        scores["reglas_criticas"] = scores["reglas_criticas"].apply(safe_json)
        scores.to_sql("scores_riesgo", con=conn, if_exists="append", index=False)
        print(f"  ✅ Scores: {len(scores)}")

        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

    print("\n✅ Base de datos poblada correctamente.")

if __name__ == "__main__":
    poblar()
