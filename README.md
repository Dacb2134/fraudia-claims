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
| IA / Agente | Claude API (Anthropic) |
| Orquestación | Docker + Docker Compose |

---

## Requisitos previos

Solo necesitas tener instalado en tu máquina:

1. **Git**
2. **Docker Desktop** — debe estar **abierto y corriendo** antes de cualquier comando

No necesitas instalar Python, Node.js ni MySQL localmente.

---

## Primera vez — configuración inicial

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd fraudia-claims
```

### 2. Crear el archivo de variables de entorno

```bash
# Copiar la plantilla
cp backend/.env.example backend/.env
```

Abrir `backend/.env` y completar:

```env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=reasonscore_db
DB_URL=mysql+pymysql://root:root@db:3306/reasonscore_db
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXX   # ← pedir al líder del equipo
SECRET_KEY=cualquier_cadena_larga_random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> ⚠️ **Nunca subas el `.env` a GitHub.** Ya está en el `.gitignore`.

### 3. Construir y levantar los contenedores

```bash
docker-compose up --build
```

La primera vez tarda ~5 minutos descargando imágenes. Las siguientes veces es instantáneo.

Cuando veas esto en la terminal, todo está listo:

```
frontend-1  |   ➜  Local:   http://localhost:5173/
api-1       | 🚀 Arrancando FastAPI...
db-1        | ready for connections. port: 3306
```

### 4. Crear las tablas en la base de datos

**Abrir una segunda terminal** (dejar la primera con Docker corriendo) y ejecutar:

```bash
docker-compose exec db mysql -u root -proot reasonscore_db < db/schema.sql
```

Solo se hace **una vez**. Si el volumen de MySQL ya existe de antes, este paso no es necesario.

### 5. Cargar los datos sintéticos

```bash
docker-compose exec api python poblar_bd.py
```

Solo se hace **una vez** (o cada vez que quieras resetear los datos).

---

## Uso diario — arrancar el proyecto

```bash
# Levantar todo
docker-compose up

# Apagar todo
docker-compose down
```

> No uses `--build` en el uso diario, solo cuando cambies el `Dockerfile` o el `requirements.txt`.

---

## URLs de acceso

| Servicio | URL |
|----------|-----|
| 🎨 Frontend (Dashboard) | http://localhost:5173 |
| ⚙️ API REST | http://localhost:8000 |
| 📖 Swagger (docs interactivos) | http://localhost:8000/docs |
| 🗄️ MySQL Workbench | `localhost:3307` · user: `root` · pass: `root` |

> MySQL expone el puerto **3307** (no 3306) para evitar conflicto con MySQL local.

---

## Estructura del proyecto

```
fraudia-claims/
├── backend/                  # API FastAPI + Motor de reglas
│   ├── src/
│   │   ├── api/v1/           # Endpoints: siniestros, chat, stats
│   │   ├── core/             # Conexión BD, configuración
│   │   └── engine/           # Motor de reglas deterministas
│   ├── main.py               # Entry point de la API
│   ├── poblar_bd.py          # Carga el CSV a MySQL
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example          # Plantilla de variables (copiar a .env)
│
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   └── Dockerfile
│
├── ai_data_core/             # Datos, notebooks y agente IA
│   ├── agents/               # Orquestador, NLP, prompts
│   ├── data/synthetic/       # CSV con siniestros sintéticos
│   └── notebooks/            # Exploración y evaluación
│
├── db/
│   └── schema.sql            # DDL completo de MySQL
│
├── docs/                     # Documentación técnica
├── docker-compose.yml
└── .gitignore
```

---

## Comandos útiles

```bash
# Ver logs de un servicio específico
docker-compose logs api
docker-compose logs db
docker-compose logs frontend

# Entrar a la terminal del contenedor del backend
docker-compose exec api bash

# Entrar a MySQL desde la terminal
docker-compose exec db mysql -u root -proot reasonscore_db

# Resetear todo (borra datos de MySQL también)
docker-compose down -v
# Luego volver a hacer los pasos 3, 4 y 5

# Reconstruir solo el backend (cuando cambias requirements.txt)
docker-compose up --build api
```

---

## División del equipo

| Miembro | Responsabilidad |
|---------|----------------|
| **Miembro 1** | Dataset sintético · Motor de reglas · Modelo ML/NLP (`backend/src/engine/`, `ai_data_core/`) |
| **Miembro 2** | Dashboard frontend · Semáforo visual · Red de relaciones (`frontend/src/`) |
| **Miembro 3** | Agente Claude API · Explicabilidad del score · Documentación · Pitch (`backend/src/api/v1/chat.py`, `docs/`) |

---

## Solución de problemas frecuentes

**`exec /entrypoint.sh: no such file or directory`**  
El `entrypoint.sh` tiene saltos de línea Windows (CRLF). Verifica que el `Dockerfile` use `CMD` directo sin script externo.

**`ports are not available: 3306`**  
Tienes MySQL corriendo localmente. El `docker-compose.yml` ya mapea al puerto `3307` para evitarlo.

**`Can't initialize batch_readline`**  
La carpeta `db/` no existe o el path del `schema.sql` está mal. Crea la carpeta `db/` en la raíz y pon el `schema.sql` ahí.

**La API se reinicia en bucle**  
MySQL aún no terminó de arrancar. Espera 30 segundos y se estabiliza solo.

**`Table doesn't exist`**  
No corriste el paso 4. Ejecuta `docker-compose exec db mysql -u root -proot reasonscore_db < db/schema.sql`.
