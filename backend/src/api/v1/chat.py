"""
POST /api/v1/chat
Agente conversacional usando Google Gemini.
"""
import os
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.core.database import get_db

router = APIRouter()

# ── Cambiar el modelo aquí cuando quieras ─────────────────────────────────────
GEMINI_MODEL = "gemini-3.1-flash-lite"   # ← esta es la línea para cambiar el modelo
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


SYSTEM_PROMPT = """Eres un analista experto en detección de fraudes en siniestros de seguros.
Ayudas a los analistas humanos a revisar casos sospechosos.

REGLAS:
1. NUNCA acuses directamente. Usa: "presenta señales de riesgo", "requiere revisión".
2. El score es una ALERTA, no una acusación automática.
3. Basa tus respuestas solo en los datos proporcionados.
4. Sé conciso y directo.
5. Montos en formato $12,500.00

Score 0-100:
- 0-40: VERDE (flujo normal)
- 41-75: AMARILLO (revisar documentación)
- 76-100: ROJO (revisión especializada)"""


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
        raise HTTPException(status_code=500, detail=f"Error del agente: {str(e)}")
