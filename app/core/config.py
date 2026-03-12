# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "clavesecretajawjdnajwdajwda8182477583u2njnaj"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./banco.db"

    # ─── Soporte (Ollama vía OpenAI SDK) ──────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = "ollama"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    # Memoria en RAM (ventana deslizante) para el chat de soporte
    SOPORTE_MAX_MENSAJES_POR_CHAT: int = 20
    SOPORTE_MAX_CHATS_EN_RAM: int = 200
    SOPORTE_CHAT_TTL_SEGUNDOS: int = 60 * 30  # 30 min sin actividad -> se limpia

    class Config:
        env_file = ".env"


settings = Settings()
