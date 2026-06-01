from pydantic import BaseModel

#Pydantic response models. Professional APIs define schemas.

class FileContentResponse(BaseModel):
    filename: str = ""
    content: str = ""


class FileChunkResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: list[str]  #  tells FastAPI to expect a list of text strings