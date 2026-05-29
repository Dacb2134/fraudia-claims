"""
tests/test_rules.py
Tests unitarios para el motor de reglas de negocio (ReglasNegocioEngine).

Ejecutar:
  cd backend
  python -m pytest tests/ -v
  python -m unittest tests.test_rules -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine.rules_evaluator import ReglasNegocioEngine


# ── Helper ────────────────────────────────────────────────────────────────────

def sin(**kwargs):
    """Siniestro base seguro para testing — anula todas las señales por defecto."""
    base = {
        "ramo": "Vehículos",
        "cobertura": "Daño",
        "estado": "Reserva",
        "monto_reclamado": 5_000.0,
        "monto_estimado":  4_000.0,
        "suma_asegurada":  20_000.0,
        "descripcion": "",
        "dias_desde_inicio_poliza":      180,
        "dias_desde_fin_poliza":         180,
        "dias_entre_ocurrencia_reporte":   2,
        "historial_siniestros_asegurado":  0,
        "documentos_completos":           True,
        "tiene_doc_inconsistente":        False,
        "similitud_narrativa":            0.0,
    }
    base.update(kwargs)
    return base


def prov(**kwargs):
    base = {"en_lista_restrictiva": False, "pct_casos_observados": 0.0}
    base.update(kwargs)
    return base


def motor(s_kwargs=None, p_kwargs=None):
    s = sin(**(s_kwargs or {}))
    p = prov(**(p_kwargs or {}))
    return ReglasNegocioEngine(s, proveedor=p).ejecutar_motor()


# ── S-01: Borde de vigencia ───────────────────────────────────────────────────

class TestS01BordeVigencia(unittest.TestCase):

    def test_sin_alerta(self):
        r = motor({"dias_desde_inicio_poliza": 180, "dias_desde_fin_poliza": 180})
        self.assertEqual(r["score_bruto"], 0)

    def test_borde_11_30_dias_inicio(self):
        r = motor({"dias_desde_inicio_poliza": 20, "dias_desde_fin_poliza": 300})
        self.assertIn("S-01", r["alertas_activadas"])
        self.assertEqual(r["score_bruto"], 4)

    def test_borde_maximo_menor_10(self):
        r = motor({"dias_desde_inicio_poliza": 3, "dias_desde_fin_poliza": 300})
        self.assertGreaterEqual(r["score_bruto"], 8)

    def test_rf05_extremo(self):
        r = motor({"dias_desde_inicio_poliza": 1, "dias_desde_fin_poliza": 300})
        self.assertIn("RF-05", r["reglas_criticas"])


# ── S-03: Frecuencia asegurado ────────────────────────────────────────────────

class TestS03Frecuencia(unittest.TestCase):

    def test_sin_historial(self):
        r = motor({"historial_siniestros_asegurado": 0})
        self.assertEqual(r["score_bruto"], 0)

    def test_historial_2(self):
        r = motor({"historial_siniestros_asegurado": 2})
        self.assertEqual(r["score_bruto"], 4)

    def test_historial_3_o_mas(self):
        r = motor({"historial_siniestros_asegurado": 3})
        self.assertEqual(r["score_bruto"], 8)

    def test_historial_alto(self):
        r = motor({"historial_siniestros_asegurado": 7})
        self.assertGreaterEqual(r["score_bruto"], 8)


# ── S-07: Proveedor restrictivo ───────────────────────────────────────────────

class TestS07Proveedor(unittest.TestCase):

    def test_proveedor_en_lista(self):
        r = motor(p_kwargs={"en_lista_restrictiva": True, "pct_casos_observados": 0.0})
        self.assertGreaterEqual(r["score_bruto"], 10)
        self.assertIn("RF-03", r["reglas_criticas"])

    def test_proveedor_normal(self):
        r = motor(p_kwargs={"en_lista_restrictiva": False, "pct_casos_observados": 0.0})
        self.assertEqual(r["score_bruto"], 0)

    def test_proveedor_alta_concentracion(self):
        r = motor(p_kwargs={"en_lista_restrictiva": False, "pct_casos_observados": 0.45})
        self.assertGreaterEqual(r["score_bruto"], 5)


# ── S-08: Documentos incompletos ──────────────────────────────────────────────

class TestS08DocIncompletos(unittest.TestCase):

    def test_docs_incompletos(self):
        r = motor({"documentos_completos": False})
        self.assertGreaterEqual(r["score_bruto"], 4)

    def test_docs_completos(self):
        r = motor({"documentos_completos": True})
        self.assertEqual(r["score_bruto"], 0)


# ── S-11: Documentos inconsistentes ──────────────────────────────────────────

class TestS11DocInconsistente(unittest.TestCase):

    def test_doc_inconsistente_int(self):
        r = motor({"tiene_doc_inconsistente": 1})
        self.assertGreaterEqual(r["score_bruto"], 10)
        self.assertIn("RF-02", r["reglas_criticas"])

    def test_doc_inconsistente_bool(self):
        r = motor({"tiene_doc_inconsistente": True})
        self.assertGreaterEqual(r["score_bruto"], 10)

    def test_doc_consistente(self):
        r = motor({"tiene_doc_inconsistente": False})
        self.assertNotIn("RF-02", r.get("reglas_criticas", []))


# ── S-12: Reporte tardío ─────────────────────────────────────────────────────

class TestS12ReporteTardio(unittest.TestCase):

    def test_reporte_a_tiempo(self):
        r = motor({"dias_entre_ocurrencia_reporte": 2})
        self.assertEqual(r["score_bruto"], 0)

    def test_reporte_tardio_mas_7(self):
        r = motor({"dias_entre_ocurrencia_reporte": 10})
        self.assertGreaterEqual(r["score_bruto"], 5)


# ── RF-01: Pérdida Total por Robo ─────────────────────────────────────────────

class TestRF01RoboTotal(unittest.TestCase):

    def test_rf01_dispara(self):
        r = motor({"cobertura": "Robo Total", "estado": "Pérdida Total por Robo"})
        self.assertGreaterEqual(r["score_bruto"], 20)
        self.assertIn("RF-01", r["reglas_criticas"])

    def test_rf01_no_sin_robo(self):
        r = motor({"cobertura": "Daño", "estado": "Pérdida Total por Robo"})
        self.assertNotIn("RF-01", r["reglas_criticas"])

    def test_rf01_no_sin_perdida_total(self):
        r = motor({"cobertura": "Robo Total", "estado": "Reserva"})
        self.assertNotIn("RF-01", r["reglas_criticas"])


# ── Score y nivel ─────────────────────────────────────────────────────────────

class TestScoreNivel(unittest.TestCase):

    def test_base_es_verde(self):
        r = motor()
        self.assertEqual(r["nivel_riesgo"], "VERDE")
        self.assertLessEqual(r["score_normalizado"], 40)

    def test_amarillo_varias_senales(self):
        r = motor(
            {"historial_siniestros_asegurado": 3, "tiene_doc_inconsistente": 1,
             "documentos_completos": False, "dias_desde_inicio_poliza": 20},
            {"en_lista_restrictiva": False},
        )
        self.assertIn(r["nivel_riesgo"], ("AMARILLO", "ROJO"))
        self.assertGreaterEqual(r["score_normalizado"], 25)

    def test_rojo_combinacion_critica(self):
        """Combinación RF-01+S-11+S-07+S-03+S-01+S-02+S-12+S-08 → score_bruto=73 → 81 → ROJO."""
        r = motor(
            {
                "cobertura":                     "Robo Total",
                "estado":                        "Pérdida Total por Robo",
                "tiene_doc_inconsistente":        1,
                "documentos_completos":           False,
                "historial_siniestros_asegurado": 5,
                "dias_desde_inicio_poliza":       5,
                "dias_desde_fin_poliza":          60,
                "dias_entre_ocurrencia_reporte":  12,
            },
            {"en_lista_restrictiva": True, "pct_casos_observados": 0.0},
        )
        self.assertEqual(r["nivel_riesgo"], "ROJO",
                         f"Esperaba ROJO, obtuvo {r['nivel_riesgo']} (score={r['score_normalizado']})")
        self.assertGreaterEqual(r["score_normalizado"], 76)

    def test_score_normalizado_no_supera_100(self):
        r = motor(
            {"cobertura": "Robo Total", "estado": "Pérdida Total por Robo",
             "tiene_doc_inconsistente": 1, "documentos_completos": False,
             "historial_siniestros_asegurado": 10, "dias_desde_inicio_poliza": 1,
             "dias_entre_ocurrencia_reporte": 15, "similitud_narrativa": 0.95},
            {"en_lista_restrictiva": True, "pct_casos_observados": 0.9},
        )
        self.assertLessEqual(r["score_normalizado"], 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
