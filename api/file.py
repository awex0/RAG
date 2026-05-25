import logging
from models.file_models import FileUploadResponse, FileContentResponse
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status)

from config import settings
from services.file_service import file_service


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Files"]
)

# API endpoint for uploading files with validation, unique naming, and error handling

@router.post("/files/", response_model=FileUploadResponse,
             status_code=status.HTTP_201_CREATED
)
async def upload_stream(
    file: UploadFile = File(...)
):
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
        settings.UPLOAD_DIR / unique_name )
    # Save uploaded file
    success, message = (
        await file_service.save_upload(
            file,target_path   )
    )
    # Handle save errors
    if not success:
        raise HTTPException(
            status_code=500, detail=message )
    
# Return structured response with file details and status
    return {
    "success": True,
    "status_code": status.HTTP_201_CREATED,
    "file_id": file_id,
    "original_filename": file.filename,
    "stored_filename": unique_name,
    "size": target_path.stat().st_size,
    "message": message,
}  

#API endpoint to retrieve file content with error handling form missing files and read errors
@router.get("/files/{filename}", response_model=FileContentResponse)
async def get_file_content(
    filename: str
):

    try:

        content = await file_service.read_text_file(
            filename )

        return {
            "success": True,
            "filename": filename,
            "content": content  }
    
    except FileNotFoundError:
             raise HTTPException(
            status_code=404, detail="File not found")
    except Exception as e:
            raise HTTPException(
            status_code=500,
            detail=str(e)
        )