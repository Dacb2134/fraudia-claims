# Reglas de Negocio — FraudIA

## Sistema de Puntuación

Cada siniestro acumula puntos según las señales detectadas. El total se normaliza a escala 0-100.

### Señales y Puntuaciones

| Código | Señal | Puntuación máx | Criterio |
|--------|-------|---------------|---------|
| S-01 | Reclamo borde de vigencia | 8 pts | ≤10 días: 8pts / 11-30 días: 4pts |
| S-02 | Demora denuncia robo | 8 pts | >48h: 8pts / 24-48h: 4pts |
| S-03 | Alta frecuencia asegurado | 8 pts | ≥3 siniestros: 8pts / 2: 4pts |
| S-04 | Alta frecuencia vehículo | 6 pts | ≥3 siniestros: 6pts / 2: 3pts |
| S-05 | Alta frecuencia conductor | 8 pts | ≥3 siniestros: 8pts / 2: 4pts |
| S-06 | Proveedor recurrente | 10 pts | Lista restrictiva: 10pts / >30% casos: 5pts |
| S-07 | Documentos incompletos | 4 pts | Falta doc obligatorio: 4pts |
| S-08 | Dinámica sospechosa | 6 pts | Relato ilógico: 6pts / madrugada: 3pts |
| S-09 | Sin tercero identificado | 5 pts | Daño severo sin rastro: 5pts |
| S-10 | Documentos inconsistentes | 10 pts | Alteración confirmada: 10pts |
| S-11 | Reporte tardío | 5 pts | >7 días: 5pts / 4-7 días: 3pts |
| S-12 | Narrativas similares | 8 pts | >85%: 8pts / 70-84%: 4pts |
| S-13 | Monto cercano suma asegurada | 4 pts | >95% de cobertura: 4pts |

**Puntuación máxima teórica:** 85 puntos → normalizado a 100

---

## Reglas Críticas (clasificación directa)

| Código | Regla | Clasificación | Efecto |
|--------|-------|--------------|--------|
| RF-01 | Cobertura Pérdida Total por Robo (PTxRB) | **ROJO** | Score mínimo 76 |
| RF-02 | Evidencia de Adulteración Documental | **ROJO** | Score mínimo 76 |
| RF-03 | Coincidencia exacta con Lista Restrictiva | **ROJO** | Score mínimo 76 |
| RF-04 | Dinámica del Accidente Físicamente Imposible | **ROJO** | Score mínimo 76 |
| RF-05 | Siniestro extremo borde de vigencia (<48h) | **AMARILLO** | Alerta obligatoria |
| RF-06 | Demora atípica denuncia robo (>4 días) | **AMARILLO** | Alerta obligatoria |
| RF-07 | Narrativa Idéntica Clonada (>85%) | **AMARILLO** | Alerta obligatoria |

---

## Semáforo de Riesgo

| Rango | Nivel | Color | Acción recomendada |
|-------|-------|-------|--------------------|
| 0 – 40 | VERDE | 🟢 | Continuar flujo normal |
| 41 – 75 | AMARILLO | 🟡 | Escalar a Unidad Antifraude para revisión documental |
| 76 – 100 | ROJO | 🔴 | Escalar para revisión especializada de campo |

---

## Principio Fundamental

> El sistema genera **alertas de revisión**, nunca acusaciones automáticas de fraude.
> Toda decisión final debe ser tomada por un analista humano calificado.
