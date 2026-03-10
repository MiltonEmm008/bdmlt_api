# app/services/cuenta_service.py
from datetime import datetime
from calendar import monthrange

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Cuenta, TipoCuenta, Transaccion, TipoTransaccion, Usuario
from app.schemas.schemas import LimiteGastoSetRequest, PagoCreditoRequest, PagoServicioRequest, TransferenciaRequest


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


def _rango_mes_actual() -> tuple[datetime, datetime]:
    ahora = datetime.now()
    inicio = datetime(ahora.year, ahora.month, 1, 0, 0, 0)
    ultimo_dia = monthrange(ahora.year, ahora.month)[1]
    fin = datetime(ahora.year, ahora.month, ultimo_dia, 23, 59, 59, 999999)
    return inicio, fin


def _gasto_mes_actual(cuenta_origen_id: int, db: Session) -> float:
    inicio, fin = _rango_mes_actual()
    transacciones = (
        db.query(Transaccion)
        .filter(
            Transaccion.cuenta_origen_id == cuenta_origen_id,
            Transaccion.creada_en >= inicio,
            Transaccion.creada_en <= fin,
            Transaccion.tipo.in_([TipoTransaccion.TRANSFERENCIA, TipoTransaccion.PAGO_SERVICIO]),
        )
        .all()
    )
    return float(sum(t.monto for t in transacciones))


def _validar_limite_gasto_y_advertencia(cuenta: Cuenta, db: Session, monto: float) -> str | None:
    limite = float(cuenta.limite_gasto_mensual or 0.0)
    if limite <= 0:
        return None

    gasto_mes = _gasto_mes_actual(cuenta.id, db)
    nuevo_total = gasto_mes + monto

    if nuevo_total > limite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Límite de gasto mensual alcanzado. No puedes realizar más movimientos este mes.",
        )

    if nuevo_total >= 0.9 * limite:
        return "Advertencia: has alcanzado el 90% de tu límite de gasto mensual."
    return None


def obtener_movimientos(
    usuario: Usuario,
    db: Session,
    limite: int = 20,
    orden_fecha: str = "desc",
    tipo: TipoTransaccion | None = None,
) -> list[Transaccion]:
    cuenta_ids = [c.id for c in usuario.cuentas]
    q = db.query(Transaccion).filter(
        (Transaccion.cuenta_origen_id.in_(cuenta_ids))
        | (Transaccion.cuenta_destino_id.in_(cuenta_ids))
    )
    if tipo is not None:
        q = q.filter(Transaccion.tipo == tipo)
    if orden_fecha == "asc":
        q = q.order_by(Transaccion.creada_en.asc())
    else:
        q = q.order_by(Transaccion.creada_en.desc())
    return q.limit(limite).all()


def realizar_transferencia(
    datos: TransferenciaRequest, usuario: Usuario, db: Session
) -> tuple[Transaccion, str | None]:
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

    # No permitir transferencias a usuarios desactivados
    if cuenta_destino.usuario and not cuenta_destino.usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes transferir a un usuario desactivado",
        )

    if cuenta_origen.id == cuenta_destino.id:
        raise HTTPException(status_code=400, detail="No puedes transferirte a ti mismo")

    advertencia = _validar_limite_gasto_y_advertencia(cuenta_origen, db, datos.monto)

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
    return transaccion, advertencia


def pagar_servicio(
    datos: PagoServicioRequest, usuario: Usuario, db: Session
) -> tuple[Transaccion, str | None]:
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

        advertencia = _validar_limite_gasto_y_advertencia(cuenta_credito, db, datos.monto)

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

        advertencia = _validar_limite_gasto_y_advertencia(cuenta_debito, db, datos.monto)

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
    return transaccion, advertencia


def establecer_limite_gasto(datos: LimiteGastoSetRequest, usuario: Usuario, db: Session) -> list[Cuenta]:
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == usuario.id).all()
    if not cuentas:
        raise HTTPException(status_code=404, detail="No tienes cuentas")

    tipos_objetivo = (
        [datos.tipo] if datos.tipo is not None else [TipoCuenta.DEBITO, TipoCuenta.CREDITO]
    )
    for c in cuentas:
        if c.tipo in tipos_objetivo:
            c.limite_gasto_mensual = float(datos.limite)
            db.add(c)
    db.commit()
    return cuentas


def obtener_limite_gasto(usuario: Usuario, db: Session) -> list[dict]:
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == usuario.id).all()
    if not cuentas:
        raise HTTPException(status_code=404, detail="No tienes cuentas")
    resp: list[dict] = []
    for c in cuentas:
        resp.append(
            {
                "tipo": c.tipo,
                "limite_gasto_mensual": float(c.limite_gasto_mensual or 0.0),
                "gasto_mes_actual": _gasto_mes_actual(c.id, db),
            }
        )
    return resp


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
