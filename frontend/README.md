# FraudIA — Detector de Posibles Fraudes en Siniestros

Sistema híbrido de IA para detección de fraudes en siniestros de seguros.  
**hackIAthon 2026 · Reto Aseguradora del Sur**

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19 + Vite + TypeScript |
| Backend API | FastAPI (Python 3.11) |
| Base de datos | MySQL 8.0 |
| IA / Agente | Gemini API |
| Orquestación | Docker + Docker Compose |

---

## Requisitos previos

Solo necesitas tener instalado:

1. **Git**
2. **Docker Desktop** — debe estar **abierto y corriendo** antes de cualquier comando

No necesitas instalar Python, Node.js ni MySQL localmente.

---

## Primera vez — configuración inicial

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/Dacb2134/fraudia-claims.git
cd fraudia-claims
```

### Paso 2 — Crear el archivo de variables de entorno

En la carpeta `backend/` busca el archivo `.env.example`, cópialo y renómbralo a `.env`.

En VS Code: clic derecho sobre `.env.example` → Copy → pegar en la misma carpeta → renombrar a `.env`

El archivo debe quedar exactamente así — **no cambies nada excepto la API key**:

```env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=reasonscore_db
DB_URL=mysql+pymysql://root:root@db:3306/reasonscore_db
GEMINI_API_KEY=tu_api_key_aqui
SECRET_KEY=fraudia2026hackiathon_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> ⚠️ La `GEMINI_API_KEY` te la pasa Diego por WhatsApp. Nunca la subas a GitHub.

### Paso 3 — Levantar los contenedores

Abre una terminal en la raíz del proyecto y ejecuta:

```powershell
docker-compose up --build
```

La primera vez tarda ~5 minutos. Espera hasta ver **los tres mensajes** antes de continuar:

```
db-1   | ready for connections. port: 3306
api-1  | ✅ MySQL listo
api-1  | INFO: Application startup complete.
```

> ⚠️ No sigas al paso 4 hasta ver exactamente esos mensajes. Los errores de conexión que aparecen antes son normales — el API espera a que MySQL esté listo.

### Paso 4 — Crear las tablas (segunda terminal)

**Deja la Terminal 1 corriendo** y abre una **Terminal 2** nueva en la misma carpeta:

```powershell
# Copiar el schema al contenedor
docker cp db/schema.sql fraudia-claims-db-1:/schema.sql

# Crear las tablas
docker-compose exec db mysql -u root -proot reasonscore_db -e "source /schema.sql"

# Verificar que las tablas se crearon
docker-compose exec db mysql -u root -proot reasonscore_db -e "SHOW TABLES;"
```

Debes ver esto:
```
+---------------------------+
| Tables_in_reasonscore_db  |
+---------------------------+
| alertas                   |
| asegurados                |
| documentos                |
| log_consultas_agente      |
| polizas                   |
| proveedores               |
| scores_riesgo             |
| siniestros                |
| usuarios                  |
| vehiculos                 |
+---------------------------+
```

### Paso 5 — Cargar los datos sintéticos

```powershell
docker-compose exec api python poblar_bd.py
```

Debes ver:
```
✅ Base de datos poblada correctamente.
```

### Paso 6 — Verificar que todo funciona

Abre el navegador en estas URLs:

| URL | Qué deberías ver |
|-----|-----------------|
| http://localhost:5173 | Dashboard del frontend |
| http://localhost:8000/docs | Swagger con todos los endpoints |
| http://localhost:8000/api/v1/stats | JSON con estadísticas |

---

## Uso diario — arrancar el proyecto

```powershell
# Levantar (sin --build, es más rápido)
docker-compose up

# Apagar
docker-compose down
```

> Solo usa `--build` si cambiaste el `Dockerfile` o el `requirements.txt`.

> El paso 4 (schema) y el paso 5 (poblar) **solo se hacen una vez**. No los repitas a menos que hayas corrido `docker-compose down -v`.

---

## Si algo sale mal — resetear todo

```powershell
# Borra contenedores Y volumen de MySQL (datos se pierden)
docker-compose down -v

# Volver a levantar limpio
docker-compose up --build
```

Luego repetir los pasos 4 y 5.

---

## URLs de acceso

| Servicio | URL |
|----------|-----|
| 🎨 Frontend | http://localhost:5173 |
| ⚙️ API REST | http://localhost:8000 |
| 📖 Swagger docs | http://localhost:8000/docs |
| 🗄️ MySQL Workbench | `localhost:3307` · user: `root` · pass: `root` |

> MySQL usa el puerto **3307** externamente (no 3306) para no chocar con MySQL local.

---

## Endpoints disponibles

```
GET  /api/v1/stats                    → KPIs para el dashboard
GET  /api/v1/siniestros               → Lista priorizada por score
GET  /api/v1/siniestros?nivel_riesgo=ROJO  → Filtrar por semáforo
GET  /api/v1/siniestros?ramo=Vehículos     → Filtrar por ramo
GET  /api/v1/siniestros/{id}          → Detalle de un siniestro
POST /api/v1/chat                     → Agente IA (ver ejemplo abajo)
```

**Ejemplo chat:**
```json
POST /api/v1/chat
{
  "pregunta": "¿Cuáles son los 5 siniestros con mayor riesgo?",
  "contexto_siniestro": "SIN-00018"
}
```

---

## Estructura del proyecto

```
fraudia-claims/
├── backend/
│   ├── src/
│   │   ├── api/v1/
│   │   │   ├── siniestros.py   ← GET /siniestros
│   │   │   ├── stats.py        ← GET /stats
│   │   │   └── chat.py         ← POST /chat (agente IA)
│   │   ├── core/
│   │   │   └── database.py     ← conexión MySQL
│   │   └── engine/
│   │       └── rules_evaluator.py  ← motor de reglas
│   ├── main.py                 ← entry point FastAPI
│   ├── poblar_bd.py            ← carga CSV a MySQL
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example            ← copiar a .env
├── frontend/
│   ├── src/
│   └── Dockerfile
├── ai_data_core/
│   ├── agents/                 ← orquestador y NLP
│   └── data/synthetic/         ← CSVs con datos sintéticos
├── db/
│   └── schema.sql              ← DDL de todas las tablas
├── docs/
│   └── ai_ethics.md            ← ética y privacidad
└── docker-compose.yml
```

---

## Comandos útiles

```powershell
# Ver logs de un servicio
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f frontend

# Entrar al contenedor del backend
docker-compose exec api bash

# Entrar a MySQL
docker-compose exec db mysql -u root -proot reasonscore_db

# Reconstruir solo el backend
docker-compose up --build api
```

---

## Problemas frecuentes

**Error: `Can't connect to local MySQL server through socket`**
MySQL aún no terminó de arrancar. Espera a ver `ready for connections. port: 3306` en los logs y vuelve a intentar.

**Error: `Table doesn't exist`**
No corriste el paso 4. Ejecuta el `docker cp` y el `source /schema.sql`.

**Error: `Access denied for user root`**
El volumen tiene una contraseña vieja. Corre `docker-compose down -v` y vuelve a empezar desde el paso 3.

**Error: `ports are not available: 3306`**
Tienes MySQL local corriendo. El `docker-compose.yml` ya mapea al puerto `3307`, no debería pasar. Verifica que tu `docker-compose.yml` tenga `3307:3306`.

**El API se reinicia en bucle con errores de conexión**
Normal durante los primeros 20-30 segundos. Espera a ver `✅ MySQL listo`.

**No veo el `.env.example` en Windows**
Windows oculta archivos que empiezan con punto. Ábrelo desde VS Code donde sí aparece.

---

## División del equipo

| Miembro | Área | Archivos principales |
|---------|------|---------------------|
| Diego | Backend + IA | `backend/src/`, `ai_data_core/` |
| Miembro 2 | Frontend | `frontend/src/` |
| Miembro 3 | Agente + Docs + Pitch | `backend/src/api/v1/chat.py`, `docs/` |
