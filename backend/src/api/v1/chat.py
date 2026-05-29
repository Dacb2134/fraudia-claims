"""
POST /api/v1/chat          — consulta al agente
POST /api/v1/chat/archivo  — consulta con archivo adjunto (PDF, TXT, imagen)
"""
import os
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.core.database import get_db

router = APIRouter()

# ── Cambiar el modelo aquí cuando quieras ─────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"   # ← esta es la línea para cambiar el modelo
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    pregunta:           str
    contexto_siniestro: str | None = None


def obtener_contexto_bd(db: Session, id_siniestro: str | None = None) -> str:
    """Obtiene resumen real de la BD para darle contexto al agente."""

    resumen = db.execute(text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN sc.nivel_riesgo = 'ROJO'     THEN 1 ELSE 0 END) AS rojos,
            SUM(CASE WHEN sc.nivel_riesgo = 'AMARILLO' THEN 1 ELSE 0 END) AS amarillos,
            SUM(CASE WHEN sc.nivel_riesgo = 'VERDE'    THEN 1 ELSE 0 END) AS verdes,
            ROUND(AVG(sc.score_normalizado), 1) AS score_promedio
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
    """)).mappings().first()

    top5 = db.execute(text("""
        SELECT s.id_siniestro, s.ramo, s.cobertura,
               s.monto_reclamado, sc.score_normalizado,
               sc.nivel_riesgo, sc.alertas_activadas
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        ORDER BY sc.score_normalizado DESC
        LIMIT 5
    """)).mappings().all()

    top_prov = db.execute(text("""
        SELECT s.id_proveedor_beneficiario AS proveedor,
               COUNT(*) AS total,
               SUM(CASE WHEN sc.nivel_riesgo = 'ROJO' THEN 1 ELSE 0 END) AS rojos
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        WHERE s.id_proveedor_beneficiario IS NOT NULL
        GROUP BY s.id_proveedor_beneficiario
        ORDER BY rojos DESC
        LIMIT 3
    """)).mappings().all()

    contexto = f"""
RESUMEN DEL SISTEMA:
- Total siniestros: {resumen['total']}
- Nivel ROJO (alto riesgo): {resumen['rojos']}
- Nivel AMARILLO (medio): {resumen['amarillos']}
- Nivel VERDE (bajo): {resumen['verdes']}
- Score promedio: {resumen['score_promedio']}

TOP 5 SINIESTROS DE MAYOR RIESGO:
{json.dumps([dict(r) for r in top5], ensure_ascii=False, default=str)}

TOP 3 PROVEEDORES CON MÁS ALERTAS ROJAS:
{json.dumps([dict(r) for r in top_prov], ensure_ascii=False, default=str)}
"""

    if id_siniestro:
        detalle = db.execute(text("""
            SELECT s.*, sc.score_normalizado, sc.nivel_riesgo,
                   sc.alertas_activadas, sc.reglas_criticas
            FROM siniestros s
            JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
            WHERE s.id_siniestro = :id
        """), {"id": id_siniestro}).mappings().first()

        if detalle:
            contexto += f"""
DETALLE DEL SINIESTRO {id_siniestro}:
{json.dumps(dict(detalle), ensure_ascii=False, default=str)}
"""
    return contexto


SYSTEM_PROMPT = """Eres FraudIA, un agente experto en detección de posibles fraudes en siniestros de seguros.
Apoyas a analistas humanos con insights basados en datos. NUNCA tomas decisiones automáticas de pago o rechazo.

REGLAS FUNDAMENTALES:
1. NUNCA acuses a un asegurado directamente de fraude. Usa: "presenta señales de riesgo", "requiere revisión", "caso con alertas".
2. El score es una ALERTA para revisión humana, no una acusación automática.
3. Basa tus respuestas SOLO en los datos del contexto proporcionado.
4. Responde en español, de forma concisa y estructurada.
5. Montos en formato $12,500.00. Usa tablas markdown cuando aplique.

SCORE DE RIESGO (0-100):
- 0-40 🟢 VERDE: flujo normal, continuar proceso
- 41-75 🟡 AMARILLO: escalar a Unidad Antifraude para revisión documental
- 76-100 🔴 ROJO: escalar para revisión especializada de campo

SEÑALES QUE ANALIZAS:
- Borde de vigencia (siniestro ≤30 días del inicio/fin de póliza)
- Demora en denuncia de robo (>48 horas)
- Alta frecuencia de reclamos del asegurado (≥3 en 12 meses)
- Proveedor en lista restrictiva o con múltiples alertas
- Documentos incompletos o inconsistentes
- Narrativas similares o clonadas entre reclamos (>85% similitud)
- Monto reclamado cercano a la suma asegurada (≥95%)
- Reporte tardío del evento (>7 días)

PREGUNTAS QUE PUEDES RESPONDER:
1. Los 10 siniestros con mayor riesgo de posible fraude
2. Por qué un siniestro fue marcado como alto riesgo (explicar alertas activadas)
3. Qué proveedores concentran más alertas
4. Qué ramos tienen mayor porcentaje de casos sospechosos
5. Qué ciudades/sucursales presentan mayor concentración de alertas
6. Qué asegurados tienen mayor frecuencia de reclamos
7. Qué documentos faltan en casos críticos
8. Qué casos tienen montos atípicos
9. Qué siniestros ocurrieron cerca del inicio de la póliza
10. Qué patrones se repiten en reclamos sospechosos
11. Generar resumen ejecutivo de casos críticos
12. Recomendar qué casos revisar primero

Siempre concluye recordando que la decisión final es del analista humano."""


@router.post("/")
def chat_query(request: ChatRequest, db: Session = Depends(get_db)):
    """Responde preguntas sobre siniestros usando Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY no configurada en el .env"
        )

    contexto = obtener_contexto_bd(db, request.contexto_siniestro)

    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,      # ← se usa la variable de arriba
            system_instruction=SYSTEM_PROMPT,
        )

        prompt = f"""Contexto actual del sistema:

{contexto}

Pregunta del analista: {request.pregunta}"""

        response = model.generate_content(prompt)
        respuesta = response.text

        # Guardar en log
        try:
            db.execute(text("""
                INSERT INTO log_consultas_agente (pregunta, respuesta, tokens_usados)
                VALUES (:pregunta, :respuesta, :tokens)
            """), {
                "pregunta":  request.pregunta,
                "respuesta": respuesta,
                "tokens":    0,
            })
            db.commit()
        except Exception:
            pass

        return {
            "pregunta":  request.pregunta,
            "respuesta": respuesta,
            "modelo":    GEMINI_MODEL,
        }

    except Exception as e:
        err_str = str(e)
        # Manejo amigable de errores comunes
        if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
            detail = (
                "⚠️ El agente IA está temporalmente no disponible por límite de uso de la API de Google. "
                "Espera unos minutos y vuelve a intentarlo, o verifica que la GEMINI_API_KEY tenga cuota disponible."
            )
        elif "API_KEY" in err_str or "api key" in err_str.lower():
            detail = "⚠️ La clave de API de Gemini no es válida. Verifica la variable GEMINI_API_KEY."
        elif "404" in err_str or "not found" in err_str.lower():
            detail = f"⚠️ Modelo Gemini no disponible ({GEMINI_MODEL}). Contacta al administrador."
        else:
            detail = f"⚠️ Error del agente: {err_str[:200]}"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/archivo")
async def chat_con_archivo(
    pregunta: str = Form(...),
    archivo:  UploadFile = File(...),
    db:       Session = Depends(get_db),
):
    """
    Responde preguntas sobre un archivo adjunto (PDF, TXT, imagen).
    El analista puede subir un documento de siniestro y hacer preguntas sobre él.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada")

    contenido = await archivo.read()
    mime_type  = archivo.content_type or "application/octet-stream"
    nombre     = archivo.filename or "archivo"

    # Validar tamaño (máx 10 MB)
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máximo 10 MB)")

    tipos_permitidos = {
        "application/pdf", "text/plain", "text/csv",
        "image/jpeg", "image/png", "image/webp",
    }
    if mime_type not in tipos_permitidos:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no soportado: {mime_type}. Usa PDF, TXT, CSV o imagen."
        )

    contexto = obtener_contexto_bd(db)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)

        partes = [
            f"Contexto del sistema:\n{contexto}\n\nEl analista adjuntó el archivo '{nombre}'.\nPregunta: {pregunta}",
            {"mime_type": mime_type, "data": contenido},
        ]

        response  = model.generate_content(partes)
        respuesta = response.text

        try:
            db.execute(text("""
                INSERT INTO log_consultas_agente (pregunta, respuesta, tokens_usados)
                VALUES (:p, :r, 0)
            """), {"p": f"[ARCHIVO: {nombre}] {pregunta}", "r": respuesta})
            db.commit()
        except Exception:
            pass

        return {
            "pregunta":  pregunta,
            "archivo":   nombre,
            "respuesta": respuesta,
            "modelo":    GEMINI_MODEL,
        }

    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "quota" in err_str.lower():
            detail = "⚠️ Límite de uso de la API alcanzado. Espera unos minutos y vuelve a intentarlo."
        else:
            detail = f"⚠️ Error procesando archivo: {err_str[:200]}"
        raise HTTPException(status_code=500, detail=detail)
