# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# connect_args solo para SQLite; PostgreSQL/Supabase no lo necesita
_connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia de FastAPI para inyectar la sesión de DB en los endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
