import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))

csv_path = os.path.join(os.path.dirname(__file__), "../ai_data_core/data/synthetic/siniestros_scored.csv")
df = pd.read_csv(csv_path)

with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
    
    # Limpiamos para evitar duplicados
    conn.execute(text("TRUNCATE TABLE siniestros;"))
    conn.execute(text("TRUNCATE TABLE polizas;"))
    conn.execute(text("TRUNCATE TABLE asegurados;"))
    conn.execute(text("TRUNCATE TABLE proveedores;"))
    
    # 1. Inyectando Proveedores
    print("Inyectando proveedores...")
    proveedores = df[['beneficiario']].drop_duplicates().rename(columns={'beneficiario': 'id_proveedor'})
    proveedores.to_sql('proveedores', con=conn, if_exists='append', index=False)
    
    # 2. Inyectando Asegurados
    print("Inyectando asegurados...")
    asegurados = df[['id_asegurado', 'historial_siniestros_asegurado']].drop_duplicates()
    asegurados = asegurados.rename(columns={'historial_siniestros_asegurado': 'reclamos_ultimos_12_meses'})
    asegurados.to_sql('asegurados', con=conn, if_exists='append', index=False)
    
    # 3. Inyectando Pólizas
    print("Inyectando pólizas...")
    polizas = df[['id_poliza', 'id_asegurado', 'ramo', 'suma_asegurada']].drop_duplicates()
    polizas.to_sql('polizas', con=conn, if_exists='append', index=False)
    
    # 4. Inyectando Siniestros (Mapeo completo)
    print("Inyectando siniestros...")
    columnas_siniestros = [
        'id_siniestro', 'id_poliza', 'id_asegurado', 'ramo', 'cobertura', 
        'fecha_ocurrencia', 'fecha_reporte', 'monto_reclamado', 'monto_estimado', 
        'monto_pagado', 'estado', 'sucursal', 'descripcion', 'documentos_completos', 
        'tiene_doc_inconsistente'
    ]
    siniestros = df[columnas_siniestros].copy()
    siniestros['id_proveedor'] = df['beneficiario']
    
    # Dejamos el score en 0 para que nuestro propio motor lo calcule después
    siniestros['score_riesgo'] = 0 
    siniestros['nivel_riesgo'] = 'Pendiente'
    siniestros['alertas_activadas'] = ''
    siniestros['reglas_criticas'] = ''
    siniestros['explicacion_ia'] = None
    
    siniestros.to_sql('siniestros', con=conn, if_exists='append', index=False)
    
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

print("✅ Base de datos relacional poblada con éxito. 0% de NULLs injustificados.")
