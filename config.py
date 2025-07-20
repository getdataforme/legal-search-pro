import os
from typing import Optional


class Settings:
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb://appuser:FrthgnjunD43xeWi8@34.174.230.159:27017/courts-database?authSource=courts-database"
    )
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "courts-database")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "allcourts")

    # API Configuration
    API_TITLE: str = "Legal Cases Search API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "FastAPI backend for managing and searching legal case documents"

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()
