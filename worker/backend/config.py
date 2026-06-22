import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from Ashared.config import settings as shared_settings  # noqa: E402


class Settings:
    DATABASE_URL = shared_settings.DATABASE_URL
    CORS_ORIGINS = shared_settings.CORS_ORIGINS
    APP_TITLE = "Worker API"


settings = Settings()
