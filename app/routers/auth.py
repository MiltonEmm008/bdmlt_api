# app/routers/auth.py
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import (
    DesactivarCuentaRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegistroRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerificarEmailRequest,
    MensajeResponse,
    UsuarioResponse,
)
from app.services.auth_service import (
    actualizar_perfil_usuario,
    desactivar_usuario,
    get_usuario_actual,
    login_usuario,
    registrar_usuario,
    resetear_password,
    solicitar_reset_password,
    verificar_email,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

BASE_DIR = Path(__file__).resolve().parent.parent  # app/
VIEWS_DIR = BASE_DIR / "views"


@router.post("/registro", response_model=MensajeResponse, status_code=201)
def registro(datos: RegistroRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario, lo deja desactivado y envía un correo de verificación."""
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


@router.post("/forgot-password")
def forgot_password(datos: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Inicia el flujo de recuperación de contraseña.

    Siempre responde de forma genérica para no revelar si el correo existe.
    """
    solicitar_reset_password(datos.email, db)
    return {
        "mensaje": "Si el correo existe en el sistema, enviaremos un enlace de recuperación."
    }


@router.get("/reset-password-form")
def reset_password_form():
    """
    Devuelve el HTML con el formulario para establecer una nueva contraseña.

    El token JWT llega como querystring: ?token=...
    """
    html_path = VIEWS_DIR / "reset_password.html"
    return FileResponse(html_path)


@router.post("/reset-password")
def reset_password(datos: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Actualiza la contraseña del usuario usando el token de recuperación.
    """
    return resetear_password(datos.token, datos.password, datos.confirmar_password, db)


@router.get("/verificar-email-form")
def verificar_email_form():
    """
    Devuelve el HTML que verifica automáticamente el correo del usuario usando el token.

    El token JWT llega como querystring: ?token=...
    """
    html_path = VIEWS_DIR / "verify_email.html"
    return FileResponse(html_path)


@router.post("/verificar-email", response_model=MensajeResponse)
def verificar_email_endpoint(datos: VerificarEmailRequest, db: Session = Depends(get_db)):
    """
    Verifica el correo del usuario a partir de un token JWT enviado por correo.
    """
    return verificar_email(datos.token, db)
