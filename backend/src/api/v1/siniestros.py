"""
GET  /api/v1/siniestros                            — lista priorizada con filtros
GET  /api/v1/siniestros/{id}                       — detalle de un siniestro
POST /api/v1/siniestros/{id}/recalcular            — recalcula score en tiempo real
POST /api/v1/siniestros/evaluar                    — evalúa un caso nuevo sin guardar en BD
POST /api/v1/siniestros/ingestar                   — carga CSV de casos nuevos a la BD
GET  /api/v1/siniestros/{id}/documentos            — lista documentos del expediente
POST /api/v1/siniestros/{id}/documentos/subir      — sube PDF y lo guarda en BD
POST /api/v1/siniestros/{id}/documentos/analizar   — analiza un documento con Gemini
"""
import base64
import csv
import io
import os
import re
import uuid
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from src.core.database import get_db
from src.engine.risk_scorer import calcular_score_hibrido

# ── Ruta a los PDFs del dataset (Docker: /app/ai_data_core, Railway: igual) ──
def _pdf_base() -> Path:
    candidates = [
        Path("/app/ai_data_core/data/synthetic/pdfs"),
        Path(__file__).resolve().parents[4] / "ai_data_core" / "data" / "synthetic" / "pdfs",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

PDF_BASE = _pdf_base()

TIPO_INFO = {
    "factura":               {"carpeta": "FACTURAS",                "icono": "receipt_long",  "label": "Factura"},
    "declaracion_accidente": {"carpeta": "DECLARACIÓN DE ACCIDENTE", "icono": "description",  "label": "Declaración de Accidente"},
    "parte_policial":        {"carpeta": "PARTE POLICIAL",           "icono": "local_police", "label": "Parte Policial"},
}

def _docs_dataset(id_siniestro: str) -> list[dict]:
    numero = re.sub(r"^SIN-0*", "", id_siniestro)
    patron = re.compile(rf"SIN-0*{numero}\b", re.IGNORECASE)
    encontrados = []
    for tipo, info in TIPO_INFO.items():
        carpeta = PDF_BASE / info["carpeta"]
        if carpeta.exists():
            for f in sorted(carpeta.iterdir()):
                if f.is_file() and f.suffix.lower() == ".pdf" and patron.search(f.name):
                    encontrados.append({
                        "id": f"dataset_{tipo}", "tipo": tipo,
                        "label": info["label"], "nombre": f.name,
                        "origen": "dataset", "icono": info["icono"],
                    })
    return encontrados

def _init_tabla(db: Session):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS archivos_siniestro (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            id_siniestro   VARCHAR(50)  NOT NULL,
            tipo_documento VARCHAR(50)  NOT NULL,
            nombre_archivo VARCHAR(255),
            contenido_pdf  LONGBLOB     NOT NULL,
            analisis_ia    TEXT,
            origen         VARCHAR(20)  DEFAULT 'upload',
            subido_en      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sin (id_siniestro)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))
    db.commit()

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


# ── Modelo para evaluación de caso nuevo ─────────────────────────────────────

class EvaluarRequest(BaseModel):
    ramo:                          str   = "Vehículos"
    cobertura:                     str   = "Daño"
    estado:                        str   = "Reserva"
    monto_reclamado:               float = 5000.0
    monto_estimado:                float = 4000.0
    suma_asegurada:                float = 20000.0
    dias_desde_inicio_poliza:      int   = 180
    dias_desde_fin_poliza:         int   = 180
    dias_entre_ocurrencia_reporte: int   = 2
    historial_siniestros_asegurado: int  = 0
    documentos_completos:          bool  = True
    tiene_doc_inconsistente:       int   = 0
    descripcion:                   str   = ""
    sucursal:                      str   = "Quito"
    proveedor_en_lista_restrictiva: bool = False
    pct_casos_proveedor:           float = 0.0


@router.post("/evaluar")
def evaluar_caso(body: EvaluarRequest):
    """
    Evalúa un caso nuevo sin guardarlo en BD.
    Devuelve score, nivel de riesgo y alertas explicables.
    Ideal para la prueba en vivo del jurado.
    """
    siniestro_data = {
        "ramo":                          body.ramo,
        "cobertura":                     body.cobertura,
        "estado":                        body.estado,
        "monto_reclamado":               body.monto_reclamado,
        "monto_estimado":                body.monto_estimado,
        "suma_asegurada":                body.suma_asegurada,
        "dias_desde_inicio_poliza":      body.dias_desde_inicio_poliza,
        "dias_desde_fin_poliza":         body.dias_desde_fin_poliza,
        "dias_entre_ocurrencia_reporte": body.dias_entre_ocurrencia_reporte,
        "historial_siniestros_asegurado": body.historial_siniestros_asegurado,
        "documentos_completos":          body.documentos_completos,
        "tiene_doc_inconsistente":       body.tiene_doc_inconsistente,
        "descripcion":                   body.descripcion,
        "similitud_narrativa":           0.0,
    }
    proveedor_data = {
        "en_lista_restrictiva": body.proveedor_en_lista_restrictiva,
        "pct_casos_observados": body.pct_casos_proveedor,
    }

    resultado = calcular_score_hibrido(siniestro=siniestro_data, proveedor=proveedor_data)

    nivel_icono = {"ROJO": "🔴", "AMARILLO": "🟡", "VERDE": "🟢"}.get(resultado["nivel_riesgo"], "⚪")
    alertas = [a for a in resultado["alertas_activadas"].split(" | ") if a]

    return {
        "score":           resultado["score_normalizado"],
        "nivel":           resultado["nivel_riesgo"],
        "nivel_icono":     nivel_icono,
        "alertas":         alertas,
        "reglas_criticas": resultado["reglas_criticas"],
        "total_alertas":   resultado["total_alertas"],
        "modo":            resultado.get("modo", "reglas"),
        "guardado_en_bd":  False,
    }


@router.post("/ingestar")
async def ingestar_csv(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Carga un archivo CSV con siniestros nuevos, calcula su score y los guarda en BD.
    Columnas mínimas requeridas: ramo, cobertura, monto_reclamado, fecha_ocurrencia,
    dias_desde_inicio_poliza, historial_siniestros_asegurado.
    """
    if not archivo.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .csv")

    contenido = await archivo.read()
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")

    lector = csv.DictReader(io.StringIO(texto))
    filas  = list(lector)

    if not filas:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío")

    # Columnas opcionales con valores por defecto
    def get(row: dict, key: str, default=""):
        return row.get(key, row.get(key.upper(), row.get(key.lower(), default)))

    insertados = []
    errores    = []

    for i, fila in enumerate(filas, 1):
        try:
            sin_id = f"ING-{uuid.uuid4().hex[:8].upper()}"
            hoy    = date.today().isoformat()

            sin_data = {
                "id_siniestro":                  sin_id,
                "id_poliza":                     get(fila, "id_poliza") or "POL-INGESTA",
                "id_asegurado":                  get(fila, "id_asegurado") or f"ASEG-ING-{i:04d}",
                "ramo":                          get(fila, "ramo") or "Vehículos",
                "cobertura":                     get(fila, "cobertura") or "Daño",
                "fecha_ocurrencia":              get(fila, "fecha_ocurrencia") or hoy,
                "fecha_reporte":                 get(fila, "fecha_reporte") or hoy,
                "monto_reclamado":               float(get(fila, "monto_reclamado") or 0),
                "monto_estimado":                float(get(fila, "monto_estimado") or 0),
                "monto_pagado":                  float(get(fila, "monto_pagado") or 0),
                "estado":                        get(fila, "estado") or "Reserva",
                "sucursal":                      get(fila, "sucursal") or "Quito",
                "descripcion":                   get(fila, "descripcion") or "",
                "documentos_completos":          get(fila, "documentos_completos", "1") not in ("0", "false", "False"),
                "tiene_doc_inconsistente":       int(get(fila, "tiene_doc_inconsistente") or 0),
                "dias_desde_inicio_poliza":      int(get(fila, "dias_desde_inicio_poliza") or 180),
                "dias_desde_fin_poliza":         int(get(fila, "dias_desde_fin_poliza") or 180),
                "dias_entre_ocurrencia_reporte": int(get(fila, "dias_entre_ocurrencia_reporte") or 0),
                "historial_siniestros_asegurado": int(get(fila, "historial_siniestros_asegurado") or 0),
                "etiqueta_fraude_simulada":      int(get(fila, "etiqueta_fraude_simulada") or 0),
                "similitud_narrativa":           0.0,
                "id_proveedor_beneficiario":     get(fila, "id_proveedor") or None,
            }

            # Insertar siniestro
            db.execute(text("""
                INSERT INTO siniestros (
                    id_siniestro, id_poliza, id_asegurado, ramo, cobertura,
                    fecha_ocurrencia, fecha_reporte, monto_reclamado, monto_estimado,
                    monto_pagado, estado, sucursal, descripcion, documentos_completos,
                    tiene_doc_inconsistente, dias_desde_inicio_poliza, dias_desde_fin_poliza,
                    dias_entre_ocurrencia_reporte, historial_siniestros_asegurado,
                    etiqueta_fraude_simulada, similitud_narrativa, id_proveedor_beneficiario
                ) VALUES (
                    :id_siniestro, :id_poliza, :id_asegurado, :ramo, :cobertura,
                    :fecha_ocurrencia, :fecha_reporte, :monto_reclamado, :monto_estimado,
                    :monto_pagado, :estado, :sucursal, :descripcion, :documentos_completos,
                    :tiene_doc_inconsistente, :dias_desde_inicio_poliza, :dias_desde_fin_poliza,
                    :dias_entre_ocurrencia_reporte, :historial_siniestros_asegurado,
                    :etiqueta_fraude_simulada, :similitud_narrativa, :id_proveedor_beneficiario
                )
            """), sin_data)

            # Calcular score
            prov_data = {"en_lista_restrictiva": False, "pct_casos_observados": 0.0}
            resultado = calcular_score_hibrido(siniestro={**sin_data, "suma_asegurada": float(get(fila, "suma_asegurada") or 10000)}, proveedor=prov_data)

            db.execute(text("""
                INSERT INTO scores_riesgo (id_siniestro, score_normalizado, nivel_riesgo, alertas_activadas, calculado_en)
                VALUES (:id, :score, :nivel, :alertas, NOW())
            """), {
                "id":      sin_id,
                "score":   resultado["score_normalizado"],
                "nivel":   resultado["nivel_riesgo"],
                "alertas": resultado["alertas_activadas"],
            })

            insertados.append({
                "id":    sin_id,
                "fila":  i,
                "score": resultado["score_normalizado"],
                "nivel": resultado["nivel_riesgo"],
            })

        except Exception as e:
            errores.append({"fila": i, "error": str(e)})

    if insertados:
        db.commit()

    rojos     = sum(1 for r in insertados if r["nivel"] == "ROJO")
    amarillos = sum(1 for r in insertados if r["nivel"] == "AMARILLO")

    return {
        "mensaje":    f"✅ {len(insertados)} casos ingresados · {rojos} ROJO · {amarillos} AMARILLO · {len(errores)} errores",
        "insertados": insertados,
        "errores":    errores,
    }


# ── DOCUMENTOS DEL EXPEDIENTE ─────────────────────────────────────────────────

@router.get("/{id_siniestro}/documentos")
def listar_documentos(id_siniestro: str, db: Session = Depends(get_db)):
    """Lista documentos disponibles: PDFs del dataset oficial + archivos subidos por el analista."""
    _init_tabla(db)
    docs = _docs_dataset(id_siniestro)

    rows = db.execute(text("""
        SELECT id, tipo_documento, nombre_archivo, subido_en, origen,
               CASE WHEN analisis_ia IS NOT NULL THEN 1 ELSE 0 END AS tiene_analisis
        FROM archivos_siniestro WHERE id_siniestro = :id ORDER BY subido_en DESC
    """), {"id": id_siniestro}).mappings().all()

    for r in rows:
        tipo = r["tipo_documento"]
        docs.append({
            "id":            f"upload_{r['id']}",
            "tipo":          tipo,
            "label":         TIPO_INFO.get(tipo, {}).get("label", tipo),
            "nombre":        r["nombre_archivo"],
            "origen":        r["origen"],
            "icono":         TIPO_INFO.get(tipo, {}).get("icono", "description"),
            "db_id":         r["id"],
            "tiene_analisis": bool(r["tiene_analisis"]),
        })

    return {"id_siniestro": id_siniestro, "documentos": docs, "total": len(docs)}


@router.post("/{id_siniestro}/documentos/subir")
async def subir_documento(
    id_siniestro: str,
    tipo_documento: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sube un PDF para el siniestro y lo almacena en la base de datos."""
    _init_tabla(db)

    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos PDF")
    if tipo_documento not in TIPO_INFO:
        raise HTTPException(400, f"tipo_documento debe ser uno de: {list(TIPO_INFO.keys())}")

    contenido = await archivo.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(413, "Archivo demasiado grande (máx 10 MB)")

    db.execute(text("""
        INSERT INTO archivos_siniestro (id_siniestro, tipo_documento, nombre_archivo, contenido_pdf, origen)
        VALUES (:id, :tipo, :nombre, :contenido, 'upload')
    """), {"id": id_siniestro, "tipo": tipo_documento, "nombre": archivo.filename, "contenido": contenido})
    db.commit()

    return {
        "mensaje":   f"✅ '{archivo.filename}' registrado para {id_siniestro}",
        "tipo":      tipo_documento,
        "tamaño_kb": round(len(contenido) / 1024, 1),
    }


class AnalizarDocRequest(BaseModel):
    doc_id: str  # "dataset_factura" | "upload_123"


@router.post("/{id_siniestro}/documentos/analizar")
def analizar_documento(
    id_siniestro: str,
    body: AnalizarDocRequest,
    db: Session = Depends(get_db),
):
    """Analiza un documento del expediente con Gemini IA y detecta inconsistencias."""
    _init_tabla(db)

    pdf_bytes: bytes = b""
    nombre_doc = body.doc_id

    if body.doc_id.startswith("dataset_"):
        tipo = body.doc_id[len("dataset_"):]
        docs = _docs_dataset(id_siniestro)
        doc  = next((d for d in docs if d["tipo"] == tipo), None)
        if not doc:
            raise HTTPException(404, f"No hay {TIPO_INFO.get(tipo, {}).get('label', tipo)} en el dataset para {id_siniestro}")
        ruta = PDF_BASE / TIPO_INFO[tipo]["carpeta"] / doc["nombre"]
        pdf_bytes  = ruta.read_bytes()
        nombre_doc = doc["nombre"]

    elif body.doc_id.startswith("upload_"):
        db_id = int(body.doc_id[len("upload_"):])
        row = db.execute(text(
            "SELECT contenido_pdf, nombre_archivo, analisis_ia FROM archivos_siniestro WHERE id = :id AND id_siniestro = :sin"
        ), {"id": db_id, "sin": id_siniestro}).mappings().first()
        if not row:
            raise HTTPException(404, "Documento no encontrado")
        if row["analisis_ia"]:
            return {"id_siniestro": id_siniestro, "doc_id": body.doc_id,
                    "analisis": row["analisis_ia"], "nombre": row["nombre_archivo"], "cached": True}
        pdf_bytes  = row["contenido_pdf"]
        nombre_doc = row["nombre_archivo"]
    else:
        raise HTTPException(400, "doc_id inválido. Usar 'dataset_factura' o 'upload_123'")

    sin = db.execute(text(
        "SELECT ramo, cobertura, monto_reclamado, fecha_ocurrencia, estado FROM siniestros WHERE id_siniestro = :id"
    ), {"id": id_siniestro}).mappings().first()
    if not sin:
        raise HTTPException(404, f"Siniestro {id_siniestro} no encontrado")

    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""Eres un analista antifraude de seguros. Analiza este documento del siniestro {id_siniestro}.

Datos registrados en el sistema:
  Ramo: {sin['ramo']} | Cobertura: {sin['cobertura']}
  Monto reclamado: ${sin['monto_reclamado']} | Fecha ocurrencia: {sin['fecha_ocurrencia']}
  Estado: {sin['estado']}

Revisa el documento y responde de forma concisa y estructurada:
1. ¿Qué información contiene el documento?
2. ¿Los datos del documento coinciden con el siniestro registrado (fechas, montos, partes)?
3. ¿Hay inconsistencias, campos sospechosos o señales que requieran revisión?
4. ¿Falta información obligatoria?

Sé específico. NO acuses de fraude — solo señala lo que requiere revisión humana."""

    pdf_b64  = base64.b64encode(pdf_bytes).decode("utf-8")
    response = model.generate_content([
        prompt,
        {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
    ])
    analisis = response.text

    if body.doc_id.startswith("upload_"):
        db_id = int(body.doc_id[len("upload_"):])
        db.execute(text("UPDATE archivos_siniestro SET analisis_ia = :a WHERE id = :id"), {"a": analisis, "id": db_id})
        db.commit()

    return {"id_siniestro": id_siniestro, "doc_id": body.doc_id,
            "analisis": analisis, "nombre": nombre_doc, "cached": False}
