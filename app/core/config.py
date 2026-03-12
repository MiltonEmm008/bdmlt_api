# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    EMAIL_USER: str = "..."
    EMAIL_PASSWORD: str = "..."
    EMAIL_OWNER: str = "merp2067@gmail.com"

    # ─── Recuperación de contraseña ─────────────────────────────────────────────
    PASSWORD_RESET_EXPIRE_MINUTES: int = 5
    PASSWORD_RESET_BASE_URL: str = "http://localhost:8000"

    # ─── Verificación de correo ────────────────────────────────────────────────
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFICATION_BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
