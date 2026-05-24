import aiofiles
from pathlib import Path
from typing import List, Optional, Annotated
# CRUCIAL: Make sure UploadFile and File are imported together from fastapi
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
import logging


logger = logging.getLogger(__name__)

app = FastAPI()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# --- BACKGROUND HELPER FUNCTION ---
# This runs after the API sends a response back to the user
async def generate_thumbnail(path: str) -> None:
    # You can add heavy logic here later (e.g., parsing PDFs or image resizing)
    logger.info(f"Background processing started for file: {path}")


# --- EXISTING ENPOINTS ---
@app.get("/")
def home():
    return {"message": "Welcome! Go to /docs to see all endpoints."}


app = FastAPI()
# ... keep your UPLOAD_DIR and home() code exactly the same ...

# --- THE FIX ---
# Define a strict type that explicitly tells Swagger UI to render a binary file selector
SwaggerFile = Annotated[UploadFile, File(description="Select multiple files to upload")]

@app.post("/upload/many")
async def upload_many(
    user_id: str = Form(...),
    note: Optional[str] = Form(None),
    files: list[SwaggerFile] = File(...),  # Use the custom Annotated type wrapper here
):
    total = 0
    for f in files:
        if f.content_type not in {"application/pdf"}:
            raise HTTPException(415, f"Bad type for {f.filename}")
        size = len(await f.read())
        total += size
        # save files in the upload directory
    return {"count": len(files), "bytes": total, "user_id": user_id, "note": note}


@app.post("/upload/stream")
async def upload_stream(file: UploadFile = File(...)):
    target = UPLOAD_DIR / file.filename
    # add logs here to see the content type and file size
    if file.content_type not in { "application/pdf"}:
        raise HTTPException(415, "Unsupported file type")

    async with aiofiles.open(target, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)
            logger.info(f"Processing chunk for {file.filename}")
    return {"stored_as": str(target)}


# --- NEW BACKGROUND TASK ENDPOINT ---
@app.post("/upload/with-bg")
async def upload_with_bg(background: BackgroundTasks, file: UploadFile = File(...)):
    target = UPLOAD_DIR / file.filename
    
    if file.content_type not in { "application/pdf"}:
        raise HTTPException(415, "Unsupported file type")

    async with aiofiles.open(target, "wb") as out:
        while chunk := await file.read(1_000_000): # ~1MB chunks
            await out.write(chunk)
            logger.info(f"Processing chunk for {file.filename}")

    # Trigger the background worker 
    background.add_task(generate_thumbnail, str(target))
    
    return {"status": "queued", "file": file.filename}
