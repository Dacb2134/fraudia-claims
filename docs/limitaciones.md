# Limitaciones del Sistema FraudIA Claims

## Contexto
Este documento describe las limitaciones conocidas del prototipo, los casos donde el sistema puede fallar, y las condiciones bajo las cuales sus resultados no deben usarse como base de decisión sin revisión humana adicional.

---

## 1. Limitaciones del Modelo ML (XGBoost)

**Entrenamiento con datos sintéticos**
El modelo fue entrenado exclusivamente con el dataset sintético del HackIAthon 2026 (500 casos). No ha sido validado con datos reales de ninguna aseguradora. Su comportamiento con datos de producción real puede diferir significativamente.

**Etiqueta simulada, no auditada**
El campo `etiqueta_fraude_simulada` fue generado algorítmicamente, no por analistas humanos. El modelo aprende patrones sintéticos que pueden no reflejar el fraude real.

**Desbalance de clases**
El dataset tiene aproximadamente 4.2% de casos positivos (fraude simulado). El modelo puede presentar bajo recall en clases minoritarias con datos reales con distribuciones distintas.

**Métricas no generalizables**
Las métricas reportadas (Precisión: 100%, Recall: 83.3%, AUC-ROC: 98.8%) corresponden al conjunto de evaluación sintético. Estas cifras son orientativas y no representan rendimiento en producción.

---

## 2. Señales que pueden no disparar

**S-13 — Narrativas similares (TF-IDF)**
Requiere que el campo `similitud_narrativa` esté poblado en la base de datos. En instalaciones nuevas este campo es 0 para todos los casos hasta que se ejecute manualmente `POST /api/v1/nlp/similitud`. Sin este paso, la señal S-13 nunca activa.

**RF-01 — Pérdida Total por Robo**
Requiere que el campo `cobertura` contenga "robo" Y el campo `estado` contenga "pérdida total" simultáneamente. Si la aseguradora usa terminología diferente (ej. "Pérdida Completa" o "Siniestro Total"), esta regla no disparará.

**S-09 — Dinámica sospechosa**
Se basa en detección de palabras clave en el campo `descripcion` (ej. "volcadura", "sin testigo", "fuga"). Si las descripciones están vacías o usan terminología diferente, esta señal es inefectiva.

---

## 3. Falsos Positivos y Falsos Negativos

**Tasa estimada de falsos positivos: 15-20%**
Casos legítimos que el sistema marca como sospechosos. Causas principales:
- Asegurados con historial legítimamente alto (ej. flotas vehiculares)
- Siniestros cercanos al inicio de póliza por razones válidas (ej. renovación inmediata)
- Proveedores recurrentes en zonas con pocos talleres certificados

**Casos no detectables por el sistema:**
- Fraude sofisticado que no activa ninguna señal de las 13 implementadas
- Colusión entre asegurado y ajustador (no hay datos del ajustador)
- Fraude en ramos no modelados (ej. seguros de vida, agrícolas)
- Nuevos patrones de fraude no presentes en el dataset de entrenamiento

---

## 4. Dependencias Externas

**Agente IA — Google Gemini 2.0 Flash**
El agente explicativo depende de la API de Google Gemini. Si la API no está disponible, el agente no responde y las explicaciones automáticas del detalle de siniestro no se generan. El sistema de scoring continúa funcionando, pero sin la capa de explicación en lenguaje natural.

**Base de datos MySQL**
Si la conexión a MySQL falla, todos los endpoints del API retornan error 500. No existe modo offline ni caché de datos.

**Modelo ML en disco**
El archivo `fraud_model.pkl` se guarda en el sistema de archivos del servidor. Si el pod o contenedor se reinicia sin volumen persistente (caso común en Railway), el modelo se pierde y el scoring usa solo el 60% de reglas hasta que se ejecute el reentrenamiento desde la vista de Configuración.

---

## 5. Limitaciones de Cobertura

**Vehículos**
Los datos de placa, chasis, motor, marca, modelo y año están disponibles en la tabla `vehiculos`, pero la señal de "alta frecuencia de siniestros por vehículo" (señal 4 del documento del reto) no está implementada como señal independiente en el motor de reglas.

**Asegurados**
Los campos `mora_actual`, `score_cliente_simulado` y `numero_polizas` de la tabla `asegurados` no se usan en el cálculo del score de riesgo actual.

**Documentos**
La tabla `documentos` (con campos `tipo_documento`, `legible`, `inconsistencia_detectada`) existe en la BD pero no se consulta en el scoring. El motor usa únicamente los flags `documentos_completos` y `tiene_doc_inconsistente` de la tabla `siniestros`.

---

## 6. Limitaciones del Sistema como Producto

**El sistema no aprende en tiempo real**
El modelo ML no se actualiza automáticamente cuando llegan nuevos casos. Requiere reentrenamiento manual desde la vista de Configuración. No existe un pipeline de reentrenamiento automático.

**El scoring es determinístico**
Para los mismos datos de entrada, el score siempre es el mismo. No hay componente probabilístico ni actualización dinámica de pesos según patrones recientes.

**La auditoría es parcial**
Las acciones del analista (marcar caso para revisión, iniciar auditoría) se registran solo visualmente en la interfaz. No existe una tabla de auditoría en la base de datos que persista estas acciones.

**No hay integración con sistemas existentes**
El sistema no se conecta a sistemas core de aseguradoras (AS400, Oracle FS, etc.). La ingesta de datos requiere exportar CSV desde el sistema de origen y cargarlos manualmente.

---

## 7. Uso Correcto

✅ **Sí usar para:**
- Priorizar qué casos revisar primero
- Identificar señales de alerta para investigación humana
- Generar reportes de casos sospechosos para auditoría

❌ **No usar para:**
- Rechazar automáticamente siniestros
- Comunicar al asegurado que su caso fue marcado como fraude
- Tomar decisiones de pago sin revisión de un analista
- Evidencia legal o formal de fraude

---

## 8. Próximos Pasos para Producción

Para una implementación real con datos de producción se recomienda:
1. Reentrenar el modelo con datos históricos reales auditados por analistas
2. Validar umbrales del semáforo con el equipo antifraude de la aseguradora
3. Implementar tabla de auditoría para trazabilidad legal
4. Agregar autenticación JWT con expiración de sesión
5. Configurar alertas de monitoreo para detectar degradación del modelo
6. Evaluar con métricas sobre datos reales antes de usar en producción

---

*Este documento forma parte de los entregables del HackIAthon 2026 — Reto Aseguradora del Sur.*
*FraudIA Claims genera alertas de revisión, no acusaciones de fraude.*
