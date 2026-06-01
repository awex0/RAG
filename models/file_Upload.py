from pydantic import BaseModel

#Pydantic response models. Professional APIs define schemas.

class FileUploadResponse(BaseModel):
    file_id: str = ""
    original_filename: str = ""
    stored_filename: str = ""
    size: int = 0
    message: str = "File uploaded successfully."
