#Pydantic response models. APIs define schemas.
from pydantic import BaseModel

# Fixed~~~~: Removed 2 files and gathered all response models in one file for better organization and maintainability.

class FileContentResponse(BaseModel):
    filename: str = ""
    content: str = ""

#Pydantic response models. Professional APIs define schemas.

class FileUploadResponse(BaseModel):
    file_id: str = ""
    original_filename: str = ""
    stored_filename: str = ""
    size: int = 0
    message: str = "File uploaded successfully."


class FileChunkResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: list[str]  #  tells FastAPI to expect a list of text strings