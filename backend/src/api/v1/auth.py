"""
POST /api/v1/auth/login  — login simple, retorna usuario y rol
GET  /api/v1/auth/roles  — lista de roles disponibles
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from src.core.database import get_db

router = APIRouter()

ROLES_DISPONIBLES = {
    "admin":      "Ve todo el sistema",
    "analista":   "Solo ve casos asignados a el",
    "supervisor": "Ve reportes y estadisticas",
}

class LoginRequest(BaseModel):
    email:    str
    password: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login simple sin token. El frontend guarda el rol en estado local."""

    usuario = db.execute(
        text("SELECT id, nombre, email, password_plain, rol, activo FROM usuarios WHERE email = :email"),
        {"email": request.email}
    ).mappings().first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contrasena incorrectos")

    if usuario["password_plain"] != request.password:
        raise HTTPException(status_code=401, detail="Email o contrasena incorrectos")

    if not usuario["activo"]:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    return {
        "ok": True,
        "usuario": {
            "id":     usuario["id"],
            "nombre": usuario["nombre"],
            "email":  usuario["email"],
            "rol":    usuario["rol"],
        }
    }


@router.get("/roles")
def get_roles():
    """Lista de roles disponibles."""
    return {
        "roles": [
            {"rol": rol, "descripcion": desc}
            for rol, desc in ROLES_DISPONIBLES.items()
        ]
    }
