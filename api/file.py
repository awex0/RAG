import logging
import os
from models.file_models import FileUploadResponse
from models.file_models import FileContentResponse
from models.file_models import FileChunkResponse
from fastapi import (
    APIRouter,
    Query,
    UploadFile,
    File,
    HTTPException,
    status,)
from models.base_response import ApiResponse
from services.file_service import file_service


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Files"])

# BUG: comment just restates the route name
# say WHY the logic is in process_file_upload
# or remove this comment entirely
@router.post("/files/", response_model=ApiResponse[FileUploadResponse],
             status_code=status.HTTP_201_CREATED
)

# BUG: comment belongs inside the function
# decorators and functions stay together
# no code between decorator and def
async def upload_stream(file: UploadFile = File(...)):
    upload_response = await file_service.process_file_upload(file)
    file_metadata = FileUploadResponse(**upload_response)
    
    return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        success=True,
        content=file_metadata
    )


# BUG: same comment written twice here
# one with LangChain, one without
# pick one and delete the other
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

    logger.info(f"Chunking request received for file: {filename} with chunk_size: {chunk_size} and chunk_overlap: {chunk_overlap}")

    # BUG: route calling another route
    # routes should only call services
    # this creates tight coupling between routes
    # call file_service.read_text_file directly
    file_response = await get_file_content(filename)

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


@router.get(
    "/files/{filename}", response_model=ApiResponse[FileContentResponse]
)
async def get_file_content(filename: str):
    safe_filename = os.path.basename(filename)

    try:
        # BUG: PDF files are read as plain text
        # this returns binary garbage for PDFs
        # check the file extension here first
        # call pdf_service for .pdf files
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
