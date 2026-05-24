from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):

    UPLOAD_DIR = Path("uploads")

    
    class Config:
        env_file = ".env" # get paramters from the .env file


settings = Settings()
