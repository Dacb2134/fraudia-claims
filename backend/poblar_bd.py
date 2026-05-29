"""
poblar_bd.py  —  v2 (dataset Excel por hojas)
Carga el xlsx sintético v2 a MySQL.
Ejecutar: docker-compose exec api python poblar_bd.py
"""
import os
import random
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
random.seed(42)

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("Falta DB_URL en .env")

engine   = create_engine(DB_URL, pool_pre_ping=True)
XLSX_PATH = "/app/ai_data_core/data/synthetic/Evento_Datasets_Sinteticos_Fraude_500_v2.xlsx"

USUARIOS_DEMO = [
    {"nombre": "Admin FraudIA",   "email": "admin@fraudia.com",      "password": "admin123",      "rol": "admin"},
    {"nombre": "Analista Demo",   "email": "analista@fraudia.com",   "password": "analista123",   "rol": "analista"},
    {"nombre": "Supervisor Demo", "email": "supervisor@fraudia.com", "password": "supervisor123", "rol": "supervisor"},
]

# ── helpers ────────────────────────────────────────────────────────────────────
def _bool_col(series):
    """Convierte 'Sí'/'No', True/False, 1/0 → int 1/0."""
    return series.map(
        lambda v: 1 if str(v).strip().lower() in ("sí", "si", "yes", "true", "1") else 0
    ).fillna(0).astype(int)

def gen_chasis():
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "".join(random.choices(chars, k=17))

# ── carga de hojas ─────────────────────────────────────────────────────────────
xl = pd.ExcelFile(XLSX_PATH)
df_sin  = pd.read_excel(xl, "1_Siniestros")
df_pol  = pd.read_excel(xl, "2_Polizas")
df_aseg = pd.read_excel(xl, "3_Asegurados")
df_prov = pd.read_excel(xl, "4_Proveedores")
df_docs = pd.read_excel(xl, "5_Documentos")

print(f"📄 Hojas cargadas → Siniestros:{len(df_sin)} | Pólizas:{len(df_pol)} "
      f"| Asegurados:{len(df_aseg)} | Proveedores:{len(df_prov)} | Docs:{len(df_docs)}")

# ── normalización de columnas ──────────────────────────────────────────────────
# Siniestros
df_sin = df_sin.rename(columns={
    "ID Siniestro":                    "id_siniestro",
    "ID Póliza":                       "id_poliza",
    "ID Asegurado":                    "id_asegurado",
    "Ramo":                            "ramo",
    "Placa Vehículo Asegurado":        "placa_vehiculo",
    "Cobertura":                       "cobertura",
    "Fecha Ocurrencia":                "fecha_ocurrencia",
    "Fecha Reporte":                   "fecha_reporte",
    "Días Ocurr→Reporte":              "dias_entre_ocurrencia_reporte",
    "Monto Reclamado ($)":             "monto_reclamado",
    "Monto Estimado ($)":              "monto_estimado",
    "Monto Pagado ($)":                "monto_pagado",
    "Estado":                          "estado",
    "Sucursal":                        "sucursal",
    "ID Proveedor":                    "id_proveedor_beneficiario",
    "Descripción del Evento":          "descripcion",
    "Docs Completos":                  "documentos_completos",
    "Prov. Lista Restrictiva":         "prov_lista_restrictiva",
    "Días desde Inicio Póliza":        "dias_desde_inicio_poliza",
    "Días hasta Fin Póliza":           "dias_desde_fin_poliza",
    "N° Reclamos Previos Asegurado":   "historial_siniestros_asegurado",
    "Suma Asegurada ($)":              "suma_asegurada",
    "Similitud Narrativa Máx.":        "similitud_max_narrativa",
    "Número Parte Policial":           "numero_parte_policial",
})
df_sin["ramo"]                  = df_sin["ramo"].str.replace("Vehículos", "Vehiculos")
df_sin["documentos_completos"]  = _bool_col(df_sin["documentos_completos"])
# Fraude simulado: monto reclamado > estimado  O  proveedor en lista restrictiva
df_sin["etiqueta_fraude_simulada"] = (
    (df_sin["monto_reclamado"] > df_sin["monto_estimado"]) |
    (_bool_col(df_sin["prov_lista_restrictiva"]) == 1)
).astype(int)
# Doc inconsistente: docs incompletos
df_sin["tiene_doc_inconsistente"] = (df_sin["documentos_completos"] == 0).astype(int)

# Pólizas
df_pol = df_pol.rename(columns={
    "ID Póliza":           "id_poliza",
    "ID Asegurado":        "id_asegurado",
    "Ramo":                "ramo",
    "Fecha Inicio":        "fecha_inicio",
    "Fecha Fin":           "fecha_fin",
    "Suma Asegurada ($)":  "suma_asegurada",
    "Prima Anual ($)":     "prima",
    "Canal Venta":         "canal_venta",
    "Estado Póliza":       "estado_poliza",
})
df_pol["ramo"]  = df_pol["ramo"].str.replace("Vehículos", "Vehiculos")
df_pol["deducible"] = 0.0
df_pol["ciudad"]    = "Quito"

# Asegurados
df_aseg = df_aseg.rename(columns={
    "ID Asegurado":                    "id_asegurado",
    "Nombres Asegurado":               "nombre",
    "Segmento":                        "segmento",
    "Ciudad":                          "ciudad",
    "Antigüedad (años)":               "antiguedad_anios",
    "N° Pólizas Activas":              "num_polizas",
    "N° Reclamos Últimos 12 Meses":    "reclamos_12m",
    "N° Reclamos Histórico Total":     "reclamos_historico",
    "Reclamos RC sin Tercero":         "reclamos_rc",
    "Perfil Riesgo Histórico":         "perfil_riesgo",
})
df_aseg["antiguedad_meses"] = df_aseg["antiguedad_anios"] * 12
df_aseg["mora_actual"]      = 0
df_aseg["score_cliente"]    = df_aseg["perfil_riesgo"].map(
    {"Alto": 40, "Medio": 60, "Bajo": 80}
).fillna(70).astype(int)

# Proveedores
df_prov = df_prov.rename(columns={
    "ID Proveedor":            "id_proveedor",
    "Nombre Proveedor":        "nombre_proveedor",
    "Tipo":                    "tipo",
    "Ciudad":                  "ciudad",
    "N° Siniestros Asociados": "reclamos_asociados",
    "En Lista Restrictiva":    "en_lista_restrictiva",
    "Promedio Monto ($)":      "_monto_str",
    "Unnamed: 8":              "monto_promedio_reclamado",
})
df_prov["en_lista_restrictiva"]    = _bool_col(df_prov["en_lista_restrictiva"])
df_prov["monto_promedio_reclamado"] = pd.to_numeric(
    df_prov["monto_promedio_reclamado"], errors="coerce"
).fillna(0.0)
df_prov["pct_casos_observados"]    = 0.0
df_prov["antiguedad_anios"]        = [random.randint(1, 15) for _ in range(len(df_prov))]

# Documentos
df_docs = df_docs.rename(columns={
    "ID Documento":        "id_documento",
    "ID Siniestro":        "id_siniestro",
    "Tipo Documento":      "tipo_documento",
    "Nombre Archivo PDF":  "nombre_archivo",
})
df_docs["entregado"]                = 1
df_docs["legible"]                  = 1
df_docs["inconsistencia_detectada"] = 0
df_docs["observacion"]              = ""
# marcar inconsistencia para siniestros con docs incompletos
sin_incon = set(df_sin.loc[df_sin["tiene_doc_inconsistente"] == 1, "id_siniestro"])
df_docs.loc[df_docs["id_siniestro"].isin(sin_incon), "inconsistencia_detectada"] = 1
# fecha_emision: tomar de siniestros
fecha_map = df_sin.set_index("id_siniestro")["fecha_ocurrencia"].to_dict()
df_docs["fecha_emision"] = df_docs["id_siniestro"].map(fecha_map)

# ── scores de riesgo (reglas simples) ─────────────────────────────────────────
def calc_score(row):
    score = 0
    alertas = []
    if row["monto_reclamado"] > row["monto_estimado"] * 1.3:
        score += 30; alertas.append("R01: Monto reclamado excede estimado >30%")
    if row["dias_entre_ocurrencia_reporte"] > 30:
        score += 20; alertas.append("R02: Reporte tardío >30 días")
    if row["historial_siniestros_asegurado"] >= 3:
        score += 25; alertas.append("R03: Asegurado con 3+ reclamos previos")
    if row["documentos_completos"] == 0:
        score += 15; alertas.append("R04: Documentación incompleta")
    if row["prov_lista_restrictiva_int"] == 1:
        score += 40; alertas.append("R05: Proveedor en lista restrictiva")
    if row.get("similitud_max_narrativa", 0) >= 0.8:
        score += 20; alertas.append("R06: Alta similitud narrativa")
    score = min(score, 100)
    if score >= 70:   nivel = "ROJO"
    elif score >= 40: nivel = "AMARILLO"
    else:             nivel = "VERDE"
    return score, nivel, "; ".join(alertas)

df_sin["prov_lista_restrictiva_int"] = _bool_col(df_sin["prov_lista_restrictiva"])
df_sin["similitud_max_narrativa"] = df_sin["similitud_max_narrativa"].fillna(0.0)

scores_rows = []
for _, r in df_sin.iterrows():
    sc, nv, al = calc_score(r)
    scores_rows.append({
        "id_siniestro":             r["id_siniestro"],
        "score_raw":                sc,
        "score_normalizado":        sc,
        "nivel_riesgo":             nv,
        "alertas_activadas":        al,
        "reglas_criticas":          "[]",
        "tiene_doc_inconsistente":  int(r["tiene_doc_inconsistente"]),
        "similitud_max_narrativa":  float(r["similitud_max_narrativa"]),
        "id_siniestro_similar":     None,
        "version_modelo":           "v2.0",
    })
df_scores = pd.DataFrame(scores_rows)

# ── vehículos: una fila por póliza Vehiculos con la placa del siniestro ────────
placa_map = (
    df_sin[df_sin["ramo"] == "Vehiculos"][["id_poliza", "placa_vehiculo"]]
    .drop_duplicates("id_poliza")
    .dropna(subset=["placa_vehiculo"])
)
MARCAS  = ["Toyota","Chevrolet","Hyundai","Kia","Mazda","Nissan","Ford"]
MODELOS = {"Toyota":"Corolla","Chevrolet":"Sail","Hyundai":"Tucson",
           "Kia":"Sportage","Mazda":"CX-5","Nissan":"Sentra","Ford":"Escape"}

vehiculos_rows = []
for _, row in placa_map.iterrows():
    marca = random.choice(MARCAS)
    vehiculos_rows.append({
        "id_poliza": row["id_poliza"],
        "placa":     row["placa_vehiculo"],
        "chasis":    gen_chasis(),
        "motor":     gen_chasis()[:8],
        "marca":     marca,
        "modelo":    MODELOS[marca],
        "anio":      random.randint(2010, 2024),
    })
df_veh = pd.DataFrame(vehiculos_rows)

# ── poblar BD ──────────────────────────────────────────────────────────────────
def poblar():
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        for tabla in ["log_consultas_agente","alertas","scores_riesgo",
                      "documentos","vehiculos","siniestros",
                      "polizas","asegurados","proveedores","usuarios"]:
            conn.execute(text(f"TRUNCATE TABLE {tabla};"))
        print("🗑️  Tablas limpiadas")

        # 1. Proveedores
        df_prov[[
            "id_proveedor","tipo","ciudad","reclamos_asociados",
            "monto_promedio_reclamado","pct_casos_observados",
            "antiguedad_anios","en_lista_restrictiva",
        ]].to_sql("proveedores", con=conn, if_exists="append", index=False)
        print(f"  ✅ Proveedores: {len(df_prov)}")

        # 2. Asegurados
        df_aseg[[
            "id_asegurado","segmento","antiguedad_meses","ciudad",
            "num_polizas","reclamos_12m","mora_actual","score_cliente",
        ]].to_sql("asegurados", con=conn, if_exists="append", index=False)
        print(f"  ✅ Asegurados: {len(df_aseg)}")

        # 3. Pólizas
        df_pol[[
            "id_poliza","id_asegurado","ramo","fecha_inicio","fecha_fin",
            "prima","suma_asegurada","deducible","canal_venta","ciudad","estado_poliza",
        ]].to_sql("polizas", con=conn, if_exists="append", index=False)
        print(f"  ✅ Pólizas: {len(df_pol)}")

        # 4. Vehículos
        if not df_veh.empty:
            df_veh.to_sql("vehiculos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Vehículos: {len(df_veh)}")

        # 5. Siniestros
        df_sin[[
            "id_siniestro","id_poliza","id_asegurado","id_proveedor_beneficiario",
            "ramo","cobertura","fecha_ocurrencia","fecha_reporte",
            "monto_reclamado","monto_estimado","monto_pagado","estado","sucursal",
            "descripcion","documentos_completos","dias_desde_inicio_poliza",
            "dias_desde_fin_poliza","dias_entre_ocurrencia_reporte",
            "historial_siniestros_asegurado","etiqueta_fraude_simulada",
            "tiene_doc_inconsistente",
        ]].to_sql("siniestros", con=conn, if_exists="append", index=False)
        print(f"  ✅ Siniestros: {len(df_sin)}")

        # 6. Documentos
        df_docs[[
            "id_documento","id_siniestro","tipo_documento","entregado",
            "legible","fecha_emision","inconsistencia_detectada","observacion",
        ]].to_sql("documentos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Documentos: {len(df_docs)}")

        # 7. Scores de riesgo
        df_scores.to_sql("scores_riesgo", con=conn, if_exists="append", index=False)
        print(f"  ✅ Scores: {len(df_scores)}")

        # 8. Usuarios
        for u in USUARIOS_DEMO:
            conn.execute(text("""
                INSERT IGNORE INTO usuarios (nombre, email, password_plain, rol)
                VALUES (:nombre, :email, :password, :rol)
            """), {"nombre": u["nombre"], "email": u["email"],
                   "password": u["password"], "rol": u["rol"]})
        print(f"  ✅ Usuarios: {len(USUARIOS_DEMO)}")

        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

    print("\n✅ Base de datos poblada correctamente (dataset v2).")
    print(f"\n📊 Resumen:")
    print(f"   Proveedores : {len(df_prov)}")
    print(f"   Asegurados  : {len(df_aseg)}")
    print(f"   Pólizas     : {len(df_pol)}")
    print(f"   Vehículos   : {len(df_veh)}")
    print(f"   Siniestros  : {len(df_sin)}")
    print(f"   Documentos  : {len(df_docs)}")
    print(f"   Scores      : {len(df_scores)}")
    print(f"   Usuarios    : {len(USUARIOS_DEMO)}")
    print("\n👤 Usuarios para la demo:")
    print("─" * 40)
    for u in USUARIOS_DEMO:
        print(f"  {u['rol']:12} | {u['email']:30} | {u['password']}")

if __name__ == "__main__":
    poblar()