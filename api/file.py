import logging
import os
from models.file_Upload import FileUploadResponse
from models.file_model_Content import FileContentResponse
from models.file_model_Content import FileChunkResponse
from fastapi import (
    APIRouter,
    Query,
    UploadFile,
    File,
    HTTPException,
    status,)
from config import settings
from models.base_response import ApiResponse
from services.file_service import file_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Files"])



# API endpoint for uploading files with validation, unique naming, and error handling

@router.post("/files/", response_model=ApiResponse[FileUploadResponse],
             status_code=status.HTTP_201_CREATED
)
async def upload_stream(file: UploadFile = File(...)):
    
    #1. Validate the file (size, type.)
    is_valid, validation_message = (file_service.validate_upload(file) )

    if not is_valid:
        raise HTTPException(status_code=400,detail=validation_message)

    #2 Generate unique filename
    unique_name = (
        file_service.generate_unique_filename(
            file.filename or "unnamed_file"))
    
    file_id = unique_name.split("_", 1)[0]

    #3 Build target path
    target_path = (settings.UPLOAD_DIR / unique_name )
    success, message = (await file_service.save_upload(file,target_path   )
    )
    #4 Handle save errors
    if not success:
        raise HTTPException( status_code=500, detail=message )
    
    # 5. Package the data cleanly into your mentor's structure
    file_metadata = FileUploadResponse(
        file_id=file_id,
        original_filename=file.filename or "unnamed_file",
        stored_filename=unique_name,
        message="File processed and uploaded successfully.",
    )
    # Return the uniform response envelope
    return ApiResponse(status_code=201, success=True, content=file_metadata)



#Chunking endpoint to split file content into smaller pieces.

@router.get(
    "/files/{filename}/chunks", response_model=ApiResponse[FileChunkResponse]
)
async def get_file_chunks(
    filename: str,
    chunk_size: int = Query(default=500,ge=100,le=2000, description="The number of characters per chunk", ),
):
    
        file_response = await get_file_content(filename)
        text_chunks = file_service.chunk_text(file_response.content.content, chunk_size)

        return ApiResponse(
            status_code=status.HTTP_200_OK, success=True,
            content=FileChunkResponse(filename=filename,total_chunks=len(text_chunks),chunks=text_chunks,),
        )

# API endpoint to retrieve file content with error handling from missing files and read errors

@router.get(
    "/files/{filename}", response_model=ApiResponse[FileContentResponse]
)
async def get_file_content(filename: str):
    #Extract the safe filename to prevent directory traversal attacks
    safe_filename = os.path.basename(filename)

    try:
        content = await file_service.read_text_file(safe_filename)
        
        return ApiResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            content=FileContentResponse(filename=safe_filename, content=content),
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error reading file {safe_filename}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while reading the file.")



 