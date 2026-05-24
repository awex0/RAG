import aiofiles
from pathlib import Path
from fastapi import HTTPException, UploadFile
import logging
import uuid
from config import settings

logger = logging.getLogger(__name__)

class FileService:

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.upload_dir.mkdir(exist_ok=True)

    def check_validity(self, file: UploadFile | None) -> tuple[bool, str]:
        if not file.filename:
            return False , "Filename is missing"

        if not self.check_file_type(file.content_type):
            return False , "Unsupported file type"

        return True , ""

    def generate_unique_filename(self, original_name: str) -> str:
        return f"{uuid.uuid4()}_{original_name}"

    async def save_upload(self, file: UploadFile , target_path: Path) -> tuple[bool, str]:

        async with aiofiles.open(target_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)

        logger.info(f"Saved file: {target_path}")

        return True , "File uploaded successfully" 

file_service = FileService()