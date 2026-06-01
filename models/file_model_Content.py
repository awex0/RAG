from pydantic import BaseModel

#Pydantic response models. Professional APIs define schemas.

class FileContentResponse(BaseModel):
    filename: str = ""
    content: str = ""