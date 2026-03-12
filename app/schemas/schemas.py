# app/schemas/schemas.py
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.models import EstadoTransaccion, Servicio, TipoCuenta, TipoTransaccion


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegistroRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    telefono: str | None = None
    calle_numero: str | None = None
    colonia: str | None = None
    ciudad: str | None = None
    codigo_postal: str | None = None

    @field_validator("password")
    @classmethod
    def password_minimo(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class DesactivarCuentaRequest(BaseModel):
    email: EmailStr
    password: str
    confirmar_password: str

    @model_validator(mode="after")
    def passwords_coinciden(self) -> "DesactivarCuentaRequest":
        if self.confirmar_password != self.password:
            raise ValueError("La confirmación de contraseña no coincide")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirmar_password: str

    @model_validator(mode="after")
    def passwords_coinciden(self) -> "ResetPasswordRequest":
        if self.confirmar_password != self.password:
            raise ValueError("La confirmación de contraseña no coincide")
        if len(self.password) < 6:
            raise ValueError("La contraseña nueva debe tener al menos 6 caracteres")
        return self


# ─── Usuario ──────────────────────────────────────────────────────────────────

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: str | None = None
    calle_numero: str | None = None
    colonia: str | None = None
    ciudad: str | None = None
    codigo_postal: str | None = None
    activo: bool
    foto_perfil: str | None = None
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
    limite_gasto_mensual: float
    creada_en: datetime

    model_config = {"from_attributes": True}


class LimiteGastoSetRequest(BaseModel):
    limite: float
    tipo: TipoCuenta | None = None  # si es None, aplica a débito y crédito

    @field_validator("limite")
    @classmethod
    def limite_no_negativo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("El límite debe ser mayor o igual a 0")
        return v


class LimiteGastoInfoResponse(BaseModel):
    tipo: TipoCuenta
    limite_gasto_mensual: float
    gasto_mes_actual: float


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


# ─── Soporte (chat) ───────────────────────────────────────────────────────────

class SoporteChatRequest(BaseModel):
    session_id: str | None = None
    message: str

    @field_validator("message")
    @classmethod
    def mensaje_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El mensaje no puede estar vacío")
        return v


class SoporteChatResponse(BaseModel):
    session_id: str
    reply: str
    memory_messages: int
