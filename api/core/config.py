from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    secret_key: str
    algorithm: str = "HS256"
    redis_port: int = 6379
    redis_host: str = "localhost"
    jwt_refresh_token_expires_days: int = 30 
    jwt_access_token_expires_minutes: int = 30
    debug: bool = False
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        from_attributes=True
    )

settings = Settings()
