"""
Configuración central de la aplicación usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Configuración global de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/mercado_automotor",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")

    # BCRA API
    bcra_api_base_url: str = Field(
        default="https://api.bcra.gob.ar",
        alias="BCRA_API_BASE_URL"
    )
    bcra_timeout: int = Field(default=30, alias="BCRA_TIMEOUT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", alias="LOG_FILE")

    # Analytics
    forecasting_periods: int = Field(default=12, alias="FORECASTING_PERIODS")
    min_data_points: int = Field(default=24, alias="MIN_DATA_POINTS")
    confidence_interval: float = Field(default=0.95, alias="CONFIDENCE_INTERVAL")

    # API (FastAPI)
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # Data paths
    data_raw_path: Path = Field(default=Path("./data/raw"), alias="DATA_RAW_PATH")
    data_processed_path: Path = Field(default=Path("./data/processed"), alias="DATA_PROCESSED_PATH")
    data_models_path: Path = Field(default=Path("./data/models"), alias="DATA_MODELS_PATH")

    # Streamlit
    streamlit_server_port: int = Field(default=8501, alias="STREAMLIT_SERVER_PORT")
    streamlit_server_address: str = Field(default="localhost", alias="STREAMLIT_SERVER_ADDRESS")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    def get_database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return str(self.database_url)

    def get_database_url_async(self) -> str:
        """Get asynchronous database URL."""
        return str(self.database_url).replace("postgresql://", "postgresql+asyncpg://")


# Singleton instance
settings = Settings()
