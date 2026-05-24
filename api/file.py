import logging

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from config import settings
from services.file_service import file_service


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="",
    tags=["Files"]
)


@router.post("/upload/")
async def upload_stream(
    file: UploadFile = File(...)
):

    is_valid, validation_message = file_service.check_validity(file)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message
        )

    unique_name = file_service.generate_unique_filename(
        file.filename
    )

    file_id = unique_name.split("_", 1)[0]

    target_path = settings.UPLOAD_DIR / unique_name

    success, message = await file_service.save_upload(
        file,
        target_path
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail=message
        )

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": target_path.stat().st_size,
        "message": message
    }