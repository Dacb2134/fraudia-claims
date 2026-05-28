class ReglasNegocioEngine:
    def __init__(self, siniestro_data: dict, historial_asegurado: int):
        self.siniestro = siniestro_data
        self.historial_asegurado = historial_asegurado
        self.score_total = 0
        self.alertas = []

    def evaluar_rf01_robo_total(self):
        """RF-01: Cobertura Pérdida Total por Robo (Regla Crítica)"""
        cobertura = str(self.siniestro.get('cobertura', '')).lower()
        estado = str(self.siniestro.get('estado', '')).lower()
        
        if "robo" in cobertura and "pérdida total" in estado:
            self.score_total += 30
            self.alertas.append("RF-01: Reclamo crítico por Pérdida Total por Robo.")

    def evaluar_rf04_historial_sospechoso(self):
        """RF-04: Asegurado con múltiples siniestros en 12 meses"""
        if self.historial_asegurado >= 3:
            self.score_total += 25
            self.alertas.append(f"RF-04: Historial sospechoso ({self.historial_asegurado} siniestros previos).")
        elif self.historial_asegurado == 2:
            self.score_total += 15
            self.alertas.append("RF-04: Historial de riesgo medio (2 siniestros previos).")

    def ejecutar_motor(self):
        """Ejecuta todas las reglas y determina el semáforo"""
        self.evaluar_rf01_robo_total()
        self.evaluar_rf04_historial_sospechoso()
        
        # Clasificación Semáforo
        nivel = "Verde"
        if 41 <= self.score_total <= 75:
            nivel = "Amarillo"
        elif self.score_total >= 76:
            nivel = "Rojo"
            
        return {
            "score_riesgo": self.score_total,
            "nivel_riesgo": nivel,
            "alertas_activadas": " | ".join(self.alertas) if self.alertas else "Sin alertas"
        }
