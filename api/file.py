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
    tags=["Files"]
)


@router.post("/upload/")
async def upload_stream(
    file: UploadFile = File(...)
):

    # Validate uploaded file
    is_valid, validation_message = (
        file_service.validate_upload(file)
    )

    if not is_valid:

        raise HTTPException(
            status_code=400,
            detail=validation_message
        )

    # Generate unique filename
    unique_name = (
        file_service.generate_unique_filename(
            file.filename
        )
    )

    # Extract UUID as file ID
    file_id = unique_name.split("_", 1)[0]

    # Build target path
    target_path = (
        settings.UPLOAD_DIR / unique_name
    )

    # Save uploaded file
    success, message = (
        await file_service.save_upload(
            file,
            target_path
        )
    )

    if not success:

        raise HTTPException(
            status_code=500,
            detail=message
        )

    return {
    "file_id": file_id,
    "original_filename": file.filename,
    "stored_filename": unique_name,
    "size": target_path.stat().st_size,
    "path": str(target_path),
    "message": message
}
    


@router.get("/files/{filename}")
async def get_file_content(
    filename: str
):

    try:

        content = await file_service.read_text_file(
            filename
        )

        return {
            "filename": filename,
            "content": content
        }

    except FileNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )