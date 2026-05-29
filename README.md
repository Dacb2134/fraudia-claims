# FraudIA Claims — Detector Inteligente de Posibles Fraudes en Siniestros

> **HackIAthon 2026 · Reto Aseguradora del Sur**
> Sistema híbrido de IA que detecta señales de riesgo en siniestros de seguros, asigna un score explicable y apoya la revisión humana — sin reemplazarla.

[![Live Demo](https://img.shields.io/badge/🚀_Demo_Live-Railway-6366f1?style=for-the-badge)](https://desirable-eagerness-production-3aea.up.railway.app)
[![Backend API](https://img.shields.io/badge/⚙️_API_Docs-Swagger-0ea5e9?style=for-the-badge)](https://fraudia-claims-production.up.railway.app/docs)

---

## El problema que resuelve

Los equipos antifraude de aseguradoras dependen de revisión manual, reglas dispersas y experiencia del analista. Cruzar variables de pólizas, asegurados, proveedores, documentos y fechas toma tiempo — y los patrones sospechosos pasan desapercibidos.

**FraudIA Claims** digitaliza ese proceso: analiza cada siniestro contra 13 señales de riesgo calibradas, aplica un modelo XGBoost entrenado con datos sintéticos, y genera un score explicable de 0–100. El sistema prioriza los casos para revisión pero **nunca acusa — solo alerta**.

---

## Cómo funciona (flujo del analista)

```
Siniestro ingresa
      │
      ▼
Motor de Reglas (13 señales)    ←── Borde vigencia, demora denuncia,
      │  60% del score                proveedor lista restrictiva,
      │                               doc. inconsistentes, etc.
      ▼
Modelo XGBoost                  ←── Entrenado con 500 siniestros
      │  40% del score                sintéticos + etiqueta fraude
      │
      ▼
Score Híbrido 0–100
      │
      ├── 🟢 0–40   VERDE    → Continuar flujo normal
      ├── 🟡 41–75  AMARILLO → Escalar a Unidad Antifraude (revisión doc.)
      └── 🔴 76–100 ROJO     → Revisión especializada de campo
            │
            ▼
      Analista revisa en el dashboard
      con explicación de cada alerta activada
      y puede consultar al Agente IA en lenguaje natural
```

---

## Stack tecnológico

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Frontend | React 19 + Vite + TypeScript | SPA rápida, tipada, escalable |
| Backend API | FastAPI (Python 3.11) | Async, autodocs Swagger, rápido |
| Base de datos | MySQL 8.0 | Relacional, JOIN eficientes entre tablas |
| Motor de reglas | Python (custom engine) | 13 señales del documento del hackathon |
| Modelo ML | XGBoost / RandomForest | Score supervisado con `etiqueta_fraude_simulada` |
| NLP | TF-IDF + cosine similarity | Detección de narrativas clonadas (RF-07) |
| Agente IA | Gemini 2.0 Flash Lite | Consultas en lenguaje natural sobre los datos reales |
| Infraestructura | Docker + Docker Compose | Entorno reproducible en cualquier máquina |
| Deploy | Railway (backend + frontend + MySQL) | CI/CD automático desde GitHub |

---

## Funcionalidades implementadas

### Mínimas (requisitos obligatorios del reto)
- ✅ Carga y procesamiento de 500 siniestros sintéticos con todas las tablas requeridas
- ✅ Cálculo de 13 variables de riesgo con puntaje ponderado
- ✅ Detección de alertas por reglas (RF-01 a RF-07, todas implementadas)
- ✅ Modelo ML (XGBoost) para score de posible fraude
- ✅ Semáforo VERDE / AMARILLO / ROJO con umbrales correctos (0-40 / 41-75 / 76-100)
- ✅ Dashboard con KPIs, distribución por ramo, top proveedores, top asegurados
- ✅ Explicación automática: cada alerta muestra cuál señal se activó y por qué

### Deseables (implementadas)
- ✅ Chat con el agente IA en lenguaje natural (Gemini 2.0)
- ✅ Análisis de texto del reclamo (TF-IDF + similitud coseno → detecta narrativas clonadas)
- ✅ Red de relaciones asegurados-proveedores-siniestros
- ✅ Ranking de proveedores con mayor concentración de alertas
- ✅ Exportación de reporte CSV para auditoría (casos ROJO, AMARILLO o todos)
- ✅ API REST funcional con Swagger autodocumentado
- ✅ Carga de archivos en el chat (PDF, TXT, imagen → Gemini multimodal)

### 12 preguntas que el agente puede responder
1. ✅ Los 10 siniestros con mayor riesgo de posible fraude
2. ✅ Por qué un siniestro fue marcado como alto riesgo (alertas activadas)
3. ✅ Qué proveedores concentran más alertas
4. ✅ Qué ramos tienen mayor porcentaje de casos sospechosos
5. ✅ Qué sucursales presentan mayor concentración de alertas
6. ✅ Qué asegurados tienen mayor frecuencia de reclamos
7. ✅ Qué documentos faltan en los casos críticos
8. ✅ Qué casos tienen montos atípicos (≥95% de la suma asegurada)
9. ✅ Qué siniestros ocurrieron cerca del inicio de la póliza
10. ✅ Qué patrones se repiten en los reclamos sospechosos
11. ✅ Resumen ejecutivo de casos críticos
12. ✅ Qué casos debería revisar primero el analista

---

## Roles y acceso por perfil

| Rol | Dashboard | Gestión de Casos | Reportes | Agente IA | Configuración |
|-----|-----------|-----------------|----------|-----------|---------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Analista** | ✅ | ✅ Solo sus casos | ❌ | ✅ | ❌ |
| **Supervisor** | ✅ | ❌ | ✅ | ✅ | ✅ |

**Cuentas de demo:**

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Admin | `admin@fraudia.com` | `admin123` |
| Analista | `analista@fraudia.com` | `analista123` |
| Supervisor | `supervisor@fraudia.com` | `supervisor123` |

---

## Señales de riesgo implementadas

| Código | Señal | Puntos máx |
|--------|-------|------------|
| S-01 | Siniestro ≤30 días del borde de vigencia | 8 pts |
| S-02 | Demora en denuncia de robo (>48h) | 8 pts |
| S-03 | Alta frecuencia de reclamos del asegurado (≥3) | 8 pts |
| S-04 | Frecuencia atípica de siniestros solo RC | 6 pts |
| S-07 | Proveedor en lista restrictiva | 10 pts |
| S-08 | Documentos obligatorios faltantes | 4 pts |
| S-09 | Dinámica del accidente físicamente cuestionable | 6 pts |
| S-10 | Daño severo sin tercero identificado | 5 pts |
| S-11 | Documentos inconsistentes / posible adulteración | 10 pts |
| S-12 | Reporte tardío del evento (>7 días) | 5 pts |
| S-13 | Narrativa clonada (>85% similitud TF-IDF) | 8 pts |
| S-14 | Monto reclamado ≥95% de la suma asegurada | 5 pts |
| RF-01 | Pérdida Total por Robo (crítica) | +20 pts |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (React)                   │
│  Login → Dashboard → Gestión → Detalle → Agente IA  │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP REST (JSON)
┌──────────────────▼──────────────────────────────────┐
│              BACKEND (FastAPI Python)                │
│  /api/v1/siniestros  /api/v1/stats  /api/v1/chat    │
│  /api/v1/ml          /api/v1/nlp    /api/v1/reporte │
│                                                      │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │  Motor Reglas   │  │   Modelo XGBoost/RF      │  │
│  │  (13 señales)   │  │   fraud_model.pkl        │  │
│  │  60% del score  │  │   40% del score          │  │
│  └────────┬────────┘  └──────────┬───────────────┘  │
│           └─────────┬────────────┘                  │
│                     ▼                               │
│            Score Híbrido 0-100                      │
│                     │                               │
│  ┌──────────────────▼──────────────────────────┐   │
│  │         Agente Gemini 2.0 Flash Lite        │   │
│  │   Responde 12 preguntas + archivo upload    │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │ SQLAlchemy ORM
┌──────────────────▼──────────────────────────────────┐
│                   MySQL 8.0                          │
│  siniestros · polizas · asegurados · proveedores    │
│  scores_riesgo · documentos · vehiculos · usuarios  │
└─────────────────────────────────────────────────────┘
```

---

## Instalación local

### Requisitos previos
- Git
- Docker Desktop (corriendo)

### Pasos

```bash
# 1. Clonar
git clone https://github.com/Dacb2134/fraudia-claims.git
cd fraudia-claims

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
# Edita backend/.env y agrega tu GEMINI_API_KEY

# 3. Levantar contenedores
docker-compose up --build

# 4. En otra terminal: poblar la base de datos
docker-compose exec api python poblar_bd.py

# 5. Acceder
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Variables de entorno requeridas (`backend/.env`)

```env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=reasonscore_db
DB_URL=mysql+pymysql://root:root@db:3306/reasonscore_db
GEMINI_API_KEY=tu_api_key_de_google_ai_studio
SECRET_KEY=fraudia2026hackiathon_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Endpoints principales

```http
GET  /api/v1/stats                         → KPIs del dashboard
GET  /api/v1/siniestros?nivel_riesgo=ROJO  → Lista filtrada por semáforo
GET  /api/v1/siniestros/{id}               → Detalle + score + alertas
POST /api/v1/siniestros/{id}/recalcular    → Score en tiempo real
POST /api/v1/chat                          → Consulta al agente IA
POST /api/v1/chat/archivo                  → Consulta con archivo adjunto
POST /api/v1/ml/entrenar                   → Entrenar modelo desde BD
GET  /api/v1/reporte/exportar              → Exportar CSV de casos
GET  /api/v1/red/relaciones                → Red de relaciones
```

---

## Estructura del repositorio

```
fraudia-claims/
├── backend/
│   ├── src/
│   │   ├── api/v1/         ← Endpoints REST
│   │   ├── engine/         ← Motor de reglas (rules_evaluator.py)
│   │   ├── ml/             ← Modelo XGBoost (fraud_model.py)
│   │   └── core/           ← Base de datos (database.py)
│   ├── main.py             ← Entry point FastAPI
│   ├── poblar_bd.py        ← Carga dataset sintético a MySQL
│   └── railway.json        ← Configuración Railway
├── frontend/
│   └── src/
│       ├── views/          ← Dashboard, Casos, Agente, Reportes
│       ├── components/     ← Sidebar (con roles)
│       └── services/       ← API calls, auth, chat
├── notebooks/
│   ├── 01_exploracion_datos.ipynb
│   ├── 02_modelo_fraude.ipynb
│   └── 03_evaluacion_modelo.ipynb
├── docs/
│   ├── arquitectura.md
│   ├── modelo_datos.md
│   ├── reglas_negocio.md
│   ├── uso_ia.md
│   └── ai_ethics.md
└── docker-compose.yml
```

---

## Arquitectura Futura (Escalabilidad)

Para una implementación en producción real, se propone la siguiente evolución de la arquitectura:

| Componente actual | Evolución a producción |
|---|---|
| Modelo `.pkl` en disco | Registro de modelos en **MLflow / S3** con versionado |
| Scoring síncrono en la API | Cola asíncrona con **Celery + Redis** para alta concurrencia |
| Autenticación por password | **JWT con expiración** + SSO corporativo |
| MySQL single instance | **MySQL con réplica** de lectura + caché Redis |
| Sin auditoría persistente | **Tabla de auditoría** para trazabilidad legal de cada decisión |
| Reentrenamiento manual | **Pipeline CI/CD** con reentrenamiento automático mensual |
| Gemini API directa | **Gateway de IA** con fallback a modelos alternativos |
| Deploy en Railway | **Kubernetes** con auto-scaling horizontal |

El diseño actual — con motor de reglas separado del API, ML como capa independiente, y agente IA desacoplado — facilita esta evolución sin reescribir la lógica de negocio.

---

## Principios éticos

- 🚫 El sistema **nunca acusa** de fraude — genera alertas de revisión
- 🚫 **No rechaza** automáticamente siniestros
- 👤 La decisión final **siempre es del analista humano**
- 🔒 Datos sintéticos — ningún dato personal real
- 📋 Cada score es **completamente trazable** (se muestra qué señal activó qué puntaje)
- ⚠️ El modelo documenta sus limitaciones y posibles falsos positivos

---

## Equipo — HackIAthon 2026

Reto: **Aseguradora del Sur** · Detector de Posibles Fraudes en Siniestros usando IA

> Este sistema genera alertas de revisión, no acusaciones de fraude. © 2026 VEXTA AI.
