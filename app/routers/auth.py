# app/routers/auth.py
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import LoginRequest, RegistroRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import (
    actualizar_perfil_usuario,
    get_usuario_actual,
    login_usuario,
    registrar_usuario,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/registro", response_model=TokenResponse, status_code=201)
def registro(datos: RegistroRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y devuelve un token de acceso."""
    return registrar_usuario(datos, db)


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    """Inicia sesión y devuelve un token de acceso."""
    return login_usuario(datos, db)


@router.get("/me", response_model=UsuarioResponse)
def perfil(usuario=Depends(get_usuario_actual)):
    """Devuelve la información del usuario autenticado."""
    return usuario


@router.patch("/me", response_model=UsuarioResponse)
def actualizar_perfil(
    nombre: str | None = Form(default=None),
    password_actual: str | None = Form(default=None),
    password_nueva: str | None = Form(default=None),
    foto: UploadFile | None = File(default=None),
    usuario=Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Actualiza datos del usuario autenticado (nombre, contraseña, foto de perfil)."""
    return actualizar_perfil_usuario(
        usuario,
        db,
        nombre=nombre,
        password_actual=password_actual,
        password_nueva=password_nueva,
        foto=foto,
    )
