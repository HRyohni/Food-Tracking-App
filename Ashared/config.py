import os


class Settings:
    """Shared configuration for every backend (custommer / worker / partner).

    All services read the SAME DATABASE_URL so they connect to one database.
    Override via environment variables in production."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/mydb"
    )
    # Comma-separated list of allowed frontend origins for CORS.
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")


settings = Settings()
