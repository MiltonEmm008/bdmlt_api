# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "..."
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # PostgreSQL (Supabase) o SQLite según .env. Ejemplo Supabase:
    # postgresql+psycopg2://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres
    DATABASE_URL: str = "sqlite:///./banco.db"

    # ─── Supabase (DB + Storage para fotos) ────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # anon key para Storage/Auth
    SUPABASE_BUCKET_FOTOS: str = "..."

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
    EMAIL_OWNER: str = "..."

    # ─── Recuperación de contraseña ─────────────────────────────────────────────
    PASSWORD_RESET_EXPIRE_MINUTES: int = 5
    PASSWORD_RESET_BASE_URL: str = "http://localhost:8000"

    # ─── Verificación de correo ────────────────────────────────────────────────
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFICATION_BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def usa_supabase_storage(self) -> bool:
        """True si hay configuración de Supabase para subir fotos al bucket."""
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY)


settings = Settings()
