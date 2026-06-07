from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


# BUG: class body uses double indentation
# standard Python uses 4 spaces only
# inconsistent indentation is hard to read
# fix all indentation to single level
class Settings(BaseSettings):
        UPLOAD_DIR: Path = Path("uploads")

        # BUG: ALLOWED_TYPES is a list
        # list lookup is O(n) on every check
        # use a set for O(1) lookup instead
        # change List[str] to Set[str]
        ALLOWED_TYPES: List[str] = [
                "application/pdf",
                "text/plain",
        ]

        class Config:
                env_file = ".env"


settings = Settings()
