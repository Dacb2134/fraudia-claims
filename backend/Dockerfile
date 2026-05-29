FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "\
  echo '⏳ Esperando MySQL...' && \
  n=0; until python -c \"import os; from sqlalchemy import create_engine, text; e = create_engine(os.getenv('DB_URL'), connect_args={'connect_timeout': 3}); e.connect().execute(text('SELECT 1')); print('✅ MySQL listo')\" 2>/dev/null; do \
    n=$((n+1)); if [ $n -ge 20 ]; then echo '❌ MySQL no responde, arrancando igual...'; break; fi; \
    echo \"  Reintentando en 3s... ($n/20)\"; sleep 3; \
  done && \
  echo '🚀 Arrancando FastAPI...' && \
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]