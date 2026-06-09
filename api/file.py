import logging
import os
from pathlib import Path

from fastapi import (
    APIRouter,
    Query,
    UploadFile,
    File,
    HTTPException,
    status,
    Depends
)

from models.file_models import (
    FileContentResponse,
    FileChunkResponse,  
    FileUploadResponse,
    SparseVectorData,
    TextEmbeddingRequest,
    TextEmbeddingResponse
) 
from models.base_response import ApiResponse
from services.pdf_service import PDFService
from services.file_service import FileService, get_file_service




logger = logging.getLogger(__name__)
router = APIRouter(tags=["Files"])

# 1. FILE UPLOAD ENDPOINT
@router.post("/files/", response_model=ApiResponse[FileUploadResponse],
             status_code=status.HTTP_201_CREATED          
)
async def upload_stream(
        file: UploadFile = File(...),
        file_service: FileService = Depends(get_file_service)
):
    # Orchestrate the file upload process with validation, unique naming, storage, and metadata packaging
    try:
        
     upload_response = await file_service.process_file_upload(file)
     
     file_metadata = FileUploadResponse(**upload_response)

     return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        success=True,
        content=file_metadata
    )
     
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Upload pipeline failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An ingestion failure occurred: {str(e)}"
        )


# 2. FILE CHUNKING ENDPOINT
@router.get("/files/{filename}/chunks", response_model=ApiResponse[FileChunkResponse])  
async def get_file_chunks(filename: str,
    chunk_size: int =
    Query(default=500, ge=100, le=2000, description="The maximum size of each text chunk",),
    chunk_overlap: int =
    Query( default=50,ge=0,le=500,description="The number of overlapping characters between chunks",),
    file_service: FileService = 
    Depends(get_file_service)
):
    
    logger.info(f"Chunking request received for file: {filename} with chunk_size: {chunk_size} and chunk_overlap: {chunk_overlap}")
    
    file_content = await file_service.read_text_file(filename)

    #  Process chunking using your updated LangChain method inside file_service
    text_chunks = file_service.chunk_text(
        text=file_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        success=True,
        content=FileChunkResponse(
            filename=filename,
            total_chunks=len(text_chunks),
            chunks=text_chunks)
    )



# 3. RETRIEVE FILE CONTENT ENDPOINT

@router.get(
    "/files/{filename}", response_model=ApiResponse[FileContentResponse]  
)
async def get_file_content(filename: str,
                           file_service:FileService = Depends(get_file_service)
):
    
    # Extract the safe filename to prevent directory traversal attacks.
    safe_filename = os.path.basename(filename)

    try:
        file_extension = os.path.splitext(safe_filename.lower()) [1]

        if file_extension == ".pdf":
            # Call pdf_service to extract text from PDFs cleanly
            content = await PDFService.extract_text(Path(safe_filename))
        else:
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



# 4. HYBRID EMBEDDINGS ENDPOINT

@router.post(
    "/embed-text",
    response_model=ApiResponse[TextEmbeddingResponse],
    status_code=status.HTTP_200_OK, 
    summary="Generate Hybrid Text Embeddings",
    description="Accepts plain text payloads to generate dense (semantic) and sparse (lexical) open-source vector models simultaneously."
)
async def embed_plain_text(payload: TextEmbeddingRequest,
                        file_service: FileService = Depends(get_file_service)):
    
    logger.info("Received execution request for text embedding transformation stream.")
    
    # 1. Call service method to generate both dense and sparse embeddings for the given text using  models
    vectors = file_service.generate_hybrid_embeddings(payload.text)
    
    # 2. Package raw execution returns into explicit schema formats
    response_payload = TextEmbeddingResponse(
        
        text=payload.text,
        dense=vectors["dense"],    
        sparse=SparseVectorData(
            indices=vectors["sparse"]["indices"],
            values=vectors["sparse"]["values"])
    )
    
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        success=True,
        content=response_payload
    )
 
 
 