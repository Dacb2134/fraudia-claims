# Uso de Inteligencia Artificial — FraudIA

## Enfoques de IA Implementados

El documento del hackathon solicita un enfoque híbrido. FraudIA implementa los 5 enfoques requeridos:

| Enfoque | Implementación | Archivo |
|---------|---------------|---------|
| Reglas de negocio | Motor determinista RF-01 a RF-07 | `src/engine/rules_evaluator.py` |
| Machine Learning supervisado | XGBoost con etiqueta simulada | `src/ml/fraud_model.py` |
| Detección de anomalías | Score híbrido fuera del rango esperado | `src/ml/fraud_model.py` |
| NLP — similitud textual | TF-IDF + Cosine Similarity | `src/api/v1/nlp_endpoints.py` |
| Agente conversacional | Gemini con contexto de BD | `src/api/v1/chat.py` |

---

## 1. Motor de Reglas Deterministas

### Qué hace
Evalúa cada siniestro contra 13 señales de fraude definidas en el documento. Cada señal tiene puntuación fija y transparente.

### Por qué este enfoque
Las reglas son auditables, explicables y no discriminan — cumplen el requisito ético del hackathon de que el modelo sea una "caja blanca", no una "caja negra".

### Reglas críticas implementadas
- **RF-01:** Pérdida Total por Robo → ROJO directo
- **RF-02:** Adulteración documental confirmada → ROJO directo
- **RF-03:** Proveedor en Lista Restrictiva → ROJO directo
- **RF-04:** Dinámica físicamente imposible → ROJO directo
- **RF-05:** Siniestro < 48 horas del borde de vigencia → AMARILLO
- **RF-06:** Demora > 4 días en denuncia de robo → AMARILLO
- **RF-07:** Narrativa idéntica clonada → AMARILLO

---

## 2. Modelo Machine Learning — XGBoost

### Qué hace
Predice la probabilidad de fraude (0 a 1) usando 16 features del siniestro.

### Features utilizadas
**Numéricas:**
- monto_reclamado
- monto_estimado
- dias_desde_inicio_poliza
- dias_desde_fin_poliza
- dias_entre_ocurrencia_reporte
- historial_siniestros_asegurado
- suma_asegurada
- score_riesgo (del motor de reglas)
- tiene_doc_inconsistente
- ratio_monto (monto_reclamado / suma_asegurada)
- es_borde_vigencia (binaria)
- reporte_tardio (binaria)

**Categóricas encodadas:**
- ramo, cobertura, estado, sucursal

### Métricas obtenidas
| Métrica | Valor | Interpretación |
|---------|-------|---------------|
| Precision | 1.000 | 0 falsos positivos — cuando dice fraude, acierta siempre |
| Recall | 0.833 | Detecta el 83.3% de todos los fraudes reales |
| F1-Score | 0.909 | Excelente balance entre precision y recall |
| AUC-ROC | 0.988 | Capacidad discriminativa casi perfecta (1.0 = máximo) |

### Score Híbrido
```
Score Final = (Score Reglas × 0.60) + (Probabilidad ML × 100 × 0.40)
```
Este diseño garantiza que las reglas de negocio tengan el mayor peso (60%), mientras el ML aporta una segunda opinión estadística (40%).

---

## 3. NLP — Análisis de Similitud de Narrativas

### Qué hace
Detecta siniestros con descripciones de reclamo casi idénticas, lo que puede indicar fraude coordinado o narrativas copiadas (regla RF-07).

### Algoritmo
1. Vectorización TF-IDF con n-gramas (1,2) — captura frases además de palabras
2. Cosine Similarity entre todos los pares de narrativas
3. Clasificación por umbral:
   - > 85% similitud → ROJO (narrativa clonada)
   - 70-85% → AMARILLO (sospechoso)
   - < 70% → normal

### Análisis de texto libre
El endpoint `/api/v1/nlp/analizar` detecta palabras clave de riesgo en cualquier texto:
- "sin testigos", "sin cámaras" → señal de ocultamiento
- "se dio a la fuga", "sin placas" → señal de tercero ficticio
- "pérdida total", "completamente destruido" → señal de exageración
- "madrugada", "accidente múltiple" → señal de dinámica sospechosa

---

## 4. Agente Conversacional — Gemini

### Qué hace
Responde preguntas en lenguaje natural sobre los siniestros usando datos reales de la base de datos como contexto.

### Arquitectura del agente
```
Pregunta del analista
        │
        ▼
Consultas SQL a MySQL (resumen, top casos, top proveedores)
        │
        ▼
Construcción del prompt con contexto real
        │
        ▼
Gemini API (model configurado en chat.py línea 13)
        │
        ▼
Respuesta en lenguaje natural
        │
        ▼
Log en tabla log_consultas_agente
```

### System Prompt — principios éticos
El agente tiene instrucciones explícitas de:
- Nunca acusar directamente — usar "presenta señales de riesgo"
- Recordar que el score es una alerta, no una acusación
- Basar respuestas solo en datos proporcionados
- Mantener la decisión final en el analista humano

### Preguntas que responde el agente
1. ¿Cuáles son los 10 siniestros con mayor riesgo?
2. ¿Por qué este siniestro fue marcado como alto riesgo?
3. ¿Qué proveedores concentran más alertas?
4. ¿Qué ramos tienen mayor porcentaje de casos sospechosos?
5. ¿Qué ciudades presentan mayor concentración de alertas?
6. ¿Qué patrones se repiten en los reclamos sospechosos?
7. Genera un resumen ejecutivo de los casos críticos.
8. Recomienda qué casos debería revisar primero el analista.

---

## 5. Cambiar el Modelo de IA

### Cambiar modelo Gemini
En `backend/src/api/v1/chat.py`, línea 13:
```python
GEMINI_MODEL = "gemini-2.0-flash-lite"   # ← cambiar aquí
```
Opciones disponibles: `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`

No requiere rebuild de Docker — uvicorn detecta el cambio automáticamente.

### Reentrenar el modelo ML
```bash
docker-compose exec api python -c "from src.ml.fraud_model import entrenar_modelo; entrenar_modelo()"
```

---

## Limitaciones Conocidas

1. **Dataset sintético** — el modelo está entrenado con 300 registros artificiales. En producción se necesitaría entrenamiento con datos reales históricos.
2. **Precision perfecta** — puede indicar sobreajuste por el tamaño pequeño del dataset. En producción se validaría con datos separados temporalmente.
3. **NLP sin embeddings semánticos** — TF-IDF detecta similitud léxica pero no semántica. Una mejora sería usar sentence-transformers.
4. **Gemini free tier** — tiene límites de requests por minuto. En producción se necesitaría un plan de pago.
