# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Clave y JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./banco.db"

    # ─── Soporte (Gemini) ────────────────────────────────────────────────────
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Memoria en RAM (ventana deslizante) para el chat de soporte
    SOPORTE_MAX_MENSAJES_POR_CHAT: int = 20
    SOPORTE_MAX_CHATS_EN_RAM: int = 200
    SOPORTE_CHAT_TTL_SEGUNDOS: int = 60 * 30  # 30 min sin actividad -> se limpia

    class Config:
        env_file = ".env"


settings = Settings()
