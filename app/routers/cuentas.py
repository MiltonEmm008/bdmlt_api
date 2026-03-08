# app/routers/cuentas.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario
from app.schemas.schemas import CuentaResponse, MiQRResponse, TransaccionResponse
from app.services.auth_service import get_usuario_actual
from app.services.cuenta_service import obtener_cuentas, obtener_mi_qr, obtener_movimientos

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


@router.get("/", response_model=list[CuentaResponse])
def mis_cuentas(usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    """Devuelve las cuentas (débito y crédito) del usuario autenticado."""
    return obtener_cuentas(usuario, db)


@router.get("/mi-qr", response_model=MiQRResponse)
def mi_qr(usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    """Devuelve el número de cuenta débito y nombre para generar el QR de transferencia."""
    return obtener_mi_qr(usuario, db)


@router.get("/movimientos", response_model=list[TransaccionResponse])
def mis_movimientos(
    limite: int = Query(default=20, ge=1, le=100),
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Devuelve el historial de movimientos del usuario autenticado."""
    return obtener_movimientos(usuario, db, limite)
