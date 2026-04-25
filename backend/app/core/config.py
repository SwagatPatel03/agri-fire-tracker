from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ── Database ──────────────────────────────────────────────
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5433"
    POSTGRES_HOST: str = "localhost"

    # ── External APIs ─────────────────────────────────────────
    NASA_FIRMS_API_KEY: str
    # Open-Meteo is free and keyless
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

    # ── Message Broker ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Admin ─────────────────────────────────────────────────
    ADMIN_API_KEY: str = "dev-admin-key-change-me"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()