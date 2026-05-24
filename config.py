
    
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
        UPLOAD_DIR: Path = Path("uploads")
        ALLOWED_TYPES: List[str] = [
                "application/pdf",
                "text/plain",
        ]

        class Config:
                env_file = ".env"  # get parameters from the .env file


settings = Settings()