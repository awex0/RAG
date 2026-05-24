from pathlib import Path
import logging

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks
)

from config import settings
from services.file_service import FileService
from services.pdf_service import PDFService


# Logging

logger = logging.getLogger(__name__)


app = FastAPI(
    title="RAG Ingestion API",
    description="Backend ingestion pipeline for PDFs",
    version="1.0.0"
)


# Services

file_service = FileService(settings.UPLOAD_DIR)


# Background PDF Processing

async def process_pdf(path: str):

    logger.info(f"Starting PDF processing: {path}")

    pdf_path = Path(path)

    extracted_text = PDFService.extract_text(pdf_path)

    logger.info(f"Extracted text length: {len(extracted_text)}")

    print("\n========== PDF TEXT ==========\n")
    print(extracted_text[:3000])  # print first 3000 chars
    print("\n==============================\n")

# Routes

@app.get("/")
def home():

    return {
        "message": "RAG ingestion API is running"
    }


@app.post("/upload/stream")
async def upload_stream(
    file: UploadFile = File(...)
):
    if not file_service.check_file_type(file.content_type):
        raise HTTPException(415, "Unsupported file type")

    saved_path = await file_service.save_upload(file)

    file_size = saved_path.stat().st_size

    return {
        "filename": file.filename,
        "size": file_size,
        "path": str(saved_path),
        "message": "File uploaded successfully"
    }


@app.post("/upload/with-bg")
async def upload_with_background(
    background: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file_service.check_file_type(file.content_type):
        raise HTTPException(415, "Unsupported file type")

    saved_path = await file_service.save_upload(file)

    background.add_task(process_pdf, str(saved_path))

    file_size = saved_path.stat().st_size
    return {
        "filename": file.filename,
        "size": file_size,
        "path": str(saved_path),
        "message": "File uploaded successfully"
    }

#Get list of all files in the upload folder with their name, size, and extension

@app.get("/files")
def list_files():
    try:
        # Convert settings path or service path to a clean Path object
        upload_dir = Path(settings.UPLOAD_DIR)
        
        # Guard check if the upload folder does not exist yet
        if not upload_dir.exists():
            return {"files": [], "message": "Upload directory is empty"}
            
        # Scan the folder for files matching *.pdf or *.txt
        all_files = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in {".pdf", ".txt"}:
                all_files.append({
                    "filename": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "extension": file_path.suffix.lower()
                })
                
        return {
            "total_count": len(all_files),
            "files": all_files,
            "message": "Files retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error scanning file directory")

#Read PDF endpoint

@app.get("/read-pdf")
def read_pdf(filename: str):
    try:
        # 1. Resolve path using settings config
        upload_dir = Path(settings.UPLOAD_DIR)
        target_path = upload_dir / filename

        # 2. Check if the specific file exists on disk
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

        # 3. Restrict endpoint to PDF extensions strictly
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="This endpoint only supports PDF extraction files")

        # 4. Use your existing PDFService to pull text blocks
        logger.info(f"API request to extract text layer from: {filename}")
        extracted_text = PDFService.extract_text(target_path)

        return {
            "message": "PDF text extracted successfully!",
            "filename": filename,
            "extracted_text": extracted_text[:3000]  # First 3000 chars matching specs
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to read PDF stream: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error parsing PDF contents")


# one endpoint for upload file 
# response with file name, size, path, and message

# read pdf  endpoint 
# accept file name  
# response with extracted text (first 3000 chars) and message