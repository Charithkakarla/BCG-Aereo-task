import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CERTIFICATES_DIR = STORAGE_DIR / "certificates"
ZIPS_DIR = STORAGE_DIR / "zips"

# Create directories if they do not exist
STORAGE_DIR.mkdir(exist_ok=True)
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
ZIPS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration (Defaults to SQLite in storage folder)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{STORAGE_DIR}/certificates.db")
    
    # Storage paths
    CERTIFICATES_PATH: Path = CERTIFICATES_DIR
    ZIPS_PATH: Path = ZIPS_DIR

settings = Settings()
