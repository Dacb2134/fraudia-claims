import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Cargar las variables ocultas desde el archivo .env
load_dotenv()

# Leer la cadena de conexión de forma segura
DATABASE_URL = os.getenv("DB_URL")

if not DATABASE_URL:
    raise ValueError("⚠️ ERROR: No se encontró la variable DB_URL en el archivo .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
