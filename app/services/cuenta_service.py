# app/services/cuenta_service.py
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Cuenta, TipoCuenta, Transaccion, TipoTransaccion, Usuario
from app.schemas.schemas import PagoCreditoRequest, PagoServicioRequest, TransferenciaRequest


def obtener_cuentas(usuario: Usuario, db: Session) -> list[Cuenta]:
    return db.query(Cuenta).filter(Cuenta.usuario_id == usuario.id).all()


def obtener_mi_qr(usuario: Usuario, db: Session) -> dict:
    cuenta_debito = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.DEBITO)
        .first()
    )
    if not cuenta_debito:
        raise HTTPException(status_code=404, detail="No tienes cuenta de débito")
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return {"numero_cuenta": cuenta_debito.numero, "nombre": usuario.nombre, "fecha": fecha}


def obtener_movimientos(usuario: Usuario, db: Session, limite: int = 20) -> list[Transaccion]:
    cuenta_ids = [c.id for c in usuario.cuentas]
    return (
        db.query(Transaccion)
        .filter(
            (Transaccion.cuenta_origen_id.in_(cuenta_ids))
            | (Transaccion.cuenta_destino_id.in_(cuenta_ids))
        )
        .order_by(Transaccion.creada_en.desc())
        .limit(limite)
        .all()
    )


def realizar_transferencia(datos: TransferenciaRequest, usuario: Usuario, db: Session) -> Transaccion:
    # Cuenta débito del usuario como origen
    cuenta_origen = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.DEBITO)
        .first()
    )
    if not cuenta_origen:
        raise HTTPException(status_code=404, detail="No tienes cuenta de débito")

    if cuenta_origen.saldo < datos.monto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente",
        )

    cuenta_destino = db.query(Cuenta).filter(Cuenta.numero == datos.numero_cuenta_destino).first()
    if not cuenta_destino:
        raise HTTPException(status_code=404, detail="Cuenta destino no encontrada")

    if cuenta_origen.id == cuenta_destino.id:
        raise HTTPException(status_code=400, detail="No puedes transferirte a ti mismo")

    cuenta_origen.saldo -= datos.monto
    cuenta_destino.saldo += datos.monto

    transaccion = Transaccion(
        tipo=TipoTransaccion.TRANSFERENCIA,
        monto=datos.monto,
        descripcion=datos.descripcion or f"Transferencia a {cuenta_destino.numero}",
        cuenta_origen_id=cuenta_origen.id,
        cuenta_destino_id=cuenta_destino.id,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


def pagar_servicio(datos: PagoServicioRequest, usuario: Usuario, db: Session) -> Transaccion:
    cuenta_debito = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.DEBITO)
        .first()
    )
    cuenta_credito = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.CREDITO)
        .first()
    )

    if datos.usar_credito:
        if not cuenta_credito:
            raise HTTPException(status_code=404, detail="No tienes cuenta de crédito")

        disponible = cuenta_credito.limite_credito - cuenta_credito.deuda
        if datos.monto > disponible:
            raise HTTPException(
                status_code=400,
                detail="Límite de crédito insuficiente",
            )

        cuenta_credito.deuda += datos.monto

        transaccion = Transaccion(
            tipo=TipoTransaccion.PAGO_SERVICIO,
            monto=datos.monto,
            descripcion=f"Pago {datos.servicio.value} - Ref: {datos.referencia}",
            servicio=datos.servicio.value,
            referencia_servicio=datos.referencia,
            cuenta_origen_id=cuenta_credito.id,
        )
    else:
        if not cuenta_debito:
            raise HTTPException(status_code=404, detail="No tienes cuenta de débito")

        if cuenta_debito.saldo < datos.monto:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")

        cuenta_debito.saldo -= datos.monto

        transaccion = Transaccion(
            tipo=TipoTransaccion.PAGO_SERVICIO,
            monto=datos.monto,
            descripcion=f"Pago {datos.servicio.value} - Ref: {datos.referencia}",
            servicio=datos.servicio.value,
            referencia_servicio=datos.referencia,
            cuenta_origen_id=cuenta_debito.id,
        )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


def pagar_credito(datos: PagoCreditoRequest, usuario: Usuario, db: Session) -> Transaccion:
    cuenta_debito = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.DEBITO)
        .first()
    )
    cuenta_credito = (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == usuario.id, Cuenta.tipo == TipoCuenta.CREDITO)
        .first()
    )

    if not cuenta_debito or not cuenta_credito:
        raise HTTPException(status_code=404, detail="Cuentas no encontradas")

    if cuenta_debito.saldo < datos.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente en cuenta de débito")

    # No se puede pagar más de lo que se debe
    monto_real = min(datos.monto, cuenta_credito.deuda)
    if monto_real <= 0:
        raise HTTPException(status_code=400, detail="No tienes deuda en tu tarjeta de crédito")

    cuenta_debito.saldo -= monto_real
    cuenta_credito.deuda -= monto_real

    transaccion = Transaccion(
        tipo=TipoTransaccion.PAGO_CREDITO,
        monto=monto_real,
        descripcion="Pago de tarjeta de crédito",
        cuenta_origen_id=cuenta_debito.id,
        cuenta_destino_id=cuenta_credito.id,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion
