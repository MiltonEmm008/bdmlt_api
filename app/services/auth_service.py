# app/services/auth_service.py
import os
import random
import string
import uuid
from pathlib import Path

from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.models import Cuenta, TipoCuenta, Usuario
from app.schemas.schemas import LoginRequest, RegistroRequest

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

    token = create_access_token({"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}


def login_usuario(datos: LoginRequest, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verify_password(datos.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
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

    return usuario


def actualizar_perfil_usuario(
    usuario: Usuario,
    db: Session,
    *,
    nombre: str | None = None,
    password_actual: str | None = None,
    password_nueva: str | None = None,
    foto: UploadFile | None = None,
) -> Usuario:
    if nombre is not None and nombre.strip():
        usuario.nombre = nombre.strip()

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
