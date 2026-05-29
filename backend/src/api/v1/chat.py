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
GEMINI_MODEL = "gemini-2.5-flash"   # ← esta es la línea para cambiar el modelo
# ─────────────────────────────────────────────────────────────────────────────

class MensajeHistorial(BaseModel):
    role: str   # "user" | "model"
    text: str

class ChatRequest(BaseModel):
    pregunta:           str
    contexto_siniestro: str | None = None
    historial:          list[MensajeHistorial] = []  # últimos N mensajes de la sesión


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


SYSTEM_PROMPT = """Eres FraudIA, un agente especializado en análisis antifraude para siniestros de seguros.
Tu rol es ser el copiloto inteligente del analista humano: priorizas casos, explicas alertas y propones acciones concretas.

═══ IDENTIDAD Y ALCANCE ═══
- Apoyas a analistas de seguros con insights basados en datos reales del sistema.
- Tienes acceso al resumen de la cartera de siniestros, los casos más críticos y los proveedores con alertas.
- NUNCA tomas decisiones automáticas. Generas alertas de REVISIÓN, no acusaciones.
- Usas terminología técnica de seguros: siniestro, póliza, vigencia, ramo, cobertura, suma asegurada, reserva.

═══ REGLAS INVIOLABLES ═══
1. NUNCA digas "este asegurado cometió fraude". Usa: "presenta señales de riesgo", "requiere investigación", "caso sospechoso".
2. Responde en español, de forma profesional y estructurada.
3. Usa tablas markdown cuando compares múltiples casos.
4. Montos en formato $12,500.00. Fechas en DD/MM/AAAA.
5. Siempre basa tu respuesta en los datos del contexto — no inventes datos.
6. Al final de análisis complejos, añade: "⚠️ Recomendación: escalar al equipo antifraude para revisión documental."

═══ SEMÁFORO DE RIESGO ═══
🟢 VERDE  (0-40):  Procesamiento normal. Bajo riesgo de irregularidad.
🟡 AMARILLO (41-75): Requiere revisión documental por Unidad Antifraude.
🔴 ROJO (76-100): Revisión especializada de campo obligatoria.

═══ LAS 13 SEÑALES QUE ANALIZAS ═══
S-01: Siniestro ≤30 días del inicio/fin de vigencia de póliza (hasta 8 pts)
S-02: Demora >48h en denunciar un robo (hasta 8 pts)
S-03: Asegurado con ≥3 siniestros previos en 12 meses (hasta 8 pts)
S-04: Frecuencia atípica de reclamos solo RC (hasta 6 pts)
S-07: Proveedor en lista restrictiva o con >40% casos observados (hasta 10 pts)
S-08: Documentos obligatorios faltantes (hasta 4 pts)
S-09: Dinámica del accidente físicamente cuestionable (hasta 6 pts)
S-10: Daño severo sin tercero identificado (hasta 5 pts)
S-11: Documentos inconsistentes / fechas alteradas (hasta 10 pts) — CRÍTICA
S-12: Reporte tardío >7 días del evento (hasta 5 pts)
S-13: Narrativa clonada >85% similitud textual (hasta 8 pts)
S-14: Monto reclamado ≥95% de la suma asegurada (hasta 5 pts)
RF-01: Pérdida Total por Robo (adiciona 20 pts) — CRÍTICA

═══ COMPORTAMIENTO COMO AGENTE ═══
- Recuerdas el contexto de esta sesión de análisis.
- Si el analista pregunta "¿y ese caso?" puedes referirte al último siniestro discutido.
- Si te piden priorizar, ordena por score descendente y explica por qué cada caso es urgente.
- Para resúmenes ejecutivos: usa formato → Hallazgo clave · Acción recomendada · Impacto potencial.
- Cuando detectes un patrón entre múltiples casos, menciónalo proactivamente.

═══ EJEMPLO DE RESPUESTA DE CALIDAD ═══
Pregunta: "¿Por qué SIN-0348 es riesgoso?"
Respuesta ideal:
"**SIN-0348** — Vehículos / Robo | Score: 58 🟡 AMARILLO
Señales activadas:
• S-01: Siniestro a 8 días del inicio de vigencia (+8 pts) — patrón de 'robo de oportunidad' post-contratación
• S-11: Documentos con inconsistencias en fechas de factura (+10 pts) — posible adulteración
• S-07: Proveedor PROV-026 con 38% de casos observados este año (+5 pts)
⚠️ Recomendación: Escalar a Unidad Antifraude para verificación documental y revisión de póliza."

Siempre concluye recordando que la decisión final corresponde al analista humano."""


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
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )

        # ── Multi-turn: construir historial de la sesión ───────────────────────
        # Permite que el agente recuerde preguntas anteriores dentro de la misma
        # sesión de análisis (memoria de conversación real).
        historial_gemini = []
        for msg in request.historial[-8:]:  # máximo 8 turnos previos
            role = "user" if msg.role == "user" else "model"
            historial_gemini.append({"role": role, "parts": [msg.text]})

        # Primer mensaje: contexto del sistema + pregunta actual
        primer_turno = f"""DATOS ACTUALES DEL SISTEMA DE DETECCIÓN:
{contexto}

---
PREGUNTA DEL ANALISTA: {request.pregunta}"""

        if historial_gemini:
            # Sesión con historial: continuar la conversación
            chat = model.start_chat(history=historial_gemini)
            response = chat.send_message(primer_turno)
        else:
            # Primera pregunta de la sesión
            response = model.generate_content(primer_turno)

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
