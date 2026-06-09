from pydantic_settings import BaseSettings
from typing import Set
from pathlib import Path


class Settings(BaseSettings):
    UPLOAD_DIR: Path = Path("uploads")

    ALLOWED_TYPES: Set[str] = {
                "application/pdf",
                "text/plain",
        }
class Config:
                env_file = ".env"

settings = Settings()
