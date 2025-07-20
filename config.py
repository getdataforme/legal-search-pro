import os
from typing import Optional

class Settings:
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "legal_cases_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "cases")
    
    # API Configuration
    API_TITLE: str = "Legal Cases Search API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "FastAPI backend for managing and searching legal case documents"
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

settings = Settings()
