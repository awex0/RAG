import aiofiles
from pathlib import Path
from fastapi import HTTPException, UploadFile
import logging
import uuid


logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain"
}


class FileService:

    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(exist_ok=True)

    def check_file_type(self, content_type: str | None) -> bool:
        return bool(content_type and content_type in ALLOWED_TYPES)

    def generate_unique_filename(self, original_name: str) -> str:
        return f"{uuid.uuid4()}_{original_name}"

    async def save_upload(self, file: UploadFile) -> Path:
        if not file.filename:
            raise HTTPException(400, "Filename is missing")

        if not self.check_file_type(file.content_type):
            raise HTTPException(415, "Unsupported file type")

        original_name = Path(file.filename).name
        unique_name = self.generate_unique_filename(original_name)
        target = self.upload_dir / unique_name

        async with aiofiles.open(target, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)

        logger.info(f"Saved file: {target}")

        return target