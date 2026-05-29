"""
Motor de reglas de negocio para detección de posibles fraudes.
Implementa las 13 señales y 7 reglas críticas del documento HackIAthon 2026.

Score máximo referencial: ~90 pts (normalizado 0-100).
Semáforo: VERDE 0-40 | AMARILLO 41-75 | ROJO 76-100
"""


class ReglasNegocioEngine:
    """
    Evalúa un siniestro contra todas las señales de riesgo del hackathon.
    Retorna score normalizado, nivel semáforo, alertas y reglas críticas.
    """

    SCORE_MAX_REFERENCIA = 90

    def __init__(self, siniestro: dict, proveedor: dict | None = None):
        self.s    = siniestro
        self.prov = proveedor or {}
        self.score_bruto   = 0
        self.alertas:        list[str] = []
        self.reglas_criticas: list[str] = []

    # ── Señales ───────────────────────────────────────────────────────────────

    def s01_borde_vigencia(self):
        """S-01: Siniestro cerca del inicio o fin de vigencia (≤30 días)."""
        dias_inicio = abs(self.s.get("dias_desde_inicio_poliza") or 999)
        dias_fin    = abs(self.s.get("dias_desde_fin_poliza")    or 999)
        dias_min    = min(dias_inicio, dias_fin)
        if dias_min <= 10:
            self.score_bruto += 8
            self.alertas.append(f"S-01: Siniestro a {dias_min} día(s) del borde de vigencia (≤10 días, riesgo máximo).")
            if dias_min <= 2:
                self.reglas_criticas.append("RF-05")
        elif dias_min <= 30:
            self.score_bruto += 4
            self.alertas.append(f"S-01: Siniestro a {dias_min} días del borde de vigencia (11-30 días).")

    def s02_demora_denuncia_robo(self):
        """S-02: Demora atípica en denuncia de robo (>48 h)."""
        cobertura = str(self.s.get("cobertura", "")).lower()
        if "robo" not in cobertura:
            return
        dias   = self.s.get("dias_entre_ocurrencia_reporte") or 0
        horas  = dias * 24
        if horas > 96:
            self.score_bruto += 8
            self.alertas.append(f"S-02: Denuncia de robo tardía ({dias} días después del evento, >4 días).")
            self.reglas_criticas.append("RF-06")
        elif horas > 48:
            self.score_bruto += 4
            self.alertas.append(f"S-02: Denuncia de robo con demora ({dias} días, 24-48 h).")

    def s03_frecuencia_asegurado(self):
        """S-03: Alta frecuencia de reclamos del asegurado en 12 meses."""
        hist = self.s.get("historial_siniestros_asegurado") or 0
        if hist >= 3:
            self.score_bruto += 8
            self.alertas.append(f"S-03: Asegurado con {hist} siniestros previos (≥3, alto riesgo).")
        elif hist == 2:
            self.score_bruto += 4
            self.alertas.append(f"S-03: Asegurado con {hist} siniestros previos.")

    def s04_frecuencia_rc(self):
        """S-04/S-06: Frecuencia atípica de siniestros solo de Responsabilidad Civil."""
        cobertura = str(self.s.get("cobertura", "")).lower()
        if "responsabilidad" not in cobertura and " rc" not in cobertura:
            return
        hist = self.s.get("historial_siniestros_asegurado") or 0
        if hist > 2:
            self.score_bruto += 6
            self.alertas.append(f"S-04: Frecuencia atípica de siniestros solo RC ({hist} previos).")
        elif hist == 1:
            self.score_bruto += 3
            self.alertas.append("S-04: Antecedente de siniestro RC previo.")

    def s07_proveedor_restrictivo(self):
        """S-07: Proveedor en lista restrictiva o alta concentración de alertas."""
        en_lista = self.prov.get("en_lista_restrictiva") or False
        pct      = float(self.prov.get("pct_casos_observados") or 0)
        if en_lista:
            self.score_bruto += 10
            self.alertas.append("S-07: Proveedor/beneficiario en LISTA RESTRICTIVA.")
            self.reglas_criticas.append("RF-03")
        elif pct >= 0.40:
            self.score_bruto += 5
            self.alertas.append(f"S-07: Proveedor con {pct*100:.0f}% de casos observados (concentración alta).")

    def s08_documentos_incompletos(self):
        """S-08: Documentación obligatoria faltante."""
        completos = self.s.get("documentos_completos")
        if completos is False or completos == 0:
            self.score_bruto += 4
            self.alertas.append("S-08: Documentación incompleta — faltan documentos legales obligatorios.")

    def s09_dinamica_sospechosa(self):
        """S-09: Dinámica del accidente sospechosa o físicamente cuestionable."""
        desc = str(self.s.get("descripcion") or "").lower()
        alta  = ["volcadura", "múltiple", "imposible", "sin testigo", "sin cámara", "físicamente"]
        media = ["madrugada", "sin tercero", "huye", "fuga", "se dio a la fuga"]
        if any(k in desc for k in alta):
            self.score_bruto += 6
            self.alertas.append("S-09: Dinámica del accidente con inconsistencias físicas (relato ilógico o accidente múltiple).")
            self.reglas_criticas.append("RF-04")
        elif any(k in desc for k in media):
            self.score_bruto += 3
            self.alertas.append("S-09: Dinámica con factores de riesgo (madrugada, sin tercero identificado).")

    def s10_sin_tercero(self):
        """S-10: Daño severo sin rastro del tercero involucrado."""
        desc   = str(self.s.get("descripcion") or "").lower()
        monto  = float(self.s.get("monto_reclamado") or 0)
        kws    = ["sin tercero", "tercero huye", "no identificado", "se dio a la fuga"]
        if monto > 5000 and any(k in desc for k in kws):
            self.score_bruto += 5
            self.alertas.append(f"S-10: Daño severo (${monto:,.0f}) sin tercero identificado ni evidencia.")

    def s11_documentos_inconsistentes(self):
        """S-11: Documentos con inconsistencias o posible adulteración."""
        if self.s.get("tiene_doc_inconsistente") in (True, 1):
            self.score_bruto += 10
            self.alertas.append("S-11: DOCUMENTOS INCONSISTENTES — fechas no coinciden, valores alterados o ilegibles.")
            self.reglas_criticas.append("RF-02")

    def s12_reporte_tardio(self):
        """S-12: El siniestro se reportó muchos días después del evento."""
        dias = self.s.get("dias_entre_ocurrencia_reporte") or 0
        if dias > 7:
            self.score_bruto += 5
            self.alertas.append(f"S-12: Reporte tardío — {dias} días entre ocurrencia y notificación (>7 días).")
        elif 4 <= dias <= 7:
            self.score_bruto += 3
            self.alertas.append(f"S-12: Reporte con demora — {dias} días entre ocurrencia y notificación.")

    def s13_narrativa_similar(self):
        """S-13: Narrativa del reclamo similar a otros casos (posible clonación)."""
        similitud = float(self.s.get("similitud_narrativa") or 0)
        if similitud >= 0.85:
            self.score_bruto += 8
            self.alertas.append(f"S-13: NARRATIVA CLONADA — {similitud*100:.0f}% de similitud textual con otro reclamo.")
            self.reglas_criticas.append("RF-07")
        elif similitud >= 0.70:
            self.score_bruto += 4
            self.alertas.append(f"S-13: Narrativa muy similar a otro reclamo ({similitud*100:.0f}% similitud).")

    def s14_monto_suma_asegurada(self):
        """S-14: Monto reclamado muy cercano o superior a la suma asegurada."""
        monto  = float(self.s.get("monto_reclamado") or 0)
        suma   = float(self.s.get("suma_asegurada")  or 1)
        if suma <= 0:
            return
        ratio = monto / suma
        if ratio >= 0.95:
            self.score_bruto += 5
            self.alertas.append(f"S-14: Monto reclamado es el {ratio*100:.0f}% de la suma asegurada (≥95%).")
        elif ratio >= 0.50:
            self.score_bruto += 2
            self.alertas.append(f"S-14: Monto reclamado representa el {ratio*100:.0f}% de la suma asegurada.")

    def rf01_robo_total(self):
        """RF-01 CRÍTICA: Pérdida Total por Robo."""
        cobertura = str(self.s.get("cobertura", "")).lower()
        estado    = str(self.s.get("estado", "")).lower()
        if "robo" in cobertura and ("pérdida total" in estado or "perdida total" in estado):
            self.score_bruto += 20
            self.alertas.append("RF-01 ⚠️ CRÍTICA: Cobertura Pérdida Total por Robo — revisión especializada obligatoria.")
            self.reglas_criticas.append("RF-01")

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar_motor(self) -> dict:
        """Ejecuta todas las señales y reglas. Retorna resultado completo."""
        self.s01_borde_vigencia()
        self.s02_demora_denuncia_robo()
        self.s03_frecuencia_asegurado()
        self.s04_frecuencia_rc()
        self.s07_proveedor_restrictivo()
        self.s08_documentos_incompletos()
        self.s09_dinamica_sospechosa()
        self.s10_sin_tercero()
        self.s11_documentos_inconsistentes()
        self.s12_reporte_tardio()
        self.s13_narrativa_similar()
        self.s14_monto_suma_asegurada()
        self.rf01_robo_total()

        score_norm = min(100, round((self.score_bruto / self.SCORE_MAX_REFERENCIA) * 100))

        if score_norm >= 76:
            nivel = "ROJO"
        elif score_norm >= 41:
            nivel = "AMARILLO"
        else:
            nivel = "VERDE"

        return {
            "score_normalizado":  score_norm,
            "score_bruto":        self.score_bruto,
            "nivel_riesgo":       nivel,
            "alertas_activadas":  " | ".join(self.alertas) if self.alertas else "Sin alertas detectadas",
            "reglas_criticas":    list(set(self.reglas_criticas)),
            "total_alertas":      len(self.alertas),
        }
