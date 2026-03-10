# app/routers/auth.py
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import (
    DesactivarCuentaRequest,
    LoginRequest,
    RegistroRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.services.auth_service import (
    actualizar_perfil_usuario,
    desactivar_usuario,
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


@router.post("/desactivar")
def desactivar(datos: DesactivarCuentaRequest, db: Session = Depends(get_db)):
    """
    Desactiva la cuenta de un usuario.

    Requiere correo, contraseña y confirmación de contraseña.
    La cuenta default (`default@banco.com`) **no** se puede desactivar.
    Un usuario desactivado no puede iniciar sesión, realizar operaciones
    ni recibir transferencias a sus cuentas.
    """
    return desactivar_usuario(datos, db)


@router.get("/me", response_model=UsuarioResponse)
def perfil(usuario=Depends(get_usuario_actual)):
    """Devuelve la información del usuario autenticado."""
    return usuario


@router.patch("/me", response_model=UsuarioResponse)
def actualizar_perfil(
    nombre: str | None = Form(default=None),
    telefono: str | None = Form(default=None),
    calle_numero: str | None = Form(default=None),
    colonia: str | None = Form(default=None),
    ciudad: str | None = Form(default=None),
    codigo_postal: str | None = Form(default=None),
    password_actual: str | None = Form(default=None),
    password_nueva: str | None = Form(default=None),
    foto: UploadFile | None = File(default=None),
    usuario=Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Actualiza datos del usuario autenticado (nombre, teléfono, dirección, contraseña, foto de perfil)."""
    return actualizar_perfil_usuario(
        usuario,
        db,
        nombre=nombre,
        telefono=telefono,
        calle_numero=calle_numero,
        colonia=colonia,
        ciudad=ciudad,
        codigo_postal=codigo_postal,
        password_actual=password_actual,
        password_nueva=password_nueva,
        foto=foto,
    )
