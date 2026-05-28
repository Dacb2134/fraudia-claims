import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("⚠️  No se encontró DB_URL en el archivo .env")

# pool_pre_ping=True reconecta automáticamente si MySQL reinició
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """Dependency para inyectar sesión en cada endpoint."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db(retries: int = 10, delay: float = 3.0):
    """Espera activa para que MySQL esté listo antes de arrancar la app."""
    import time
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Base de datos lista (intento {attempt})")
            return
        except Exception as e:
            print(f"⏳ BD no disponible aún (intento {attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("❌ No se pudo conectar a la base de datos después de varios intentos")
