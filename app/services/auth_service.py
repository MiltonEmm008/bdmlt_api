# app/services/auth_service.py
import os
import random
import smtplib
import ssl
import string
import uuid
from pathlib import Path

from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_email_verification_token,
    decode_access_token,
    decode_password_reset_token,
    decode_email_verification_token,
    hash_password,
    verify_password,
)
from app.models.models import Cuenta, TipoCuenta, Usuario
from app.schemas.schemas import DesactivarCuentaRequest, LoginRequest, RegistroRequest

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _generar_numero_cuenta(tipo: TipoCuenta) -> str:
    prefijo = "4000" if tipo == TipoCuenta.DEBITO else "5000"
    digitos = "".join(random.choices(string.digits, k=12))
    return prefijo + digitos


def registrar_usuario(datos: RegistroRequest, db: Session) -> dict:
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta con ese correo",
        )

    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        hashed_password=hash_password(datos.password),
        telefono=datos.telefono,
        calle_numero=datos.calle_numero,
        colonia=datos.colonia,
        ciudad=datos.ciudad,
        codigo_postal=datos.codigo_postal,
        activo=False,
    )
    db.add(usuario)
    db.flush()  # obtenemos el id sin hacer commit aún

    # Crear cuenta de débito y crédito automáticamente al registrarse
    debito = Cuenta(
        numero=_generar_numero_cuenta(TipoCuenta.DEBITO),
        tipo=TipoCuenta.DEBITO,
        saldo=1000.0,  # saldo inicial de prueba
        usuario_id=usuario.id,
    )
    credito = Cuenta(
        numero=_generar_numero_cuenta(TipoCuenta.CREDITO),
        tipo=TipoCuenta.CREDITO,
        saldo=0.0,
        deuda=0.0,
        limite_credito=5000.0,
        usuario_id=usuario.id,
    )
    db.add(debito)
    db.add(credito)
    db.commit()
    db.refresh(usuario)

    token_verificacion = create_email_verification_token(usuario.id)
    enlace_verificacion = (
        f"{settings.EMAIL_VERIFICATION_BASE_URL}/auth/verificar-email-form?token={token_verificacion}"
    )
    _enviar_correo_verificacion(usuario.email, enlace_verificacion)

    return {
        "mensaje": "Usuario registrado correctamente. Revisa tu correo para verificar tu cuenta."
    }


def login_usuario(datos: LoginRequest, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verify_password(datos.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada. No puedes iniciar sesión.",
        )

    token = create_access_token({"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}


def get_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada.",
        )

    return usuario


def desactivar_usuario(datos: DesactivarCuentaRequest, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if usuario.email == "default@banco.com":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta default no se puede desactivar",
        )

    if not verify_password(datos.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta ya se encuentra desactivada",
        )

    usuario.activo = False
    db.add(usuario)
    db.commit()

    return {"mensaje": "La cuenta se ha desactivado correctamente"}


def actualizar_perfil_usuario(
    usuario: Usuario,
    db: Session,
    *,
    nombre: str | None = None,
    telefono: str | None = None,
    calle_numero: str | None = None,
    colonia: str | None = None,
    ciudad: str | None = None,
    codigo_postal: str | None = None,
    password_actual: str | None = None,
    password_nueva: str | None = None,
    foto: UploadFile | None = None,
) -> Usuario:
    if nombre is not None and nombre.strip():
        usuario.nombre = nombre.strip()

    if telefono is not None:
        telefono = telefono.strip()
        usuario.telefono = telefono or None

    if calle_numero is not None:
        calle_numero = calle_numero.strip()
        usuario.calle_numero = calle_numero or None

    if colonia is not None:
        colonia = colonia.strip()
        usuario.colonia = colonia or None

    if ciudad is not None:
        ciudad = ciudad.strip()
        usuario.ciudad = ciudad or None

    if codigo_postal is not None:
        codigo_postal = codigo_postal.strip()
        usuario.codigo_postal = codigo_postal or None

    if password_nueva is not None:
        if password_actual is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes enviar password_actual para cambiar la contraseña",
            )
        if not verify_password(password_actual, usuario.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta",
            )
        if len(password_nueva) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña nueva debe tener al menos 6 caracteres",
            )
        usuario.hashed_password = hash_password(password_nueva)

    if foto is not None:
        # Guardar en media/perfiles/
        media_dir = Path("media") / "perfiles"
        media_dir.mkdir(parents=True, exist_ok=True)

        _, ext = os.path.splitext(foto.filename or "")
        ext = (ext or "").lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de imagen no soportado. Usa jpg, png o webp",
            )

        nombre_archivo = f"{uuid.uuid4().hex}{ext}"
        ruta_relativa = str(Path("media") / "perfiles" / nombre_archivo)
        ruta_destino = media_dir / nombre_archivo

        contenido = foto.file.read()
        if not contenido:
            raise HTTPException(status_code=400, detail="Archivo de foto vacío")
        if len(contenido) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La foto no puede exceder 5MB")

        ruta_destino.write_bytes(contenido)
        usuario.foto_perfil = ruta_relativa

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _enviar_correo_reset_password(destinatario: str, enlace: str) -> None:
    remitente = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    if not remitente or not password:
        return

    context = ssl.create_default_context()

    asunto = "Recuperación de contraseña - Banco BDMLT"
    cuerpo = (
        "Has solicitado restablecer tu contraseña en Banco BDMLT.\n\n"
        f"Por favor haz clic en el siguiente enlace (válido por {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutos):\n"
        f"{enlace}\n\n"
        "Si no solicitaste este cambio, puedes ignorar este correo.\n\n"
        "Atentamente,\n"
        "Soporte Banco BDMLT"
    )

    headers = [
        f"From: Soporte BDMLT <{remitente}>",
        f"To: {destinatario}",
        f"Subject: {asunto}",
        "Content-Type: text/plain; charset=utf-8",
    ]
    mensaje = "\r\n".join(headers) + "\r\n\r\n" + cuerpo

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(remitente, password)
            server.sendmail(remitente, [destinatario], mensaje.encode("utf-8"))
    except Exception:
        # No romper el flujo si falla el correo
        pass


def _enviar_correo_verificacion(destinatario: str, enlace: str) -> None:
    remitente = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    if not remitente or not password:
        return

    context = ssl.create_default_context()

    asunto = "Verificación de correo - Banco BDMLT"
    cuerpo = (
        "Gracias por registrarte en Banco BDMLT.\n\n"
        "Para activar tu cuenta, por favor haz clic en el siguiente enlace "
        f"(válido por {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES} minutos):\n"
        f"{enlace}\n\n"
        "Si no creaste esta cuenta, puedes ignorar este correo.\n\n"
        "Atentamente,\n"
        "Soporte Banco BDMLT"
    )

    headers = [
        f"From: Soporte BDMLT <{remitente}>",
        f"To: {destinatario}",
        f"Subject: {asunto}",
        "Content-Type: text/plain; charset=utf-8",
    ]
    mensaje = "\r\n".join(headers) + "\r\n\r\n" + cuerpo

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(remitente, password)
            server.sendmail(remitente, [destinatario], mensaje.encode("utf-8"))
    except Exception:
        # No romper el flujo si falla el correo
        pass


def solicitar_reset_password(email: str, db: Session) -> None:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not usuario.activo:
        # Respuesta silenciosa para no filtrar existencia de cuentas
        return

    token = create_password_reset_token(usuario.email)
    enlace = f"{settings.PASSWORD_RESET_BASE_URL}/auth/reset-password-form?token={token}"
    _enviar_correo_reset_password(usuario.email, enlace)


def resetear_password(token: str, nueva_password: str, confirmar_password: str, db: Session) -> dict:
    if nueva_password != confirmar_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La confirmación de contraseña no coincide",
        )
    if len(nueva_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña nueva debe tener al menos 6 caracteres",
        )

    email = decode_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enlace de recuperación inválido o expirado",
        )

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    usuario.hashed_password = hash_password(nueva_password)
    db.add(usuario)
    db.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}


def verificar_email(token: str, db: Session) -> dict:
    user_id = decode_email_verification_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enlace de verificación inválido o expirado",
        )

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if usuario.activo:
        return {"mensaje": "La cuenta ya se encuentra verificada."}

    usuario.activo = True
    db.add(usuario)
    db.commit()

    return {"mensaje": "Cuenta verificada correctamente. Ya puedes iniciar sesión."}
