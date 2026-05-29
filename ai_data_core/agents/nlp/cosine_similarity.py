"""
ai_data_core/agents/nlp/cosine_similarity.py
Módulo NLP standalone para análisis de similitud de narrativas.
Implementa TF-IDF + Cosine Similarity para detección de la Regla RF-07.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Tipos ─────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoSimilitud:
    """Resultado del análisis de similitud entre dos narrativas."""
    id_siniestro_1:  str
    id_siniestro_2:  str
    similitud:       float
    porcentaje:      str
    nivel_alerta:    str    # ROJO / AMARILLO / VERDE
    activa_rf07:     bool
    descripcion_1:   str = ""
    descripcion_2:   str = ""

    def __repr__(self) -> str:
        return (f"ResultadoSimilitud({self.id_siniestro_1} ↔ {self.id_siniestro_2} "
                f"| {self.porcentaje} | {self.nivel_alerta})")


# ── Preprocesamiento ──────────────────────────────────────────────────────────

def preprocesar_texto(texto: str) -> str:
    """
    Normaliza el texto de una narrativa para vectorización.
    Conserva tildes y caracteres del español.
    """
    if not texto or not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-záéíóúüñ\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


# ── Motor de similitud ────────────────────────────────────────────────────────

class MotorSimilitudNarrativas:
    """
    Motor de similitud textual para narrativas de siniestros.

    Implementa la Regla RF-07 del hackIAthon:
    - Similitud > 85% → ROJO   (narrativa clonada, alerta crítica)
    - Similitud 70-84% → AMARILLO (posible plantilla compartida)
    - Similitud < 70%  → VERDE  (narrativa original)

    Uso:
        motor = MotorSimilitudNarrativas()
        motor.ajustar(ids, textos)
        pares = motor.detectar_clonadas(umbral_minimo=0.50)
    """

    UMBRAL_ROJO:     float = 0.85
    UMBRAL_AMARILLO: float = 0.70

    def __init__(self, ngram_range: tuple = (1, 2), max_features: int = 500):
        self.vectorizer = TfidfVectorizer(
            min_df=1,
            max_df=0.95,
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,
            preprocessor=preprocesar_texto,
        )
        self._ids:        list[str] = []
        self._textos:     list[str] = []
        self._matrix     = None
        self._ajustado   = False

    # ── Ajuste ────────────────────────────────────────────────────────────────

    def ajustar(self, ids: list[str], textos: list[str]) -> "MotorSimilitudNarrativas":
        """Ajusta el vectorizador con el corpus de narrativas."""
        if len(ids) != len(textos):
            raise ValueError("ids y textos deben tener la misma longitud")
        self._ids    = ids
        self._textos = textos
        self._matrix = self.vectorizer.fit_transform(textos)
        self._ajustado = True
        return self

    # ── Análisis ──────────────────────────────────────────────────────────────

    def similitud_entre_dos(self, texto_1: str, texto_2: str) -> float:
        """Calcula la similitud coseno entre dos textos sin necesidad de ajuste previo."""
        vec = TfidfVectorizer(ngram_range=(1, 2), preprocessor=preprocesar_texto)
        try:
            matrix = vec.fit_transform([texto_1, texto_2])
            return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        except Exception:
            return 0.0

    def calcular_similitud_textos(self, texto_1: str, texto_2: str) -> float:
        """Alias público para compatibilidad."""
        return self.similitud_entre_dos(texto_1, texto_2)

    def detectar_clonadas(
        self,
        umbral_minimo: float = 0.50,
        limite: Optional[int] = None,
    ) -> list[ResultadoSimilitud]:
        """
        Detecta pares de siniestros con narrativas similares.

        Args:
            umbral_minimo: Similitud mínima para reportar un par.
            limite:        Si se provee, retorna solo los N pares más similares.

        Returns:
            Lista de ResultadoSimilitud ordenada por similitud descendente.
        """
        if not self._ajustado:
            raise RuntimeError("Llama a ajustar() antes de detectar_clonadas()")

        sim_matrix = cosine_similarity(self._matrix)
        np.fill_diagonal(sim_matrix, 0)

        resultados: list[ResultadoSimilitud] = []
        visitados: set[tuple] = set()

        for i in range(len(self._ids)):
            j     = int(sim_matrix[i].argmax())
            sim   = float(sim_matrix[i, j])

            par = tuple(sorted([self._ids[i], self._ids[j]]))
            if par in visitados or sim < umbral_minimo:
                continue
            visitados.add(par)

            nivel = self._clasificar_nivel(sim)
            resultados.append(ResultadoSimilitud(
                id_siniestro_1 = self._ids[i],
                id_siniestro_2 = self._ids[j],
                similitud      = round(sim, 4),
                porcentaje     = f"{sim*100:.1f}%",
                nivel_alerta   = nivel,
                activa_rf07    = sim > self.UMBRAL_ROJO,
                descripcion_1  = self._textos[i][:100],
                descripcion_2  = self._textos[j][:100],
            ))

        resultados.sort(key=lambda r: r.similitud, reverse=True)
        return resultados[:limite] if limite else resultados

    def analizar_texto_libre(self, texto: str) -> dict:
        """
        Compara un texto libre contra todo el corpus ajustado.
        Útil para analizar nuevos reclamos en tiempo real.
        """
        if not self._ajustado:
            raise RuntimeError("Llama a ajustar() antes de analizar_texto_libre()")

        texto_vec = self.vectorizer.transform([preprocesar_texto(texto)])
        sims      = cosine_similarity(texto_vec, self._matrix)[0]
        top_idx   = sims.argsort()[::-1][:5]

        similares = [
            {
                "id_siniestro": self._ids[i],
                "similitud":    round(float(sims[i]), 4),
                "porcentaje":   f"{sims[i]*100:.1f}%",
                "nivel_alerta": self._clasificar_nivel(float(sims[i])),
                "descripcion":  self._textos[i][:80] + "...",
            }
            for i in top_idx
            if sims[i] > 0.30
        ]

        return {
            "texto_analizado":      texto[:100],
            "siniestros_similares": similares,
            "alerta_rf07":          any(s["similitud"] > self.UMBRAL_ROJO for s in similares),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clasificar_nivel(self, similitud: float) -> str:
        if similitud > self.UMBRAL_ROJO:
            return "ROJO"
        if similitud > self.UMBRAL_AMARILLO:
            return "AMARILLO"
        return "VERDE"

    def resumen_estadistico(self) -> dict:
        """Retorna estadísticas del corpus ajustado."""
        if not self._ajustado:
            return {}
        sim_matrix = cosine_similarity(self._matrix)
        np.fill_diagonal(sim_matrix, 0)
        sims_upper = sim_matrix[np.triu_indices_from(sim_matrix, k=1)]
        return {
            "total_narrativas":    len(self._ids),
            "vocabulario":         len(self.vectorizer.vocabulary_),
            "pares_clonados_rojo": int((sims_upper > self.UMBRAL_ROJO).sum()),
            "pares_sospechosos":   int(((sims_upper > self.UMBRAL_AMARILLO) & (sims_upper <= self.UMBRAL_ROJO)).sum()),
            "similitud_promedio":  round(float(sims_upper.mean()), 4),
            "similitud_max":       round(float(sims_upper.max()), 4),
        }


# ── Función de conveniencia ───────────────────────────────────────────────────

def calcular_similitud_textos(texto1: str, texto2: str) -> float:
    """
    Función standalone para calcular similitud entre dos textos.
    Compatible con la interfaz del ai_data_core original.
    """
    motor = MotorSimilitudNarrativas()
    return motor.similitud_entre_dos(texto1, texto2)


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    try:
        df = pd.read_csv('../../data/synthetic/siniestros_scored.csv')
    except FileNotFoundError:
        print("⚠ Ejecutar desde ai_data_core/agents/nlp/")
        raise

    motor = MotorSimilitudNarrativas()
    motor.ajustar(df['id_siniestro'].tolist(), df['descripcion'].fillna('').tolist())

    resumen = motor.resumen_estadistico()
    print(f"{'='*50}")
    print(f"  ANÁLISIS NLP — FraudIA Claims")
    print(f"{'='*50}")
    for k, v in resumen.items():
        print(f"  {k:<30}: {v}")

    print("\nTop 5 pares más similares (RF-07):")
    for r in motor.detectar_clonadas(umbral_minimo=0.85, limite=5):
        print(f"  {r}")