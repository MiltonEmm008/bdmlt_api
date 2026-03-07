# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.models import Cuenta, TipoCuenta, Usuario
from app.routers import auth, cuentas, operaciones


def _crear_usuario_default() -> None:
    """Crea (o actualiza) un usuario 'default' con saldo máximo en sus tarjetas."""
    db = SessionLocal()
    try:
        email_default = "default@banco.com"

        usuario_default = db.query(Usuario).filter(Usuario.email == email_default).first()
        if not usuario_default:
            usuario_default = Usuario(
                nombre="default",
                email=email_default,
                hashed_password=hash_password("CONTRA1234"),
            )
            db.add(usuario_default)
            db.flush()

        cuentas_por_tipo = {c.tipo: c for c in usuario_default.cuentas}

        # Valores máximos de ejemplo para pruebas
        saldo_maximo_debito = 1_000_000.0
        limite_credito_maximo = 5_000.0

        # Cuenta de débito
        cuenta_debito = cuentas_por_tipo.get(TipoCuenta.DEBITO)
        if not cuenta_debito:
            cuenta_debito = Cuenta(
                numero="4000" + "0" * 12,
                tipo=TipoCuenta.DEBITO,
                saldo=saldo_maximo_debito,
                usuario_id=usuario_default.id,
            )
            db.add(cuenta_debito)
        else:
            cuenta_debito.saldo = saldo_maximo_debito

        # Cuenta de crédito
        cuenta_credito = cuentas_por_tipo.get(TipoCuenta.CREDITO)
        if not cuenta_credito:
            cuenta_credito = Cuenta(
                numero="5000" + "0" * 12,
                tipo=TipoCuenta.CREDITO,
                saldo=0.0,
                deuda=0.0,
                limite_credito=limite_credito_maximo,
                usuario_id=usuario_default.id,
            )
            db.add(cuenta_credito)
        else:
            cuenta_credito.deuda = 0.0
            cuenta_credito.limite_credito = limite_credito_maximo

        db.commit()
    finally:
        db.close()


# Crea las tablas en la DB si no existen
Base.metadata.create_all(bind=engine)
_crear_usuario_default()

app = FastAPI(
    title="Banco Simulado API",
    description="API REST para la app bancaria escolar",
    version="1.0.0",
)

# CORS abierto para desarrollo local — ajustar en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router)
app.include_router(cuentas.router)
app.include_router(operaciones.router)


@app.get("/", tags=["Root"])
def root():
    return {"mensaje": "Banco Simulado API activa", "docs": "/docs"}
