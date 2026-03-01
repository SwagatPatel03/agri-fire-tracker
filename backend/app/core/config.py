from pydantic_settings import BaseSettings # To create a settings class

class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str="5432"
    POSTGRES_HOST: str="localhost"

    # External API Settings
    NASA_FIRMS_API_KEY : str
    OPEN_WEATHER_MAP_API_KEY : str

    # Message Broker
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()