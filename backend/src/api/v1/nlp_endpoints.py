"""
GET  /api/v1/nlp/similitud          — narrativas más similares entre sí
POST /api/v1/nlp/analizar           — analizar texto de un reclamo
GET  /api/v1/nlp/clonadas           — casos con narrativas clonadas (>85%)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.core.database import get_db

router = APIRouter()


class AnalizarRequest(BaseModel):
    texto: str
    id_siniestro: str | None = None


def calcular_similitudes(descripciones: list, ids: list) -> list:
    """Calcula similitud TF-IDF entre todas las narrativas."""
    if len(descripciones) < 2:
        return []

    vectorizer = TfidfVectorizer(
        min_df=1,
        ngram_range=(1, 2),
        max_features=500,
    )
    tfidf_matrix = vectorizer.fit_transform(descripciones)
    sim_matrix   = cosine_similarity(tfidf_matrix)
    np.fill_diagonal(sim_matrix, 0)

    pares = []
    vistos = set()

    for i in range(len(ids)):
        max_sim = float(sim_matrix[i].max())
        j       = int(sim_matrix[i].argmax())

        par_key = tuple(sorted([ids[i], ids[j]]))
        if par_key in vistos or max_sim < 0.50:
            continue
        vistos.add(par_key)

        pares.append({
            "siniestro_1":  ids[i],
            "siniestro_2":  ids[j],
            "similitud":    round(max_sim, 4),
            "porcentaje":   f"{max_sim*100:.1f}%",
            "nivel_alerta": "ROJO" if max_sim > 0.85 else "AMARILLO" if max_sim > 0.70 else "VERDE",
        })

    return sorted(pares, key=lambda x: x["similitud"], reverse=True)


@router.get("/similitud")
def get_similitudes(
    limite: int = 20,
    db: Session = Depends(get_db),
):
    """Top pares de siniestros con narrativas más similares."""
    rows = db.execute(text("""
        SELECT id_siniestro, descripcion
        FROM siniestros
        WHERE descripcion IS NOT NULL AND descripcion != ''
        LIMIT 300
    """)).mappings().all()

    if len(rows) < 2:
        return {"pares": [], "total": 0}

    ids          = [r["id_siniestro"] for r in rows]
    descripciones = [str(r["descripcion"]) for r in rows]

    pares = calcular_similitudes(descripciones, ids)

    return {
        "total":    len(pares),
        "pares":    pares[:limite],
        "resumen": {
            "clonadas":  sum(1 for p in pares if p["similitud"] > 0.85),
            "sospechosas": sum(1 for p in pares if 0.70 < p["similitud"] <= 0.85),
        }
    }


@router.get("/clonadas")
def get_narrativas_clonadas(db: Session = Depends(get_db)):
    """Siniestros con narrativas clonadas (similitud > 85%) — señal RF-07."""
    rows = db.execute(text("""
        SELECT s.id_siniestro, s.descripcion, s.ramo,
               s.monto_reclamado, sc.nivel_riesgo, sc.score_normalizado
        FROM siniestros s
        LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
        WHERE s.descripcion IS NOT NULL
        LIMIT 300
    """)).mappings().all()

    ids           = [r["id_siniestro"] for r in rows]
    descripciones = [str(r["descripcion"]) for r in rows]
    datos         = {r["id_siniestro"]: dict(r) for r in rows}

    pares = calcular_similitudes(descripciones, ids)
    clonadas = [p for p in pares if p["similitud"] > 0.85]

    # Enriquecer con datos del siniestro
    resultado = []
    for par in clonadas[:50]:
        resultado.append({
            **par,
            "detalle_1": {
                "ramo":            datos[par["siniestro_1"]]["ramo"],
                "monto_reclamado": float(datos[par["siniestro_1"]]["monto_reclamado"]),
                "nivel_riesgo":    datos[par["siniestro_1"]]["nivel_riesgo"],
            },
            "detalle_2": {
                "ramo":            datos[par["siniestro_2"]]["ramo"],
                "monto_reclamado": float(datos[par["siniestro_2"]]["monto_reclamado"]),
                "nivel_riesgo":    datos[par["siniestro_2"]]["nivel_riesgo"],
            },
        })

    return {
        "total_clonadas": len(clonadas),
        "casos":          resultado,
        "regla_activada": "RF-07 — Narrativa Idéntica (Clonada)",
    }


@router.post("/analizar")
def analizar_texto(request: AnalizarRequest, db: Session = Depends(get_db)):
    """
    Analiza el texto de un reclamo y retorna:
    - Palabras clave detectadas
    - Señales de riesgo en el texto
    - Siniestros similares en la BD
    """
    texto = request.texto.lower()

    # Señales de riesgo en el texto
    señales = {
        "sin_testigos":      any(k in texto for k in ["sin testigos", "no hay testigos", "nadie vio"]),
        "sin_camaras":       any(k in texto for k in ["sin cámaras", "no hay cámaras", "zona sin cámaras"]),
        "fuga_tercero":      any(k in texto for k in ["se dio a la fuga", "huyó", "sin placas", "no identificado"]),
        "perdida_total":     any(k in texto for k in ["pérdida total", "completamente destruido", "irreparable"]),
        "madrugada":         any(k in texto for k in ["madrugada", "de noche", "sin luz"]),
        "accidente_multiple": any(k in texto for k in ["múltiple", "varios vehículos", "3 vehículos"]),
        "circunstancias_confusas": any(k in texto for k in ["no del todo claro", "circunstancias", "sin explicación"]),
    }

    señales_activas = [k for k, v in señales.items() if v]
    puntos_texto    = len(señales_activas) * 2

    # Buscar narrativas similares en BD
    rows = db.execute(text("""
        SELECT id_siniestro, descripcion FROM siniestros
        WHERE descripcion IS NOT NULL LIMIT 300
    """)).mappings().all()

    similares = []
    if rows:
        ids           = [r["id_siniestro"] for r in rows]
        descripciones = [str(r["descripcion"]) for r in rows]

        vectorizer   = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(descripciones + [request.texto])
        sims         = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]

        top_indices = sims.argsort()[-5:][::-1]
        for idx in top_indices:
            if sims[idx] > 0.30:
                similares.append({
                    "id_siniestro": ids[idx],
                    "similitud":    round(float(sims[idx]), 4),
                    "porcentaje":   f"{sims[idx]*100:.1f}%",
                })

    return {
        "texto_analizado":  request.texto[:200],
        "señales_detectadas": señales_activas,
        "puntos_riesgo_texto": puntos_texto,
        "nivel_sospecha":  "ALTO" if puntos_texto >= 4 else "MEDIO" if puntos_texto >= 2 else "BAJO",
        "siniestros_similares": similares,
        "total_similares": len(similares),
    }
