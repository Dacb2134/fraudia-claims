# Ética, Privacidad y Limitaciones del Sistema

## Principio fundamental

**Este sistema genera alertas de revisión. No acusa, no rechaza siniestros ni toma decisiones automáticas.**

Toda alerta generada debe ser revisada por un analista humano calificado antes de tomar cualquier acción sobre un siniestro.

---

## Privacidad y datos

### Datos utilizados
- El sistema fue desarrollado y evaluado **exclusivamente con datos sintéticos** generados algorítmicamente mediante `ai_data_core/src/ingestion/generate_dataset.py`.
- No se utilizó ningún dato real de asegurados, pólizas ni siniestros de Aseguradora del Sur ni de ninguna otra entidad.
- Ningún registro contiene información personal identificable (PII): nombres, cédulas, direcciones, teléfonos ni correos electrónicos.

### Identificadores anonimizados
Todos los identificadores son códigos internos sin valor fuera del sistema:

| Campo | Formato | Ejemplo |
|-------|---------|---------|
| Asegurado | `ASE-XXXX` | `ASE-0042` |
| Póliza | `POL-XXXXX` | `POL-00134` |
| Siniestro | `SIN-XXXXX` | `SIN-00087` |
| Proveedor | `PROV-XXX` | `PROV-026` |

### Fuentes de datos
| Dataset | Origen | Descripción |
|---------|--------|-------------|
| `siniestros.csv` | Generación sintética | 300 siniestros con patrones de fraude simulados al 20% |
| `polizas.csv` | Generación sintética | 160 pólizas con fechas y montos aleatorios |
| `asegurados.csv` | Generación sintética | 120 asegurados con historial simulado |
| `proveedores.csv` | Generación sintética | 30 proveedores, 4 en lista restrictiva simulada |
| `documentos.csv` | Generación sintética | 1184 documentos con inconsistencias simuladas |

---

## Seguridad del sistema

- Las credenciales de base de datos y API keys se almacenan en variables de entorno (`.env`) que **nunca se suben al repositorio** (incluidas en `.gitignore`).
- El repositorio no contiene ninguna clave, contraseña ni token en el código fuente.
- Las comunicaciones entre servicios ocurren dentro de la red Docker privada.

---

## Limitaciones del modelo

### Falsos positivos
El sistema **sobreestima el riesgo** en ciertos casos legítimos:

- Siniestros ocurridos al inicio de pólizas nuevas (es normal que alguien use su seguro recién contratado).
- Proveedores con alto volumen de reclamos que son legítimamente populares.
- Narrativas similares que coinciden porque describen accidentes comunes (choques en intersección, por ejemplo).
- Retrasos en el reporte por causas ajenas al asegurado (hospitalización, zona sin señal).

**Tasa estimada de falsos positivos en datos sintéticos: ~15-20%** — esto es aceptable para un sistema de priorización, pero inaceptable para tomar decisiones automáticas.

### Falsos negativos
El sistema **puede no detectar** fraudes sofisticados que:

- No activan ninguna regla de las RF-01 a RF-07.
- Usan proveedores nuevos aún no observados.
- Presentan documentos falsificados de alta calidad.
- Operan en redes de asegurados sin historial previo.

### Sesgos conocidos
- El modelo fue entrenado con datos sintéticos que pueden no reflejar la distribución real de fraudes en Ecuador.
- Las reglas de negocio están calibradas con umbrales sugeridos en el documento del reto, no con datos históricos reales.
- Ciudades con menor volumen de siniestros pueden tener scores menos confiables.

---

## Uso correcto del sistema

### Lo que SÍ debe hacer un analista con las alertas
- Usar el score como criterio de **priorización** de la cola de revisión.
- Investigar los factores específicos que generaron cada alerta.
- Tomar la decisión final basándose en evidencia documental y criterio profesional.
- Registrar el resultado de su revisión para retroalimentar el modelo.

### Lo que NO debe hacer
- Rechazar automáticamente un siniestro por tener score ROJO.
- Comunicar al asegurado que "el sistema detectó fraude".
- Usar el score como única evidencia en un proceso legal o administrativo.
- Omitir la revisión humana en casos de alto riesgo.

---

## Marco ético

El sistema sigue los principios de **IA explicable y responsable**:

| Principio | Implementación |
|-----------|---------------|
| Transparencia | Cada score incluye la lista de alertas activadas y los puntos asignados |
| Explicabilidad | El agente IA puede responder en lenguaje natural por qué un caso es sospechoso |
| Proporcionalidad | El sistema prioriza, no decide |
| Revisión humana | El flujo siempre termina en un analista, nunca en una acción automática |
| No discriminación | Las variables usadas son comportamentales, no demográficas |

---

## Declaración de alcance

> Este prototipo fue desarrollado para el **hackIAthon 2026 — Reto Aseguradora del Sur** con fines exclusivamente demostrativos. No está listo para producción sin validación con datos reales, auditoría de sesgo, y aprobación de los equipos de riesgo y compliance de la aseguradora.
