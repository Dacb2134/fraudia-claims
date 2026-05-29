import os
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import siniestros, chat, stats, ml_endpoints, nlp_endpoints, extra_endpoints, auth, admin_endpoints

app = FastAPI(
    title="ReasonScore AI — Detector de Fraudes",
    description="Motor híbrido de detección de posibles fraudes en siniestros",
    version="1.0.0",
)

_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw.split(",")] if _raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,                    prefix="/api/v1/auth",       tags=["Autenticación"])
app.include_router(siniestros.router,              prefix="/api/v1/siniestros", tags=["Siniestros"])
app.include_router(chat.router,                    prefix="/api/v1/chat",       tags=["Agente IA"])
app.include_router(stats.router,                   prefix="/api/v1/stats",      tags=["Estadísticas"])
app.include_router(ml_endpoints.router,            prefix="/api/v1/ml",         tags=["Modelo ML"])
app.include_router(nlp_endpoints.router,           prefix="/api/v1/nlp",        tags=["NLP"])
app.include_router(extra_endpoints.router_red,      prefix="/api/v1/red",        tags=["Red de Relaciones"])
app.include_router(extra_endpoints.router_reporte,  prefix="/api/v1/reporte",    tags=["Reportes"])
app.include_router(admin_endpoints.router_admin,    prefix="/api/v1/admin",      tags=["Admin Demo"])

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
