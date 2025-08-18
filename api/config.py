from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    secret_key: str
    algorithm: str = "HS256"
    redis_url: str # ! pay attention to this one, in Dockerfile it's redis://redis:6379/0 
    jwt_refresh_token_expires_days: int = 30 
    jwt_access_token_expires_minutes: int = 30
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        from_attributes=True
    )

settings = Settings()
