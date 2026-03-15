# main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.models import Cuenta, TipoCuenta, Usuario
from app.routers import auth, cuentas, operaciones, soporte


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


def _migraciones_sqlite() -> None:
    """Ajustes mínimos de esquema para SQLite sin usar Alembic."""
    with engine.begin() as conn:
        columnas_usuarios = {
            row[1] for row in conn.execute(text("PRAGMA table_info(usuarios)")).fetchall()
        }
        if "foto_perfil" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN foto_perfil VARCHAR(255)"))
        if "telefono" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20)"))
        if "calle_numero" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN calle_numero VARCHAR(255)"))
        if "colonia" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN colonia VARCHAR(255)"))
        if "ciudad" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN ciudad VARCHAR(100)"))
        if "codigo_postal" not in columnas_usuarios:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN codigo_postal VARCHAR(10)"))
        if "activo" not in columnas_usuarios:
            conn.execute(
                text("ALTER TABLE usuarios ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
            )

        columnas_cuentas = {
            row[1] for row in conn.execute(text("PRAGMA table_info(cuentas)")).fetchall()
        }
        if "limite_gasto_mensual" not in columnas_cuentas:
            conn.execute(
                text("ALTER TABLE cuentas ADD COLUMN limite_gasto_mensual FLOAT NOT NULL DEFAULT 0.0")
            )


# Crea las tablas en la DB si no existen
Base.metadata.create_all(bind=engine)
if "sqlite" in settings.DATABASE_URL:
    _migraciones_sqlite()
_crear_usuario_default()

app = FastAPI(
    title="Banco Simulado API",
    description="API REST para la app bancaria escolar",
    version="1.0.0",
)

# Archivos estáticos para fotos de perfil (rutas locales; con Supabase las fotos son URLs)
if Path("media").exists():
    app.mount("/media", StaticFiles(directory="media"), name="media")

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
app.include_router(soporte.router)


@app.get("/", tags=["Root"])
def root():
    return {"mensaje": "Banco Simulado API activa", "docs": "/docs"}
