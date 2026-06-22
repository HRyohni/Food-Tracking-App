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

    # JWT auth. All services share ONE secret so a token's signature is valid
    # everywhere; each service additionally checks the token's "type" claim so a
    # customer token can't be used on the worker/partner API. Override
    # JWT_SECRET_KEY via environment in production — never ship this default.
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "dev-insecure-change-me-in-production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()
