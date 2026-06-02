from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models.base_response import ApiResponse
from api.file import router as file_router


app = FastAPI(
    title="RAG Ingestion API",
    description="Backend ingestion pipeline for Files and PDFs",
    version="1.0.0"
)

# Register API routes
app.include_router(file_router)

@app.get("/")
def home():

    return {
        "message": "RAG ingestion API is running"
    }
    
# Global exception handler for HTTPException to ensure consistent error responses    
@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
  
     error_envelope = {
        "status_code": exc.status_code,
        "success": False,
        "content": exc.detail,  
     }

     return JSONResponse(status_code=exc.status_code, content=error_envelope)