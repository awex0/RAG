from pydantic import BaseModel

# fix 
# File structure issue (models)
# You currently have:
# file_Upload.py
# file_model_Content.py
# Trainer feedback:
# This is over-splitting for a small project.
# Fix (good practice for beginners):
# 👉 Merge into ONE file:
# models/file.py


#Pydantic response models. Professional APIs define schemas.
class FileContentResponse(BaseModel):
    filename: str = ""
    content: str = ""


class FileChunkResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: list[str]  #  tells FastAPI to expect a list of text strings