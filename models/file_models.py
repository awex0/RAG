from pydantic import BaseModel

#Pydantic response models. Professional APIs define schemas.

class FileUploadResponse(BaseModel):

    success: bool
    file_id: str
    original_filename: str
    stored_filename: str
    size: int
    message: str


class FileContentResponse(BaseModel):

    success: bool
    filename: str
    content: str