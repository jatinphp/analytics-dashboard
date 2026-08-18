from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central app configuration. All values can be overridden with
    environment variables (see docker-compose.yml / .env).
    """

    database_url: str = (
        "postgresql+asyncpg://analytics:analytics@localhost:5432/analytics"
    )

    # Redis is OPTIONAL. If redis_url is empty, the app falls back to an
    # in-memory broadcaster -- fine for a single backend instance / local dev.
    # Set it to enable pub/sub fan-out across multiple backend instances.
    redis_url: str = ""

    # How often (seconds) the fake data generator emits a new event.
    fake_event_min_interval: float = 0.4
    fake_event_max_interval: float = 1.5

    # How often (seconds) the materialized view backing the trend charts
    # is refreshed.
    materialized_view_refresh_seconds: int = 15

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
