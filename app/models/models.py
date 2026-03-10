# app/models/models.py
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class TipoCuenta(str, PyEnum):
    DEBITO = "debito"
    CREDITO = "credito"


class EstadoTransaccion(str, PyEnum):
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    PENDIENTE = "pendiente"


class TipoTransaccion(str, PyEnum):
    TRANSFERENCIA = "transferencia"
    PAGO_SERVICIO = "pago_servicio"
    PAGO_CREDITO = "pago_credito"
    DEPOSITO = "deposito"


class Servicio(str, PyEnum):
    CFE = "CFE"
    INFINITUM = "Infinitum"
    TELCEL = "Telcel"
    AGUA = "Agua"
    GAS = "Gas"


# ─── Tablas ───────────────────────────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    foto_perfil: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    calle_numero: Mapped[str | None] = mapped_column(String(255), nullable=True)
    colonia: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    cuentas: Mapped[list["Cuenta"]] = relationship("Cuenta", back_populates="usuario")


class Cuenta(Base):
    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    tipo: Mapped[TipoCuenta] = mapped_column(Enum(TipoCuenta))
    saldo: Mapped[float] = mapped_column(Float, default=0.0)
    limite_gasto_mensual: Mapped[float] = mapped_column(Float, default=0.0)
    # Solo aplica para crédito: deuda actual y límite
    deuda: Mapped[float] = mapped_column(Float, default=0.0)
    limite_credito: Mapped[float] = mapped_column(Float, default=0.0)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="cuentas")
    transacciones_origen: Mapped[list["Transaccion"]] = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_origen_id", back_populates="cuenta_origen"
    )
    transacciones_destino: Mapped[list["Transaccion"]] = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_destino_id", back_populates="cuenta_destino"
    )


class Transaccion(Base):
    __tablename__ = "transacciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo: Mapped[TipoTransaccion] = mapped_column(Enum(TipoTransaccion))
    monto: Mapped[float] = mapped_column(Float)
    descripcion: Mapped[str] = mapped_column(String(255), default="")
    estado: Mapped[EstadoTransaccion] = mapped_column(
        Enum(EstadoTransaccion), default=EstadoTransaccion.COMPLETADA
    )
    servicio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referencia_servicio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cuenta_origen_id: Mapped[int | None] = mapped_column(ForeignKey("cuentas.id"), nullable=True)
    cuenta_destino_id: Mapped[int | None] = mapped_column(ForeignKey("cuentas.id"), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    cuenta_origen: Mapped["Cuenta | None"] = relationship(
        "Cuenta", foreign_keys=[cuenta_origen_id], back_populates="transacciones_origen"
    )
    cuenta_destino: Mapped["Cuenta | None"] = relationship(
        "Cuenta", foreign_keys=[cuenta_destino_id], back_populates="transacciones_destino"
    )
