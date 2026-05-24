from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):

    UPLOAD_DIR = Path("uploads")
    ALLOWED_TYPES: List[str] = {
                "application/pdf",
                "text/plain"
            }

    
    class Config:
        env_file = ".env" # get paramters from the .env file


settings = Settings()
