from pathlib import Path
import logging

# Configure logging globally
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class Settings:

    # Main upload folder
    UPLOAD_DIR = Path("uploads")


#  reusable settings object
settings = Settings()