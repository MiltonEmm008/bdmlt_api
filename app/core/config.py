# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "clavesecretajawjdnajwdajwda8182477583u2njnaj"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./banco.db"

    class Config:
        env_file = ".env"


settings = Settings()
