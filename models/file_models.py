from pydantic import BaseModel,Field
from typing import List


# This model encapsulates the complete response for a text embedding request,
class FileContentResponse(BaseModel):
    filename: str 
    content: str 


#Pydantic response models. Professional APIs define schemas.
class FileUploadResponse(BaseModel):
    file_id: str 
    original_filename: str 
    stored_filename: str 
    size: int = 0
    message: str = "File uploaded successfully."

class FileChunkResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: list[str] 
    
    
    
# This model encapsulates the complete response for a text embedding request.
class TextEmbeddingRequest(BaseModel):
    text: str = Field(..., description="The raw input text string to transform into vector representations.")


# This model encapsulates the sparse vector data structure.
class SparseVectorData(BaseModel):
    indices: List[int] = Field(..., description="The list of unique vocabulary token integer IDs.")
    values: List[float] = Field(..., description="The mathematical weight/importance assigned to each token.")


# This model encapsulates the complete response for a text embedding request.
class TextEmbeddingResponse(BaseModel):
    text: str = Field(..., description="Echoes back the evaluated source text snippet.")
    dense: list[float] = Field(..., description="High-utility floating point semantic representation.")
    sparse: SparseVectorData = Field(..., description="Token weight pairs optimized for keyword matching accuracy.")
    
    