"""
ai_data_core/agents/orchestrator.py
Orquestador principal del agente FraudIA.
Coordina el motor de reglas, modelo ML, NLP y el agente conversacional.
"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass, field
from typing import Optional

# Importaciones internas (relativas al proyecto)
try:
    from agents.memory.chat_history import ChatHistoryManager
    from agents.nlp.cosine_similarity import MotorSimilitudNarrativas, calcular_similitud_textos
except ImportError:
    # Ejecución standalone
    pass


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class AlertaRiesgo:
    """Representa una alerta generada por el motor de análisis."""
    codigo:        str
    descripcion:   str
    puntos:        int
    clasificacion: str   # ROJO / AMARILLO / VERDE
    fuente:        str   # REGLAS / ML / NLP

    def to_dict(self) -> dict:
        return {
            "codigo":        self.codigo,
            "descripcion":   self.descripcion,
            "puntos":        self.puntos,
            "clasificacion": self.clasificacion,
            "fuente":        self.fuente,
        }


@dataclass
class ResultadoAnalisis:
    """Resultado completo del análisis de un siniestro."""
    id_siniestro:     str
    score_reglas:     int
    score_ml:         float
    score_hibrido:    int
    nivel_riesgo:     str
    alertas:          list[AlertaRiesgo] = field(default_factory=list)
    explicacion_ia:   Optional[str] = None
    reglas_criticas:  list[dict] = field(default_factory=list)

    @property
    def es_alto_riesgo(self) -> bool:
        return self.nivel_riesgo == "ROJO"

    def resumen(self) -> str:
        alertas_str = " | ".join(a.descripcion for a in self.alertas[:3])
        return (f"Siniestro {self.id_siniestro}: Score {self.score_hibrido}/100 "
                f"({self.nivel_riesgo}) — {alertas_str}")

    def to_dict(self) -> dict:
        return {
            "id_siniestro":    self.id_siniestro,
            "score_reglas":    self.score_reglas,
            "score_ml":        round(self.score_ml, 4),
            "score_hibrido":   self.score_hibrido,
            "nivel_riesgo":    self.nivel_riesgo,
            "alertas":         [a.to_dict() for a in self.alertas],
            "explicacion_ia":  self.explicacion_ia,
            "reglas_criticas": self.reglas_criticas,
        }


# ── Orquestador ───────────────────────────────────────────────────────────────

class AIOrchestrator:
    """
    Orquestador central del sistema FraudIA.

    Flujo de procesamiento:
    1. Motor de Reglas Deterministas → score parcial (peso 60%)
    2. Modelo ML XGBoost             → probabilidad   (peso 40%)
    3. Score Híbrido = Reglas*0.6 + ML*100*0.4
    4. NLP: similitud de narrativas  → alerta RF-07
    5. Agente IA Gemini              → explicación en lenguaje natural

    Semáforo:
    - 0-40  → VERDE   (flujo normal)
    - 41-75 → AMARILLO (revisión documental)
    - 76-100 → ROJO   (revisión especializada)
    """

    # Pesos del score híbrido
    PESO_REGLAS = 0.60
    PESO_ML     = 0.40

    # Umbrales semáforo
    UMBRAL_ROJO     = 76
    UMBRAL_AMARILLO = 41

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self._historial = ChatHistoryManager() if 'ChatHistoryManager' in dir() else None
        self._motor_nlp = MotorSimilitudNarrativas() if 'MotorSimilitudNarrativas' in dir() else None
        self._modelo_ml = None
        self._encoders  = None

    # ── Inicialización ────────────────────────────────────────────────────────

    def cargar_modelo_ml(self, model_path: str = None, encoders_path: str = None) -> bool:
        """Carga el modelo XGBoost y los encoders desde disco."""
        import pickle
        from pathlib import Path

        model_path    = model_path    or Path(__file__).parents[2] / "data/processed/fraud_model.pkl"
        encoders_path = encoders_path or Path(__file__).parents[2] / "data/processed/label_encoders.pkl"

        try:
            with open(model_path, "rb") as f:
                self._modelo_ml = pickle.load(f)
            with open(encoders_path, "rb") as f:
                self._encoders = pickle.load(f)
            return True
        except FileNotFoundError:
            return False

    def ajustar_nlp(self, ids: list[str], textos: list[str]) -> None:
        """Ajusta el motor NLP con el corpus de narrativas."""
        if self._motor_nlp:
            self._motor_nlp.ajustar(ids, textos)

    # ── Motor de Reglas ───────────────────────────────────────────────────────

    def _evaluar_reglas(self, datos: dict) -> tuple[int, list[AlertaRiesgo]]:
        """
        Evalúa las 13 señales de fraude y retorna (score, alertas).
        Implementación de las reglas RF-01 a RF-07 del hackIAthon.
        """
        score   = 0
        alertas = []

        def agregar(codigo, desc, pts, nivel, fuente="REGLAS"):
            nonlocal score
            score += pts
            alertas.append(AlertaRiesgo(codigo, desc, pts, nivel, fuente))

        # S-01: Borde de vigencia
        dias_fin = datos.get("dias_desde_fin_poliza", 999)
        if dias_fin <= 10:
            agregar("S-01", f"Siniestro a {dias_fin} días del borde de vigencia (≤10 días → 8 pts)", 8, "ROJO")
        elif dias_fin <= 30:
            agregar("S-01", f"Siniestro a {dias_fin} días del borde de vigencia (11-30 días → 4 pts)", 4, "AMARILLO")

        # S-02: Demora denuncia robo
        cobertura = str(datos.get("cobertura", "")).lower()
        dias_rep  = datos.get("dias_entre_ocurrencia_reporte", 0)
        if "robo" in cobertura:
            if dias_rep > 2:
                agregar("S-02", f"Demora de {dias_rep} días en denunciar robo (>48 h → 8 pts)", 8, "AMARILLO")
            elif dias_rep >= 1:
                agregar("S-02", f"Demora de {dias_rep} días en denunciar robo (24-48 h → 4 pts)", 4, "AMARILLO")

        # S-03: Alta frecuencia asegurado
        hist = datos.get("historial_siniestros_asegurado", 0)
        if hist >= 3:
            agregar("S-03", f"Asegurado con {hist} siniestros previos (≥3 → 8 pts)", 8, "ROJO")
        elif hist == 2:
            agregar("S-03", f"Asegurado con 2 siniestros previos (2 → 4 pts)", 4, "AMARILLO")

        # S-07: Documentos incompletos
        if not datos.get("documentos_completos", True):
            agregar("S-07", "Documentos incompletos o faltantes (4 pts)", 4, "AMARILLO")

        # S-10: Documentos inconsistentes
        if datos.get("tiene_doc_inconsistente", False):
            agregar("RF-02", "Documentos con inconsistencias detectadas (+10 pts)", 10, "ROJO")

        # S-11: Reporte tardío
        if dias_rep > 7:
            agregar("S-11", f"Reporte tardío: {dias_rep} días (>7 → 5 pts)", 5, "AMARILLO")
        elif dias_rep >= 4:
            agregar("S-11", f"Reporte tardío: {dias_rep} días (4-7 → 3 pts)", 3, "AMARILLO")

        # S-13: Monto cercano a suma asegurada
        monto  = datos.get("monto_reclamado", 0)
        suma   = datos.get("suma_asegurada", 1)
        if suma > 0 and (monto / suma) >= 0.95:
            pct = round(monto / suma * 100)
            agregar("S-13", f"Monto reclamado es {pct}% de la suma asegurada (≥95% → 4 pts)", 4, "AMARILLO")

        return min(score, 100), alertas

    # ── Score híbrido ─────────────────────────────────────────────────────────

    def _calcular_score_hibrido(self, score_reglas: int, prob_ml: float) -> int:
        hibrido = score_reglas * self.PESO_REGLAS + prob_ml * 100 * self.PESO_ML
        return int(min(100, max(0, round(hibrido))))

    def _nivel_semaforo(self, score: int) -> str:
        if score >= self.UMBRAL_ROJO:     return "ROJO"
        if score >= self.UMBRAL_AMARILLO: return "AMARILLO"
        return "VERDE"

    # ── Análisis principal ────────────────────────────────────────────────────

    def procesar_alerta(self, datos: dict) -> ResultadoAnalisis:
        """
        Procesa un siniestro completo y retorna el análisis de riesgo.

        Args:
            datos: Diccionario con campos del siniestro (ver esquema en docs/).

        Returns:
            ResultadoAnalisis con score, nivel, alertas y explicación.
        """
        id_sin = datos.get("id_siniestro", "SIN-UNKNOWN")

        # 1. Motor de reglas
        score_reglas, alertas = self._evaluar_reglas(datos)

        # 2. Modelo ML
        prob_ml = 0.0
        if self._modelo_ml is not None:
            try:
                import pandas as pd
                import numpy as np
                df_row = pd.DataFrame([datos])
                # Features mínimas necesarias
                features = [
                    "monto_reclamado", "monto_estimado", "dias_desde_inicio_poliza",
                    "dias_desde_fin_poliza", "dias_entre_ocurrencia_reporte",
                    "historial_siniestros_asegurado", "suma_asegurada",
                ]
                for col in features:
                    if col not in df_row.columns:
                        df_row[col] = 0
                X = df_row[features].fillna(0)
                prob_ml = float(self._modelo_ml.predict_proba(X)[0][1])
            except Exception:
                prob_ml = score_reglas / 100  # fallback

        # 3. Score híbrido
        score_hibrido = self._calcular_score_hibrido(score_reglas, prob_ml)
        nivel         = self._nivel_semaforo(score_hibrido)

        # 4. Reglas críticas (RF clasificación directa a ROJO)
        reglas_criticas = [a.to_dict() for a in alertas if a.clasificacion == "ROJO"]

        return ResultadoAnalisis(
            id_siniestro    = id_sin,
            score_reglas    = score_reglas,
            score_ml        = prob_ml,
            score_hibrido   = score_hibrido,
            nivel_riesgo    = nivel,
            alertas         = alertas,
            reglas_criticas = reglas_criticas,
        )

    def procesar_lote(self, lista_siniestros: list[dict]) -> list[ResultadoAnalisis]:
        """Procesa múltiples siniestros y retorna lista ordenada por riesgo."""
        resultados = [self.procesar_alerta(s) for s in lista_siniestros]
        return sorted(resultados, key=lambda r: r.score_hibrido, reverse=True)

    # ── Interfaz de consulta ──────────────────────────────────────────────────

    def consultar(self, pregunta: str, contexto: Optional[dict] = None) -> str:
        """
        Consulta al agente en lenguaje natural.
        Si no hay Gemini disponible, retorna un resumen estructurado.
        """
        if self._historial:
            self._historial.agregar_usuario(pregunta)

        if self.gemini_api_key and contexto:
            respuesta = self._consultar_gemini(pregunta, contexto)
        else:
            respuesta = self._respuesta_fallback(pregunta, contexto)

        if self._historial:
            self._historial.agregar_asistente(respuesta)

        return respuesta

    def _consultar_gemini(self, pregunta: str, contexto: dict) -> str:
        """Consulta real a la API de Gemini."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-lite",
                system_instruction=ChatHistoryManager.SYSTEM_PROMPT,
            )
            prompt = f"Contexto: {json.dumps(contexto, ensure_ascii=False, default=str)}\n\nPregunta: {pregunta}"
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._respuesta_fallback(pregunta, contexto)

    def _respuesta_fallback(self, pregunta: str, contexto: Optional[dict]) -> str:
        """Respuesta estructurada cuando Gemini no está disponible."""
        if not contexto:
            return "No hay contexto disponible para responder esta consulta."
        score = contexto.get("score_hibrido", contexto.get("score_riesgo", 0))
        nivel = contexto.get("nivel_riesgo", "VERDE")
        alertas = contexto.get("alertas_activadas", "Sin alertas")
        return (f"El siniestro presenta nivel {nivel} (score: {score}/100). "
                f"Alertas activas: {alertas}. "
                f"Se recomienda revisión {'especializada' if nivel == 'ROJO' else 'documental' if nivel == 'AMARILLO' else 'estándar'}.")


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    orquestador = AIOrchestrator()

    siniestro_test = {
        "id_siniestro":                   "SIN-TEST-001",
        "cobertura":                      "Robo",
        "dias_desde_fin_poliza":          5,
        "dias_entre_ocurrencia_reporte":  10,
        "historial_siniestros_asegurado": 3,
        "documentos_completos":           False,
        "tiene_doc_inconsistente":        True,
        "monto_reclamado":                50000,
        "suma_asegurada":                 52000,
    }

    resultado = orquestador.procesar_alerta(siniestro_test)
    print("=" * 55)
    print(f"  {resultado.resumen()}")
    print("=" * 55)
    print(f"  Score reglas : {resultado.score_reglas}")
    print(f"  Score ML     : {resultado.score_ml:.3f}")
    print(f"  Score híbrido: {resultado.score_hibrido}")
    print(f"  Nivel        : {resultado.nivel_riesgo}")
    print(f"\n  Alertas ({len(resultado.alertas)}):")
    for alerta in resultado.alertas:
        print(f"    [{alerta.clasificacion}] {alerta.descripcion}")