from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict
from pydantic import Field
from functools import lru_cache
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ Choose env file dynamically:
# - In Docker: set ENV_FILE=.env.docker (in compose) OR set IN_DOCKER=1
ENV_FILE = os.getenv("ENV_FILE", ".env")
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ENV_FILE)


class Settings(BaseSettings):
    db_port: int | None = Field(None, env="DB_PORT")
    db_host: str | None = Field(None, env="DB_HOST")
    db_name: str | None = Field(None, env="DB_NAME")
    db_user: str | None = Field(None, env="DB_USER")
    db_password: str | None = Field(None, env="DB_PASSWORD")

    REDIS_URL: str | None = Field(None, env="REDIS_URL")
    REDIS_HMAC_SECRET: str | None = Field(None, env="REDIS_HMAC_SECRET")

    # CELERY SETTINGS 
    CELERY_BROKER_URL: str | None = Field(None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str | None = Field(None, env="CELERY_RESULT_BACKEND")

    CELERY_TIMEZONE: str = Field("UTC", env="CELERY_TIMEZONE")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def validate_required(self):
        required_fields = [
            self.db_host,
            self.db_port,
            self.db_name,
            self.db_user,
            self.db_password,
            self.REDIS_URL,
            self.REDIS_HMAC_SECRET,
            self.CELERY_BROKER_URL,
            self.CELERY_RESULT_BACKEND,
        ]

        if any(v is None for v in required_fields):
            raise ValueError(
                "Missing required environment variables for runtime"
            )
        
    model_config = ConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
