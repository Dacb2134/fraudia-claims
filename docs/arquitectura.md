# Arquitectura del Sistema — FraudIA

## Visión General

FraudIA es un sistema híbrido de detección de posibles fraudes en siniestros de seguros. Combina reglas de negocio deterministas, un modelo de Machine Learning y un agente conversacional con IA generativa.

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                               │
│              (Analista / Antifraude / Jefatura)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   FRONTEND                                   │
│              React 19 + Vite + TypeScript                    │
│                  http://localhost:5173                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────────┐
│                   BACKEND API                                │
│              FastAPI + Python 3.11                           │
│                  http://localhost:8000                        │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Motor Reglas│  │  Modelo ML   │  │   Agente Gemini   │  │
│  │  RF-01/RF-07│  │   XGBoost    │  │  google-genai     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Score Hibrido                          │    │
│  │         Reglas x60% + ML x40%                       │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy ORM
┌──────────────────────▼──────────────────────────────────────┐
│                   BASE DE DATOS                              │
│                  MySQL 8.0                                   │
│               puerto 3307 (externo)                          │
│                                                              │
│  siniestros · polizas · asegurados · proveedores             │
│  vehiculos · documentos · scores_riesgo · alertas            │
└─────────────────────────────────────────────────────────────┘
```

## Capas del Sistema

### 1. Capa de Presentación — Frontend
- **Tecnología:** React 19, Vite, TypeScript
- **Patrón:** Componentes funcionales con hooks
- **Comunicación:** fetch API hacia el backend REST

### 2. Capa de API — Backend
- **Tecnología:** FastAPI, Uvicorn
- **Patrón:** Router por dominio (siniestros, stats, chat, ml, nlp, red, reporte)
- **Validación:** Pydantic schemas
- **CORS:** Configurado para http://localhost:5173

### 3. Motor de Detección Híbrido

#### 3a. Motor de Reglas Deterministas
Evalúa 13 señales de fraude con puntuación fija según el documento del hackathon:

| Señal | Puntos máx |
|-------|-----------|
| Reclamo borde de vigencia | 8 |
| Demora denuncia robo | 8 |
| Alta frecuencia asegurado | 8 |
| Alta frecuencia conductor | 8 |
| Narrativas similares (NLP) | 8 |
| Proveedor recurrente | 10 |
| Documentos inconsistentes | 10 |
| Documentos incompletos | 4 |
| Reporte tardío | 5 |
| Dinámica sospechosa | 6 |
| Sin tercero identificado | 6 |
| Monto cercano suma asegurada | 5 |

#### 3b. Modelo Machine Learning — XGBoost
- **Algoritmo:** XGBoost Classifier
- **Features:** 16 variables (numéricas + categóricas encodadas)
- **Balance:** scale_pos_weight=4 para compensar desbalance 80/20
- **Métricas:** Precision 1.0 | Recall 0.833 | F1 0.909 | AUC-ROC 0.988

#### 3c. Score Híbrido Final
```
Score Final = (Score Reglas × 60%) + (Probabilidad ML × 100 × 40%)
```

#### 3d. Clasificación Semáforo
| Rango | Nivel | Acción |
|-------|-------|--------|
| 0 – 40 | VERDE | Flujo normal |
| 41 – 75 | AMARILLO | Revisión documental |
| 76 – 100 | ROJO | Revisión especializada |

### 4. Agente IA Conversacional
- **Modelo:** Gemini (Google Generative AI)
- **Contexto:** Datos reales de la BD en cada consulta
- **Prompts:** Sistema con reglas éticas — nunca acusa, siempre alerta
- **Log:** Cada consulta se registra en `log_consultas_agente`

### 5. NLP — Análisis de Narrativas
- **Algoritmo:** TF-IDF con n-gramas (1,2)
- **Similitud:** Cosine Similarity
- **Umbral ROJO:** > 85% similitud (regla RF-07)
- **Umbral AMARILLO:** 70-85%

### 6. Base de Datos
- **Motor:** MySQL 8.0
- **ORM:** SQLAlchemy 2.0
- **Tablas:** 10 tablas relacionales
- **Vista:** v_bandeja_casos para el dashboard

## Infraestructura — Docker

```
docker-compose.yml
├── db         → MySQL 8.0 (puerto 3307 externo / 3306 interno)
├── api        → FastAPI + Python (puerto 8000)
└── frontend   → React + Vite (puerto 5173)
```

La API espera activamente a que MySQL esté listo antes de arrancar (health check con reintentos cada 3s).

## Flujo de Datos

```
CSV sintético
     │
     ▼
poblar_bd.py ──► MySQL (300 siniestros + tablas relacionadas)
                      │
                      ▼
              Motor de Reglas ──► Score parcial
                      │
                      ▼
              Modelo XGBoost ──► Probabilidad ML
                      │
                      ▼
              Score Híbrido + Semáforo
                      │
              ┌───────┴───────┐
              ▼               ▼
        Dashboard        Agente IA
        (Frontend)       (Gemini)
```

## Patrones Arquitectónicos Aplicados

| Patrón | Dónde |
|--------|-------|
| Repository | `src/core/database.py` — acceso a BD |
| Strategy | `src/engine/rules_evaluator.py` — reglas intercambiables |
| Facade | `src/ml/fraud_model.py` — oculta complejidad ML |
| Adapter | `src/api/v1/chat.py` — adapta Gemini API |
| Router | `main.py` — separación por dominio |
