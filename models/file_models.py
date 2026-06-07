from pydantic import BaseModel

# BUG: task notes do not belong in code
# use git commit messages for this instead
# delete fix notes like "Fixed~~~~:" here
# Fixed~~~~: Removed 2 files and gathered all response models in one file for better organization and maintainability.

# BUG: empty string default hides bugs
# a missing filename should raise an error
# not silently return an empty string
# remove the = "" defaults here
class FileContentResponse(BaseModel):
    filename: str = ""
    content: str = ""


# BUG: same problem, empty defaults hide errors
# file_id: str = "" means a failed upload
# looks like a success with empty data
# remove defaults, let pydantic catch missing
class FileUploadResponse(BaseModel):
    file_id: str = ""
    original_filename: str = ""
    stored_filename: str = ""
    size: int = 0
    message: str = "File uploaded successfully."


class FileChunkResponse(BaseModel):
    filename: str
    total_chunks: int
    # BUG: inline comment restates the type
    # list[str] already says it is strings
    # remove comments that repeat the code
    chunks: list[str]  #  tells FastAPI to expect a list of text strings
