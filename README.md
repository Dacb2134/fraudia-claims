# ReasonScore AI - Detector Híbrido de Fraude en Siniestros

Detector inteligente de posibles fraudes en siniestros, utilizando un motor de reglas de negocio deterministas combinado con explicaciones generadas por Inteligencia Artificial (LLMs).

## 🛠 Arquitectura del Proyecto

* **Frontend:** React + Vite + TypeScript (Diseñado para alta velocidad de renderizado).
* **Backend:** FastAPI (Python 3.11) + Motor de Reglas Determinista.
* **Base de Datos:** MySQL 8.0 (Estructura relacional robusta).
* **Orquestación:** Docker y Docker Compose para desarrollo sincronizado.

---

## ⚠️ Requisitos Previos

No es necesario instalar Python, Node.js ni MySQL localmente. Solo se requiere:
1. **Git**
2. **Docker Desktop** (Asegurarse de que el programa esté abierto y el motor en ejecución).

---

## 🚀 Guía de Ejecución Local (Para el Equipo)

### Paso 1: Clonar el Repositorio
Abrir la terminal en el directorio de preferencia y ejecutar:

```bash
git clone URL_
cd fraudia-claims
```

### Paso 2: Configurar Credenciales (.env)
Por seguridad, las contraseñas de la base de datos y las API Keys no están en el control de versiones. Es obligatorio crear un archivo local:
1. Navegar a la carpeta `backend/`.
2. Duplicar el archivo llamado `.env.example` y renombrarlo exactamente a `.env`.
3. Asegurarse de que el contenido del nuevo archivo `.env` sea el siguiente:

```env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=reasonscore_db
DB_URL=mysql+pymysql://root:root@db:3306/reasonscore_db
OPENAI_API_KEY=tu_api_key_aqui
```

### Paso 3: Levantar la Arquitectura
Regresar a la raíz del proyecto (`fraudia-claims-workspace`) en la terminal y ejecutar:

```bash
docker-compose up --build
```
*(La primera vez tomará unos minutos mientras se descargan las imágenes de React, Python y MySQL. Los siguientes arranques serán instantáneos).*

### Paso 4: Accesos de la Aplicación
Una vez que la terminal indique que los contenedores están en ejecución, acceder a través del navegador:

* 🎨 **Frontend (UI / Dashboard):** http://localhost:5173
* ⚙️ **Backend API (Datos JSON):** http://localhost:8000/api/v1/siniestros
* 📖 **Documentación Swagger API:** http://localhost:8000/docs

**Para detener el entorno:**
Presionar `Ctrl + C` en la terminal donde se ejecuta Docker, o ejecutar `docker-compose down` en una nueva terminal dentro de la raíz del proyecto.

---

## 📂 Estructura Principal

```text
├── ai_data_core             # Datos sintéticos, notebooks de NLP y prompts para IA
│   ├── agents
│   ├── data
│   └── notebooks
├── backend                  # API en FastAPI, Motor de reglas y script de BD
│   ├── src
│   │   ├── api              # Endpoints (siniestros.py, chat.py)
│   │   ├── core             # Conexión a Base de Datos
│   │   └── engine           # Motor de reglas determinista
│   ├── main.py              # Entrada principal de la API
│   ├── poblar_bd.py         # Script para inyectar CSV a MySQL
│   └── requirements.txt
├── docs                     # Documentación técnica y reglas de negocio
├── frontend                 # Interfaz de usuario en React + Vite + TS
│   ├── public
│   ├── src                  # Componentes y estilos CSS
│   └── Dockerfile           # Configuración del contenedor Node
└── docker-compose.yml       # Orquestador principal de servicios
```
