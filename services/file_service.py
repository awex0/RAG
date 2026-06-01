import uuid
import logging
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from config import settings


logger = logging.getLogger(__name__)

class FileService:

    def __init__(self):

    # Create upload directory if it does not exist
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    # Check if the uploaded file type is allowed based on content type
    def check_file_type(self, content_type: str) -> bool:
        return content_type in settings.ALLOWED_TYPES

    def validate_upload(
        self,
        file: UploadFile | None
    ) -> tuple[bool, str]:
        
    # Validate the uploaded file for presence, filename, and allowed type
        if not file:
            return False, "No file uploaded"
        if not file.filename:
            return False, "Filename is missing"
        if not self.check_file_type(file.content_type):
            return False, "Unsupported file type"

        return True, ""

    def generate_unique_filename(
        self,
        original_name: str
    ) -> str:
        
    # Generate a unique filename using UUID to prevent collisions
        return f"{uuid.uuid4()}_{original_name}"

    async def save_upload(
        self,
        file: UploadFile,
        target_path: Path
    ) -> tuple[bool, str]:
        
    # Save uploaded file asynchronously with error handling
        try:

            async with aiofiles.open(target_path, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    await out.write(chunk)
            return True, "File saved successfully"

        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return False, f"Save failed: {str(e)}"
        


    # Read text file content with sanitization and error handling
    async def read_text_file(
        self,
        filename: str  ) -> str:

    # Sanitize filename to prevent path traversal
        safe_name = Path(filename).name
        target_path = self.upload_dir / safe_name

    # Check if file exists before attempting to read
        if not target_path.exists():
            raise FileNotFoundError("File does not exist")
        
    # Read file content asynchronously with error handling
        try:
            async with aiofiles.open(
                target_path,
                "r", encoding="utf-8"
            ) as file:
             content = await file.read()
            return content

        except Exception as e:

            logger.error(f"Failed to read file: {str(e)}")
            raise

    # Singleton-style reusable service instance
file_service = FileService()