import uuid
import logging
from pathlib import Path
import aiofiles
from fastapi import UploadFile
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

    def validate_upload(
        self,file: UploadFile | None) -> tuple[bool, str]:
        
    # Validate the uploaded file for presence, filename, and allowed type
        if not file:
            return False, "No file uploaded"
        if not file.filename:
            return False, "Filename is missing"
        if not self.check_file_type(file.content_type or ""):
            return False, "Unsupported file type"

        return True, ""

    def generate_unique_filename(self,original_name: str) -> str:
        
    # Generate a unique filename using UUID to prevent collisions
        return f"{uuid.uuid4()}_{original_name}"

    async def save_upload(
        self, file: UploadFile,target_path: Path ) -> tuple[bool, str]:
        
    # Save uploaded file asynchronously with error handling
        try:

            async with aiofiles.open(target_path, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    await out.write(chunk)
            return True, "File saved successfully"

        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return False, f"Save failed: {str(e)}"
        


    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
        if not text: return []

        #  chunk_size: Max number of characters per chunk.
        #  chunk_overlap: Number of characters shared between chunks to keep context alive.

        #   7. Chunking safety issue
        # Problem:
        # if not text: return []
        # Good, but missing validation:
        # Improve:
        # if not text or len(text.strip()) == 0:
        #     return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators = ["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_text(text)
    

    # Read text file content with sanitization and error handling
    async def read_text_file(
        self,filename: str) -> str:

        safe_name = Path(filename).name
        target_path = self.upload_dir / safe_name

    # Check if file exists before attempting to read
        if not target_path.exists():
            raise FileNotFoundError("File does not exist")
        
    #  8. Async file reading line (hard to read)
    # Problem:
    # async with aiofiles.open(... ) as file:content = await file.read()
    # Fix (clean code):
    # async with aiofiles.open(target_path, "r", encoding="utf-8") as file:
    #     content = await file.read()
    
    # Read file content asynchronously with error handling
        try:
            async with aiofiles.open(
                target_path,  "r", encoding="utf-8") as file:content = await file.read()
            return content

        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise
    # Singleton-style reusable service instance
    
file_service = FileService()

