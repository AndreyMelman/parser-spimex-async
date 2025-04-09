from datetime import datetime

from pydantic import (
    BaseModel,
    PostgresDsn,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    max_overflow: int = 10
    pool_size: int = 50

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class Config(BaseModel):
    base_url: str = "https://spimex.com/markets/oil_products/trades/results/"
    download_dir: str = "downloads/"
    target_date: datetime = datetime(2023, 1, 1)
    concurrent_downloads: int = 200
    max_retries: int = 3
    concurrent_processing: int = 100


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        env_file_encoding="utf-8",
    )

    db: DatabaseConfig
    cf: Config = Config()


settings = Settings()
