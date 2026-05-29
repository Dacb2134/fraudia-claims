"""
POST /api/v1/chat
Agente conversacional usando Claude API.
Responde preguntas sobre los siniestros usando datos reales de la BD.
"""
import os
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.core.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    pregunta: str
    contexto_siniestro: str | None = None  # id_siniestro opcional para preguntas específicas


def obtener_contexto_bd(db: Session, id_siniestro: str | None = None) -> str:
    """Obtiene un resumen de la BD para darle contexto al agente."""

    # Resumen general
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

    # Top 5 casos más riesgosos
    top5 = db.execute(text("""
        SELECT s.id_siniestro, s.ramo, s.cobertura, s.monto_reclamado,
               sc.score_normalizado, sc.nivel_riesgo, sc.alertas_activadas
        FROM siniestros s
        JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        ORDER BY sc.score_normalizado DESC
        LIMIT 5
    """)).mappings().all()

    # Top 3 proveedores problemáticos
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
{json.dumps([dict(r) for r in top_prov], ensure_ascii=False)}
"""

    # Si se pide detalle de un siniestro específico
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


@router.post("/")
def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Responde preguntas sobre los siniestros usando Claude.
    El agente tiene contexto real de la base de datos.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY no configurada en el .env"
        )

    # Obtener contexto real de la BD
    contexto = obtener_contexto_bd(db, request.contexto_siniestro)

    # System prompt del agente
    system_prompt = """Eres un analista experto en detección de fraudes en siniestros de seguros.
Tu función es ayudar a los analistas humanos a revisar casos sospechosos.

REGLAS IMPORTANTES:
1. NUNCA acuses directamente a un asegurado de fraude. Usa lenguaje como "presenta señales de riesgo", "requiere revisión", "posible irregularidad".
2. Siempre recuerda que el score es una ALERTA, no una acusación.
3. Basa tus respuestas ÚNICAMENTE en los datos proporcionados.
4. Sé conciso y directo. El analista necesita información útil, no explicaciones largas.
5. Cuando menciones montos, usa formato de moneda (ej: $12,500.00).
6. Si no tienes suficiente información para responder, dilo claramente.

El sistema usa un score de 0-100 donde:
- 0-40: VERDE (bajo riesgo, flujo normal)
- 41-75: AMARILLO (revisar documentación)  
- 76-100: ROJO (revisión especializada de campo)"""

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"""Contexto actual del sistema de siniestros:

{contexto}

Pregunta del analista: {request.pregunta}"""
                }
            ]
        )

        respuesta = message.content[0].text

        # Guardar en log
        try:
            db.execute(text("""
                INSERT INTO log_consultas_agente
                    (pregunta, respuesta, tokens_usados)
                VALUES
                    (:pregunta, :respuesta, :tokens)
            """), {
                "pregunta":  request.pregunta,
                "respuesta": respuesta,
                "tokens":    message.usage.input_tokens + message.usage.output_tokens,
            })
            db.commit()
        except Exception:
            pass  # No fallar si el log falla

        return {
            "pregunta":    request.pregunta,
            "respuesta":   respuesta,
            "tokens_usados": message.usage.input_tokens + message.usage.output_tokens,
            "modelo":      "claude-sonnet-4-20250514",
        }

    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="ANTHROPIC_API_KEY inválida")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del agente: {str(e)}")
