import uuid
import logging
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from fastapi import HTTPException
from config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self):
        # Create upload directory if it does not exist
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    # Check if the uploaded file type is allowed based on content type
    def check_file_type(self, content_type: str) -> bool:
        return content_type in settings.ALLOWED_TYPES

    def validate_upload(self, file: UploadFile | None) -> tuple[bool, str]:

        # Validate the uploaded file for presence, filename, allowed type and allowed size
        if not file:
            logger.warning("File validation failed: No file uploaded")
            return False, "No file uploaded"
        if not file.filename:
            logger.warning("File validation failed: Filename is missing")
            return False, "Filename is missing"
        if not self.check_file_type(file.content_type or ""):
            logger.warning("File validation failed: Unsupported file type")
            return False, "Unsupported file type"
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        if file.size and file.size > MAX_SIZE:
            logger.warning("File validation failed: File size exceeds the maximum limit of 10MB")
            return False, "File size exceeds the maximum limit of 10MB"

        return True, ""

    def generate_unique_filename(self, original_name: str) -> tuple[str, str]:

        # Generate a unique filename using UUID to prevent collisions and ensure safe storage
        file_id = str(uuid.uuid4())
        unique_name = f"{file_id}_{original_name}"

        return file_id, unique_name

    async def save_upload(
        self, file: UploadFile, target_path: Path
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

    # orchestration Method: Validates, names, stores, and packages metadata
    async def process_file_upload(self, file: UploadFile) -> dict:

        # 1. Validate file presence, type restrictions, and maximum size limits
        is_valid, validation_message = self.validate_upload(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)

        # 2. Securely generate unique tracking credentials separately
        file_id, unique_name = self.generate_unique_filename(
            file.filename or "unnamed_file"
        )

        # 3. Build target path using the pre-initialized Path object instance
        target_path = self.upload_dir / unique_name

        # 4. Stream and save the file asynchronously to the storage sandbox
        success, message = await self.save_upload(file, target_path)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        logger.info(f"File uploaded and saved successfully: {target_path}")
        
        # 5. Pack raw dictionary variables ready for schema instantiation
        return {
            "file_id": file_id,
            "original_filename": file.filename or "unnamed_file",
            "stored_filename": unique_name,
            "size": file.size or 0,
            "message": "File uploaded successfully.",
        }

    def chunk_text(
        self, text: str, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> list[str]:
        if not text:
            return []

        #  chunk_size: Max number of characters per chunk.
        #  chunk_overlap: Number of characters shared between chunks to keep context alive.
        #  chunking safety
        
        if not text or len(text.strip()) == 0:
            return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        return text_splitter.split_text(text)
      
    # Read text file content with sanitization and error handling
    async def read_text_file(self, filename: str) -> str:

        safe_name = Path(filename).name
        target_path = self.upload_dir / safe_name

        # Check if file exists before attempting to read
        if not target_path.exists():
            raise FileNotFoundError("File does not exist")

        # Read file content asynchronously with error handling
        try:
            async with aiofiles.open(target_path, "r", encoding="utf-8") as file:
                content = await file.read()
            return content

        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise

    # Singleton-style reusable service instance


file_service = FileService()
