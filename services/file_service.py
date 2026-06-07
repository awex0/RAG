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

    # BUG: comment repeats the code
    # reader already knows what this does
    # delete comments that say nothing new
    def check_file_type(self, content_type: str) -> bool:
        return content_type in settings.ALLOWED_TYPES

    def validate_upload(self, file: UploadFile | None) -> tuple[bool, str]:

        # BUG: comment repeats what code says
        # say WHY, not WHAT it does
        # remove this comment entirely
        if not file:
            logger.warning("File validation failed: No file uploaded")
            return False, "No file uploaded"
        if not file.filename:
            logger.warning("File validation failed: Filename is missing")
            return False, "Filename is missing"
        if not self.check_file_type(file.content_type or ""):
            logger.warning("File validation failed: Unsupported file type")
            return False, "Unsupported file type"

        # BUG: MAX_SIZE defined inside method
        # recreated on every single call
        # move it to config or class level
        MAX_SIZE = 10 * 1024 * 1024  # 10MB

        # BUG: file.size can be None
        # some clients do not send file size
        # validation can be silently skipped
        # use content-length header instead
        if file.size and file.size > MAX_SIZE:
            logger.warning("File validation failed: File size exceeds the maximum limit of 10MB")
            return False, "File size exceeds the maximum limit of 10MB"

        return True, ""

    def generate_unique_filename(self, original_name: str) -> tuple[str, str]:

        # BUG: comment repeats the code again
        # uuid4 already implies uniqueness
        # remove comments that restate code
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

    async def process_file_upload(self, file: UploadFile) -> dict:

        is_valid, validation_message = self.validate_upload(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)

        file_id, unique_name = self.generate_unique_filename(
            file.filename or "unnamed_file"
        )

        target_path = self.upload_dir / unique_name

        success, message = await self.save_upload(file, target_path)
        if not success:
            raise HTTPException(status_code=500, detail=message)

        logger.info(f"File uploaded and saved successfully: {target_path}")

        # BUG: returns raw dict to the caller
        # caller then builds FileUploadResponse
        # return FileUploadResponse directly here
        # keeps types consistent and clean
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

        # BUG: same check done twice
        # line below repeats this exact check
        # delete one of them, keep the stricter
        if not text:
            return []

        # BUG: PDF is never handled here
        # PDFs saved as binary, read as text
        # read_text_file will crash on PDFs
        # call pdf_service.extract_text first
        if not text or len(text.strip()) == 0:
            return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        return text_splitter.split_text(text)

    async def read_text_file(self, filename: str) -> str:

        safe_name = Path(filename).name
        target_path = self.upload_dir / safe_name

        if not target_path.exists():
            raise FileNotFoundError("File does not exist")

        try:
            # BUG: opens PDF as UTF-8 text
            # PDF files are binary, not text
            # this will crash or return garbage
            # check extension, use pdf_service
            async with aiofiles.open(target_path, "r", encoding="utf-8") as file:
                content = await file.read()
            return content

        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise


file_service = FileService()
