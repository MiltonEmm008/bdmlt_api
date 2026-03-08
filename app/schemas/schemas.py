# app/schemas/schemas.py
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.models import EstadoTransaccion, Servicio, TipoCuenta, TipoTransaccion


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegistroRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_minimo(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Usuario ──────────────────────────────────────────────────────────────────

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    creado_en: datetime

    model_config = {"from_attributes": True}


# ─── Cuenta ───────────────────────────────────────────────────────────────────

class MiQRResponse(BaseModel):
    numero_cuenta: str
    nombre: str
    fecha: str  # Día/mes/año hora:minutos:segundos (24h), ej. "07/03/2025 14:30:45"


class CuentaResponse(BaseModel):
    id: int
    numero: str
    tipo: TipoCuenta
    saldo: float
    deuda: float
    limite_credito: float
    creada_en: datetime

    model_config = {"from_attributes": True}


# ─── Transacciones ────────────────────────────────────────────────────────────

class TransaccionResponse(BaseModel):
    id: int
    tipo: TipoTransaccion
    monto: float
    descripcion: str
    estado: EstadoTransaccion
    servicio: str | None
    referencia_servicio: str | None
    cuenta_origen_id: int | None
    cuenta_destino_id: int | None
    creada_en: datetime

    model_config = {"from_attributes": True}


class TransferenciaRequest(BaseModel):
    numero_cuenta_destino: str
    monto: float
    descripcion: str = ""

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class PagoServicioRequest(BaseModel):
    servicio: Servicio
    referencia: str          # número de contrato, teléfono, etc.
    monto: float
    usar_credito: bool = False

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class PagoCreditoRequest(BaseModel):
    monto: float

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v
