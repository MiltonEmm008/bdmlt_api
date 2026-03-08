# app/routers/operaciones.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Servicio, Usuario
from app.schemas.schemas import (
    PagoCreditoRequest,
    PagoServicioRequest,
    TransaccionResponse,
    TransferenciaRequest,
)
from app.services.auth_service import get_usuario_actual
from app.services.cuenta_service import pagar_credito, pagar_servicio, realizar_transferencia

router = APIRouter(prefix="/operaciones", tags=["Operaciones"])


@router.post("/transferencia", response_model=TransaccionResponse, status_code=201)
def transferencia(
    datos: TransferenciaRequest,
    response: Response,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Realiza una transferencia desde la cuenta débito del usuario a otra cuenta."""
    transaccion, advertencia = realizar_transferencia(datos, usuario, db)
    if advertencia:
        response.headers["X-Gasto-Advertencia"] = advertencia
    return transaccion


@router.post("/pago-servicio", response_model=TransaccionResponse, status_code=201)
def pago_servicio(
    datos: PagoServicioRequest,
    response: Response,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Paga un servicio (CFE, Infinitum, Telcel, Agua, Gas) desde la cuenta débito."""
    transaccion, advertencia = pagar_servicio(datos, usuario, db)
    if advertencia:
        response.headers["X-Gasto-Advertencia"] = advertencia
    return transaccion


@router.post("/pago-credito", response_model=TransaccionResponse, status_code=201)
def pago_credito(
    datos: PagoCreditoRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Paga la deuda de la tarjeta de crédito usando el saldo de la cuenta débito."""
    return pagar_credito(datos, usuario, db)


@router.get("/servicios-disponibles")
def servicios_disponibles():
    """Lista los servicios disponibles para pago."""
    return [{"servicio": s.value} for s in Servicio]
