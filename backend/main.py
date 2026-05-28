from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import siniestros, chat, stats

app = FastAPI(
    title="ReasonScore AI — Detector de Fraudes",
    description="Motor híbrido de detección de posibles fraudes en siniestros",
    version="1.0.0",
)

# ── CORS: permite que el frontend en :5173 llame al backend en :8000 ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(siniestros.router, prefix="/api/v1/siniestros", tags=["Siniestros"])
app.include_router(chat.router,       prefix="/api/v1/chat",       tags=["Agente IA"])
app.include_router(stats.router,      prefix="/api/v1/stats",      tags=["Estadísticas"])

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
