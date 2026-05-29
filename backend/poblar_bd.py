"""
poblar_bd.py
Carga el CSV sintético a MySQL y genera datos sintéticos
para tablas complementarias (vehiculos, documentos, usuarios).
Ejecutar: docker-compose exec api python poblar_bd.py
"""
import os
import ast
import random
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
random.seed(42)

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("Falta DB_URL en .env")

engine  = create_engine(DB_URL, pool_pre_ping=True)
CSV_PATH = "/app/data/synthetic/siniestros_scored.csv"

MARCAS  = ["Toyota", "Chevrolet", "Hyundai", "Kia", "Mazda", "Nissan", "Ford"]
MODELOS = {"Toyota": "Corolla", "Chevrolet": "Sail", "Hyundai": "Tucson",
           "Kia": "Sportage", "Mazda": "CX-5", "Nissan": "Sentra", "Ford": "Escape"}

def gen_placa():
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{''.join(random.choices(letras, k=3))}-{''.join(random.choices('0123456789', k=4))}"

def gen_chasis():
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "".join(random.choices(chars, k=17))

DOCS_POR_RAMO = {
    "Vehiculos": ["Denuncia Policial", "Informe Perito", "Fotos Daño", "Parte Policial"],
    "Salud":     ["Cédula Asegurado", "Informe Perito", "Fotos Daño"],
    "Hogar":     ["Denuncia Policial", "Fotos Daño", "Informe Perito"],
    "Vida":      ["Cédula Asegurado", "Informe Perito"],
    "Generales": ["Denuncia Policial", "Fotos Daño", "Informe Perito"],
}

USUARIOS_DEMO = [
    {"nombre": "Admin FraudIA",   "email": "admin@fraudia.com",      "password": "admin123",      "rol": "admin"},
    {"nombre": "Analista Demo",   "email": "analista@fraudia.com",   "password": "analista123",   "rol": "analista"},
    {"nombre": "Supervisor Demo", "email": "supervisor@fraudia.com", "password": "supervisor123", "rol": "supervisor"},
]

def poblar():
    df = pd.read_csv(CSV_PATH)
    print(f"📄 CSV cargado: {len(df)} filas")

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        for tabla in ["log_consultas_agente", "alertas", "scores_riesgo",
                      "documentos", "vehiculos", "siniestros",
                      "polizas", "asegurados", "proveedores", "usuarios"]:
            conn.execute(text(f"TRUNCATE TABLE {tabla};"))
        print("🗑️  Tablas limpiadas")

        # ── 1. Proveedores ────────────────────────────────────────────────────
        proveedores = (
            df[["beneficiario"]].drop_duplicates()
            .rename(columns={"beneficiario": "id_proveedor"})
        )
        proveedores["tipo"]                     = "Taller"
        proveedores["ciudad"]                   = "Quito"
        proveedores["reclamos_asociados"]       = 0
        proveedores["monto_promedio_reclamado"] = 0.0
        proveedores["pct_casos_observados"]     = 0.0
        proveedores["antiguedad_anios"]         = [random.randint(1, 15) for _ in range(len(proveedores))]
        proveedores["en_lista_restrictiva"]     = 0
        proveedores.to_sql("proveedores", con=conn, if_exists="append", index=False)
        print(f"  ✅ Proveedores: {len(proveedores)}")

        # ── 2. Asegurados ─────────────────────────────────────────────────────
        asegurados = (
            df[["id_asegurado", "historial_siniestros_asegurado"]]
            .drop_duplicates(subset=["id_asegurado"])
            .rename(columns={"historial_siniestros_asegurado": "reclamos_12m"})
        )
        asegurados["segmento"]         = "Personal"
        asegurados["antiguedad_meses"] = 12
        asegurados["ciudad"]           = "Quito"
        asegurados["num_polizas"]      = 1
        asegurados["mora_actual"]      = 0
        asegurados["score_cliente"]    = 80
        asegurados.to_sql("asegurados", con=conn, if_exists="append", index=False)
        print(f"  ✅ Asegurados: {len(asegurados)}")

        # ── 3. Pólizas ────────────────────────────────────────────────────────
        polizas = (
            df[["id_poliza", "id_asegurado", "ramo", "suma_asegurada"]]
            .drop_duplicates(subset=["id_poliza"])
            .copy()
        )
        polizas["ramo"]          = polizas["ramo"].str.replace("Vehículos", "Vehiculos")
        polizas["fecha_inicio"]  = "2022-01-01"
        polizas["fecha_fin"]     = "2026-12-31"
        polizas["prima"]         = 500.0
        polizas["deducible"]     = 0.0
        polizas["canal_venta"]   = "Agente"
        polizas["ciudad"]        = "Quito"
        polizas["estado_poliza"] = "Vigente"
        polizas.to_sql("polizas", con=conn, if_exists="append", index=False)
        print(f"  ✅ Pólizas: {len(polizas)}")

        # ── 4. Vehículos ──────────────────────────────────────────────────────
        polizas_vehiculos = polizas[polizas["ramo"] == "Vehiculos"]["id_poliza"].tolist()
        vehiculos_rows = []
        for pid in polizas_vehiculos:
            marca = random.choice(MARCAS)
            vehiculos_rows.append({
                "id_poliza": pid,
                "placa":     gen_placa(),
                "chasis":    gen_chasis(),
                "motor":     gen_chasis()[:8],
                "marca":     marca,
                "modelo":    MODELOS[marca],
                "anio":      random.randint(2010, 2024),
            })
        if vehiculos_rows:
            pd.DataFrame(vehiculos_rows).to_sql("vehiculos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Vehículos: {len(vehiculos_rows)}")

        # ── 5. Siniestros ─────────────────────────────────────────────────────
        cols_sin = [
            "id_siniestro", "id_poliza", "id_asegurado", "ramo", "cobertura",
            "fecha_ocurrencia", "fecha_reporte", "monto_reclamado",
            "monto_estimado", "monto_pagado", "estado", "sucursal",
            "descripcion", "documentos_completos", "dias_desde_inicio_poliza",
            "dias_desde_fin_poliza", "dias_entre_ocurrencia_reporte",
            "historial_siniestros_asegurado", "etiqueta_fraude_simulada",
            "tiene_doc_inconsistente",
        ]
        siniestros = df[cols_sin].copy()
        siniestros["ramo"] = siniestros["ramo"].str.replace("Vehículos", "Vehiculos")
        siniestros["id_proveedor_beneficiario"] = df["beneficiario"]
        siniestros["documentos_completos"]      = siniestros["documentos_completos"].map(
            {True: 1, False: 0, "True": 1, "False": 0}).fillna(1).astype(int)
        siniestros["tiene_doc_inconsistente"]   = siniestros["tiene_doc_inconsistente"].map(
            {True: 1, False: 0, "True": 1, "False": 0}).fillna(0).astype(int)
        siniestros.to_sql("siniestros", con=conn, if_exists="append", index=False)
        print(f"  ✅ Siniestros: {len(siniestros)}")

        # ── 6. Documentos ─────────────────────────────────────────────────────
        doc_rows = []
        doc_id   = 1
        for _, row in df.iterrows():
            ramo_clean  = str(row["ramo"]).replace("Vehículos", "Vehiculos")
            tipos       = DOCS_POR_RAMO.get(ramo_clean, ["Fotos Daño", "Informe Perito"])
            es_fraude   = int(row["etiqueta_fraude_simulada"]) == 1
            tiene_incon = str(row["tiene_doc_inconsistente"]) in ["True", "1", "true"]
            for tipo in tipos:
                doc_rows.append({
                    "id_documento":            f"DOC-{doc_id:06d}",
                    "id_siniestro":            row["id_siniestro"],
                    "tipo_documento":          tipo,
                    "entregado":               1 if not (es_fraude and random.random() < 0.4) else 0,
                    "legible":                 1 if not (es_fraude and random.random() < 0.3) else 0,
                    "fecha_emision":           row["fecha_ocurrencia"],
                    "inconsistencia_detectada": 1 if (tiene_incon and random.random() < 0.5) else 0,
                    "observacion":             "",
                })
                doc_id += 1
        df_docs = pd.DataFrame(doc_rows)
        df_docs.to_sql("documentos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Documentos: {len(df_docs)}")

        # ── 7. Scores de riesgo ───────────────────────────────────────────────
        scores = df[["id_siniestro", "score_riesgo", "nivel_riesgo",
                     "alertas_activadas", "reglas_criticas",
                     "tiene_doc_inconsistente"]].copy()
        scores = scores.rename(columns={"score_riesgo": "score_normalizado"})
        scores["score_raw"]               = scores["score_normalizado"]
        scores["similitud_max_narrativa"] = 0.0
        scores["id_siniestro_similar"]    = None
        scores["version_modelo"]          = "v1.0"
        scores["tiene_doc_inconsistente"] = scores["tiene_doc_inconsistente"].map(
            {True: 1, False: 0, "True": 1, "False": 0}).fillna(0).astype(int)

        def safe_json(val):
            try:
                import json
                return json.dumps(ast.literal_eval(str(val)))
            except Exception:
                return "[]"

        scores["reglas_criticas"] = scores["reglas_criticas"].apply(safe_json)
        scores.to_sql("scores_riesgo", con=conn, if_exists="append", index=False)
        print(f"  ✅ Scores: {len(scores)}")

        # ── 8. Usuarios de prueba ─────────────────────────────────────────────
        for u in USUARIOS_DEMO:
            conn.execute(text("""
                INSERT IGNORE INTO usuarios (nombre, email, password_plain, rol)
                VALUES (:nombre, :email, :password, :rol)
            """), {"nombre": u["nombre"], "email": u["email"],
                   "password": u["password"], "rol": u["rol"]})
        print(f"  ✅ Usuarios: {len(USUARIOS_DEMO)}")

        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

    print("\n✅ Base de datos poblada correctamente.")
    print("\n📊 Resumen:")
    print(f"   Proveedores : {len(proveedores)}")
    print(f"   Asegurados  : {len(asegurados)}")
    print(f"   Pólizas     : {len(polizas)}")
    print(f"   Vehículos   : {len(vehiculos_rows)}")
    print(f"   Siniestros  : {len(siniestros)}")
    print(f"   Documentos  : {len(df_docs)}")
    print(f"   Scores      : {len(scores)}")
    print(f"   Usuarios    : {len(USUARIOS_DEMO)}")
    print("\n👤 Usuarios para la demo:")
    print("─" * 40)
    for u in USUARIOS_DEMO:
        print(f"  {u['rol']:12} | {u['email']:30} | {u['password']}")

if __name__ == "__main__":
    poblar()
