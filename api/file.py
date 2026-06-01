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

# ❗ 9. API logic mixing concerns
# Problem:

# Inside endpoint you:

# validate
# generate filename
# save file
# build response
# Beginner improvement:

# Keep endpoint simple:
# 👉 move logic into service layer later

#------------------------------------------------
# ❗ 10. Missing logging in important places

# You only log errors.

# Add logging for:
# successful upload
# file validation failure
# chunking request

# Example:

# logger.info(f"File uploaded: {unique_name}")

#---------------------------------------------
# ❗ 11. API Response consistency issue
# Problem:

# Sometimes you raise HTTPException,
# sometimes return ApiResponse.

# Fix:

# Be consistent:

# Errors → HTTPException
# Success → ApiResponse

# example how to code :
# Clean Code Example (Single Endpoint Refactor)
# 👉 What we improve:
# Separate logic clearly
# Reduce repeated work
# Better naming
# Cleaner structure
# Easier to maintain

# @router.post(
#     "/files/",
#     response_model=ApiResponse[FileUploadResponse],
#     status_code=status.HTTP_201_CREATED
# )
# async def upload_file(file: UploadFile = File(...)):
#     """
#     Upload a file with validation, unique naming, and safe storage.
#     """

#     # 1. Validate file
#     is_valid, error_message = file_service.validate_upload(file)
#     if not is_valid:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=error_message
#         )

#     # 2. Generate safe unique filename
#     file_id = str(uuid.uuid4())
#     original_name = file.filename or "unnamed_file"
#     stored_filename = f"{file_id}_{original_name}"

#     # 3. Build file path safely
#     file_path = Path(settings.UPLOAD_DIR) / stored_filename

#     # 4. Save file
#     success, message = await file_service.save_upload(file, file_path)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=message
#         )

#     # 5. Build response (clean and structured)
#     response = FileUploadResponse(
#         file_id=file_id,
#         original_filename=original_name,
#         stored_filename=stored_filename,
#         message="File uploaded successfully."
#     )

#     return ApiResponse(
#         status_code=status.HTTP_201_CREATED,
#         success=True,
#         content=response
#     )




# API endpoint for uploading files with validation, unique naming, and error handling
@router.post("/files/", response_model=ApiResponse[FileUploadResponse],
             status_code=status.HTTP_201_CREATED
)
async def upload_stream(file: UploadFile = File(...)):
    
    #  ❗ 6. Missing file size handling (important security point)
    # You wrote comment but NOT implemented:
    # Problem:
    # No limit on upload size → can crash server
    # Fix idea (simple):
    # MAX_SIZE = 10 * 1024 * 1024  # 10MB
    # Check inside loop.
    # dont add () to the method call like this (file_service.validate_upload(file) )

    is_valid, validation_message = (file_service.validate_upload(file) )

    if not is_valid:
        raise HTTPException(status_code=400,detail=validation_message)


    # ❗ 5. File ID extraction is fragile
    # Problem:
    # file_id = unique_name.split("_", 1)[0]
    # This depends on naming format.
    # Better beginner fix:
    # Store UUID separately:
    # file_id = str(uuid.uuid4())
    # unique_name = f"{file_id}_{original_name}"

    #2 Generate unique filename
    unique_name = file_service.generate_unique_filename(
            file.filename or "unnamed_file"
    )
    file_id = unique_name.split("_", 1)[0]
    
    # 4. Wrong type for UPLOAD_DIR usage
    # Problem:
    # self.upload_dir = Path(settings.UPLOAD_DIR)
    # But later:
    # settings.UPLOAD_DIR / unique_name
    # This may break if UPLOAD_DIR is a string.
    # Fix:
    # Be consistent:
    # UPLOAD_DIR = Path(settings.UPLOAD_DIR)
    # target_path = UPLOAD_DIR / unique_name

    #3 Build target path
    # dont add () to the method call like this (settings.UPLOAD_DIR / unique_name )
    target_path = (settings.UPLOAD_DIR / unique_name )
    
    # dont add () to the method call like this (await file_service.save_upload(file,target_path   ) )
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

# Chunking endpoint to split file content into smaller pieces using LangChain
@router.get(
    "/files/{filename}/chunks", response_model=ApiResponse[FileChunkResponse]
)
async def get_file_chunks(
    filename: str,
    chunk_size: int = Query(default=500, ge=100, le=2000, description="The maximum size of each text chunk",),
    chunk_overlap: int = Query( default=50,ge=0,le=500,description="The number of overlapping characters between chunks",),
):
    
    # Call your programmatic master route to fetch and validate the file
    file_response = await get_file_content(filename)

    #  Process chunking using your updated LangChain method inside file_service
    text_chunks = file_service.chunk_text(
        text=file_response.content.content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        success=True,
        content=FileChunkResponse(
            filename=filename,total_chunks=len(text_chunks),chunks=text_chunks),
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



 