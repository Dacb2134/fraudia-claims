"""
poblar_bd.py — v2
Carga el dataset oficial del hackIAthon 2026 (500 siniestros) a MySQL.
Fuente: Evento_Datasets_Sinteticos_Fraude_500_v2.xlsx
Ejecutar: docker-compose exec api python poblar_bd.py
"""
import os
import json
import random
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
random.seed(42)

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("Falta DB_URL en .env")

engine     = create_engine(DB_URL, pool_pre_ping=True)
EXCEL_PATH = "/app/data/evento/Evento_Datasets_Sinteticos_Fraude_500_v2.xlsx"

MARCAS  = ["Toyota","Chevrolet","Hyundai","Kia","Mazda","Nissan","Ford","Volkswagen"]
MODELOS = {"Toyota":"Corolla","Chevrolet":"Sail","Hyundai":"Tucson","Kia":"Sportage",
           "Mazda":"CX-5","Nissan":"Sentra","Ford":"Escape","Volkswagen":"Golf"}

USUARIOS_DEMO = [
    {"nombre": "Admin FraudIA",   "email": "admin@fraudia.com",      "password": "admin123",      "rol": "admin"},
    {"nombre": "Analista Demo",   "email": "analista@fraudia.com",   "password": "analista123",   "rol": "analista"},
    {"nombre": "Supervisor Demo", "email": "supervisor@fraudia.com", "password": "supervisor123", "rol": "supervisor"},
]

def gen_chasis():
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "".join(random.choices(chars, k=17))

def calcular_score(row: dict, prov_restrictivos: set) -> tuple[int, str, str, str]:
    """
    Aplica las señales del hackIAthon al dataset oficial.
    Retorna (score, alertas_str, reglas_json, nivel_riesgo)
    """
    score   = 0
    alertas = []
    reglas  = []

    cobertura   = str(row.get("Cobertura", "")).lower()
    dias_rep    = int(row.get("Días Ocurr→Reporte", 0) or 0)
    dias_ini    = int(row.get("Días desde Inicio Póliza", 999) or 999)
    historial   = int(row.get("N° Reclamos Previos Asegurado", 0) or 0)
    reclamos12m = int(row.get("reclamos_12m", 0) or 0)
    docs_ok     = str(row.get("Docs Completos", "Sí")) == "Sí"
    lista_res   = str(row.get("Prov. Lista Restrictiva", "No")) == "Sí"
    similitud   = float(row.get("Similitud Narrativa Máx.", 0) or 0)
    monto       = float(row.get("Monto Reclamado ($)", 0) or 0)
    suma_aseg   = float(row.get("Suma Asegurada ($)", 1) or 1)
    id_prov     = str(row.get("ID Proveedor", ""))
    perfil      = str(row.get("Perfil Riesgo Histórico", "Bajo"))
    estado      = str(row.get("Estado", ""))

    # S-01: Borde inicio póliza
    if dias_ini <= 10:
        score += 8
        alertas.append(f"Siniestro a {dias_ini} días del inicio de póliza (≤10 días → 8 pts)")
        reglas.append({"codigo": "RF-05", "regla": "Siniestro extremo al inicio de vigencia", "clasificacion": "AMARILLO"})
    elif dias_ini <= 30:
        score += 4
        alertas.append(f"Siniestro a {dias_ini} días del inicio de póliza (11-30 días → 4 pts)")

    # S-02: Demora denuncia robo
    if "robo" in cobertura:
        if dias_rep > 4:
            score += 8
            alertas.append(f"Demora de {dias_rep} días en denunciar robo (>48 h → 8 pts)")
            reglas.append({"codigo": "RF-06", "regla": f"Demora de {dias_rep} días en denuncia de robo", "clasificacion": "AMARILLO"})
        elif dias_rep >= 2:
            score += 4
            alertas.append(f"Demora de {dias_rep} días en denunciar robo (24-48 h → 4 pts)")

    # S-03: Alta frecuencia asegurado (reclamos últimos 12 meses)
    if reclamos12m >= 3:
        score += 8
        alertas.append(f"Asegurado con {reclamos12m} reclamos en 12 meses (≥3 → 8 pts)")
    elif reclamos12m == 2:
        score += 4
        alertas.append(f"Asegurado con {reclamos12m} reclamos en 12 meses (2 → 4 pts)")
    elif historial >= 3:
        score += 6
        alertas.append(f"Historial de {historial} siniestros previos (≥3 → 6 pts)")

    # S-06: Proveedor lista restrictiva
    if lista_res or id_prov in prov_restrictivos:
        score += 10
        alertas.append(f"Proveedor {id_prov} en Lista Restrictiva (10 pts)")
        reglas.append({"codigo": "RF-03", "regla": "Proveedor en Lista Restrictiva", "clasificacion": "ROJO"})

    # S-07: Documentos incompletos
    if not docs_ok:
        score += 4
        alertas.append("Documentos incompletos o faltantes (4 pts)")

    # S-11: Reporte tardío
    if dias_rep > 7:
        score += 5
        alertas.append(f"Reporte tardío: {dias_rep} días (>7 → 5 pts)")
    elif dias_rep >= 4:
        score += 3
        alertas.append(f"Reporte tardío: {dias_rep} días (4-7 → 3 pts)")

    # S-12: Narrativas similares (RF-07)
    if similitud > 0.85:
        score += 8
        alertas.append(f"Narrativa con {similitud*100:.0f}% similitud (>85% → 8 pts)")
        reglas.append({"codigo": "RF-07", "regla": "Narrativa Idéntica (Clonada)", "clasificacion": "AMARILLO"})
    elif similitud > 0.70:
        score += 4
        alertas.append(f"Narrativa con {similitud*100:.0f}% similitud (70-85% → 4 pts)")

    # S-13: Monto cercano a suma asegurada
    if suma_aseg > 0 and (monto / suma_aseg) >= 0.95:
        score += 4
        alertas.append(f"Monto reclamado es {round(monto/suma_aseg*100)}% de suma asegurada (≥95% → 4 pts)")
    elif suma_aseg > 0 and (monto / suma_aseg) >= 0.80:
        score += 2
        alertas.append(f"Monto reclamado es {round(monto/suma_aseg*100)}% de suma asegurada (≥80% → 2 pts)")

    # Perfil de riesgo histórico alto
    if perfil == "Alto":
        score += 5
        alertas.append("Perfil de riesgo histórico ALTO del asegurado (5 pts)")

    # Estado en Investigación — señal directa
    if estado == "Investigación":
        score += 8
        alertas.append("Siniestro en estado Investigación (8 pts)")

    score = min(score, 100)
    nivel = "ROJO" if score >= 76 else "AMARILLO" if score >= 41 else "VERDE"

    return score, " | ".join(alertas), json.dumps(reglas), nivel


def poblar():
    print("📂 Leyendo dataset oficial del hackIAthon...")
    xl = pd.ExcelFile(EXCEL_PATH)

    df_sin  = pd.read_excel(xl, sheet_name="1_Siniestros")
    df_pol  = pd.read_excel(xl, sheet_name="2_Polizas")
    df_ase  = pd.read_excel(xl, sheet_name="3_Asegurados")
    df_prov = pd.read_excel(xl, sheet_name="4_Proveedores")
    df_docs = pd.read_excel(xl, sheet_name="5_Documentos")

    print(f"   Siniestros: {len(df_sin)} | Pólizas: {len(df_pol)} | Asegurados: {len(df_ase)}")

    # Enriquecer siniestros con datos de asegurados
    df_sin = df_sin.merge(
        df_ase[["ID Asegurado","Perfil Riesgo Histórico","N° Reclamos Últimos 12 Meses"]],
        on="ID Asegurado", how="left"
    )
    df_sin.rename(columns={"N° Reclamos Últimos 12 Meses": "reclamos_12m"}, inplace=True)

    prov_restrictivos = set(df_prov[df_prov["En Lista Restrictiva"]=="Sí"]["ID Proveedor"].tolist())

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        for tabla in ["log_consultas_agente","alertas","scores_riesgo","documentos",
                      "vehiculos","siniestros","polizas","asegurados","proveedores","usuarios"]:
            conn.execute(text(f"TRUNCATE TABLE {tabla};"))
        print("🗑️  Tablas limpiadas")

        # 1. Proveedores
        prov_rows = []
        for _, p in df_prov.iterrows():
            try: promedio = float(str(p.get("Promedio Monto ($)","0")).replace("—","0").replace(",",""))
            except: promedio = 0.0
            prov_rows.append({
                "id_proveedor":             str(p["ID Proveedor"]),
                "tipo":                     str(p.get("Tipo","Taller"))[:30],
                "ciudad":                   str(p.get("Ciudad","Quito"))[:80],
                "reclamos_asociados":       int(p.get("N° Siniestros Asociados",0) or 0),
                "monto_promedio_reclamado": promedio,
                "pct_casos_observados":     0.0,
                "antiguedad_anios":         random.randint(1,15),
                "en_lista_restrictiva":     1 if str(p.get("En Lista Restrictiva","No"))=="Sí" else 0,
            })
        pd.DataFrame(prov_rows).to_sql("proveedores", con=conn, if_exists="append", index=False)
        print(f"  ✅ Proveedores: {len(prov_rows)}")

        # 2. Asegurados
        ase_rows = []
        for _, a in df_ase.iterrows():
            seg = "Personal"
            if str(a.get("Segmento","Natural")) not in ["Natural","Personal"]: seg = "Empresarial"
            ase_rows.append({
                "id_asegurado":       str(a["ID Asegurado"]),
                "segmento":           seg,
                "antiguedad_meses":   int(float(a.get("Antigüedad (años)",1) or 1)*12),
                "ciudad":             str(a.get("Ciudad","Quito"))[:80],
                "num_polizas":        int(a.get("N° Pólizas Activas",1) or 1),
                "reclamos_12m":       int(a.get("N° Reclamos Últimos 12 Meses",0) or 0),
                "mora_actual":        0,
                "score_cliente":      80 if str(a.get("Perfil Riesgo Histórico","Bajo"))=="Bajo" else
                                      60 if str(a.get("Perfil Riesgo Histórico",""))=="Medio" else 40,
            })
        pd.DataFrame(ase_rows).to_sql("asegurados", con=conn, if_exists="append", index=False)
        print(f"  ✅ Asegurados: {len(ase_rows)}")

        # 3. Pólizas
        pol_rows = []
        for _, p in df_pol.iterrows():
            ramo = str(p.get("Ramo","Generales")).replace("Vehículos","Vehiculos")
            estado_pol = "Vigente" if str(p.get("Estado Póliza","Vigente"))=="Vigente" else "Vencida"
            pol_rows.append({
                "id_poliza":      str(p["ID Póliza"]),
                "id_asegurado":   str(p["ID Asegurado"]),
                "ramo":           ramo[:20],
                "fecha_inicio":   pd.to_datetime(p["Fecha Inicio"]).strftime("%Y-%m-%d"),
                "fecha_fin":      pd.to_datetime(p["Fecha Fin"]).strftime("%Y-%m-%d"),
                "prima":          float(p.get("Prima Anual ($)",500) or 500),
                "suma_asegurada": float(p.get("Suma Asegurada ($)",0) or 0),
                "deducible":      0.0,
                "canal_venta":    str(p.get("Canal Venta","Agente"))[:20],
                "ciudad":         "Quito",
                "estado_poliza":  estado_pol,
            })
        pd.DataFrame(pol_rows).to_sql("polizas", con=conn, if_exists="append", index=False)
        print(f"  ✅ Pólizas: {len(pol_rows)}")

        # 4. Vehículos
        df_veh = df_sin[df_sin["Ramo"]=="Vehículos"].drop_duplicates(subset=["ID Póliza"])
        veh_rows = []
        placas_usadas = set()
        for _, v in df_veh.iterrows():
            placa = str(v.get("Placa Vehículo Asegurado","")).strip()
            if not placa or placa=="nan" or placa in placas_usadas:
                letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                placa  = f"{''.join(random.choices(letras,k=3))}-{''.join(random.choices('0123456789',k=4))}"
            placas_usadas.add(placa)
            marca = random.choice(MARCAS)
            veh_rows.append({
                "id_poliza": str(v["ID Póliza"]),
                "placa":     placa[:10],
                "chasis":    gen_chasis(),
                "motor":     gen_chasis()[:8],
                "marca":     marca,
                "modelo":    MODELOS[marca],
                "anio":      random.randint(2012,2024),
            })
        if veh_rows:
            pd.DataFrame(veh_rows).to_sql("vehiculos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Vehículos: {len(veh_rows)}")

        # 5. Siniestros + Scores
        sin_rows   = []
        score_rows = []
        ids_sin_ok = set()

        for _, s in df_sin.iterrows():
            id_sin  = str(s["ID Siniestro"])
            id_pol  = str(s["ID Póliza"])
            id_ase  = str(s["ID Asegurado"])
            ramo    = str(s.get("Ramo","Generales")).replace("Vehículos","Vehiculos")
            id_prov = str(s["ID Proveedor"]) if pd.notna(s.get("ID Proveedor")) else None
            docs_ok = 1 if str(s.get("Docs Completos","Sí"))=="Sí" else 0
            lista_r = 1 if str(s.get("Prov. Lista Restrictiva","No"))=="Sí" else 0
            sim_max = float(s.get("Similitud Narrativa Máx.",0) or 0)

            sc, alertas_str, reglas_json, nivel = calcular_score(s.to_dict(), prov_restrictivos)

            sin_rows.append({
                "id_siniestro":                   id_sin,
                "id_poliza":                      id_pol,
                "id_asegurado":                   id_ase,
                "id_proveedor_beneficiario":      id_prov,
                "ramo":                           ramo[:20],
                "cobertura":                      str(s.get("Cobertura","Daño"))[:60],
                "fecha_ocurrencia":               pd.to_datetime(s["Fecha Ocurrencia"]).strftime("%Y-%m-%d"),
                "fecha_reporte":                  pd.to_datetime(s["Fecha Reporte"]).strftime("%Y-%m-%d"),
                "monto_reclamado":                float(s.get("Monto Reclamado ($)",0) or 0),
                "monto_estimado":                 float(s.get("Monto Estimado ($)",0) or 0),
                "monto_pagado":                   float(s.get("Monto Pagado ($)",0) or 0),
                "estado":                         str(s.get("Estado","Reserva"))[:30],
                "sucursal":                       str(s.get("Sucursal","Quito"))[:60],
                "descripcion":                    str(s.get("Descripción del Evento",""))[:500],
                "documentos_completos":           docs_ok,
                "dias_desde_inicio_poliza":       int(s.get("Días desde Inicio Póliza",0) or 0),
                "dias_desde_fin_poliza":          0,
                "dias_entre_ocurrencia_reporte":  int(s.get("Días Ocurr→Reporte",0) or 0),
                "historial_siniestros_asegurado": int(s.get("N° Reclamos Previos Asegurado",0) or 0),
                "etiqueta_fraude_simulada":        1 if nivel in ("ROJO","AMARILLO") else 0,
                "tiene_doc_inconsistente":         lista_r,
            })

            score_rows.append({
                "id_siniestro":            id_sin,
                "score_raw":               sc,
                "score_normalizado":       sc,
                "nivel_riesgo":            nivel,
                "alertas_activadas":       alertas_str,
                "reglas_criticas":         reglas_json,
                "tiene_doc_inconsistente": lista_r,
                "similitud_max_narrativa": sim_max,
                "id_siniestro_similar":    None,
                "version_modelo":          "v2.0",
            })
            ids_sin_ok.add(id_sin)

        pd.DataFrame(sin_rows).to_sql("siniestros", con=conn, if_exists="append", index=False)
        pd.DataFrame(score_rows).to_sql("scores_riesgo", con=conn, if_exists="append", index=False)
        print(f"  ✅ Siniestros: {len(sin_rows)}")
        print(f"  ✅ Scores    : {len(score_rows)}")

        # 6. Documentos
        doc_rows = []
        doc_id = 1
        for _, d in df_docs.iterrows():
            if pd.isna(d.get("ID Siniestro")): continue
            id_sin_doc = str(d["ID Siniestro"])
            if id_sin_doc not in ids_sin_ok: continue
            doc_rows.append({
                "id_documento":             f"DOC-{doc_id:06d}",
                "id_siniestro":             id_sin_doc,
                "tipo_documento":           str(d.get("Tipo Documento","Fotografías"))[:40],
                "entregado":                1,
                "legible":                  1,
                "fecha_emision":            None,
                "inconsistencia_detectada": 0,
                "observacion":              "",
            })
            doc_id += 1
        if doc_rows:
            pd.DataFrame(doc_rows).to_sql("documentos", con=conn, if_exists="append", index=False)
        print(f"  ✅ Documentos: {len(doc_rows)}")

        # 7. Usuarios
        for u in USUARIOS_DEMO:
            conn.execute(text("""
                INSERT IGNORE INTO usuarios (nombre, email, password_plain, rol)
                VALUES (:nombre, :email, :password, :rol)
            """), {"nombre": u["nombre"], "email": u["email"],
                   "password": u["password"], "rol": u["rol"]})
        print(f"  ✅ Usuarios: {len(USUARIOS_DEMO)}")

        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

    rojos     = sum(1 for s in score_rows if s["nivel_riesgo"]=="ROJO")
    amarillos = sum(1 for s in score_rows if s["nivel_riesgo"]=="AMARILLO")
    verdes    = sum(1 for s in score_rows if s["nivel_riesgo"]=="VERDE")

    print("\n✅ Base de datos poblada con dataset oficial del hackIAthon.")
    print(f"\n📊 Distribución de riesgo:")
    print(f"   🔴 ROJO     : {rojos}  ({rojos/len(score_rows)*100:.1f}%)")
    print(f"   🟡 AMARILLO : {amarillos}  ({amarillos/len(score_rows)*100:.1f}%)")
    print(f"   🟢 VERDE    : {verdes}  ({verdes/len(score_rows)*100:.1f}%)")
    print(f"\n👤 Usuarios demo:")
    for u in USUARIOS_DEMO:
        print(f"   {u['rol']:12} | {u['email']:30} | {u['password']}")


if __name__ == "__main__":
    poblar()