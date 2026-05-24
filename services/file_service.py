import aiofiles
from pathlib import Path
from fastapi import HTTPException, UploadFile
import logging
import uuid
from config import settings

logger = logging.getLogger(__name__)

class FileService:

    def __init__(self):
        # settings.UPLOAD_DIR comes as a string from pydantic-settings, convert to Path
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    # FIX FOR ERROR 2: Adding the missing file type validation method
    def check_file_type(self, content_type: str) -> bool:
        allowed_types = {"application/pdf", "text/plain", "image/png", "image/jpeg"}
        return content_type in allowed_types

    def check_validity(self, file: UploadFile | None) -> tuple[bool, str]:
        # FIX FOR ERROR 1 & 3: Check if the file object itself exists first
        if not file:
            return False, "No file uploaded"
            
        if not file.filename:
            return False, "Filename is missing"

        if not self.check_file_type(file.content_type):
            return False, "Unsupported file type"

        return True, ""

    def generate_unique_filename(self, original_name: str) -> str:
        return f"{uuid.uuid4()}_{original_name}"

    async def save_upload(self, file: UploadFile, target_path: Path) -> tuple[bool, str]:
        try:
            async with aiofiles.open(target_path, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    await out.write(chunk)
            return True, "File saved successfully"
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return False, f"Save failed: {str(e)}"
