from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models.base_response import ApiResponse
from api.file import router as file_router


app = FastAPI(
    title="RAG Ingestion API",
    description="Backend ingestion pipeline for Files and PDFs",
    version="1.0.0"
)

app.include_router(file_router)

# BUG: home() is sync, rest is async
# be consistent across all endpoints
# change def to async def here
@app.get("/")
def home():
    return {
        "message": "RAG ingestion API is running"
    }

# BUG: no CORS middleware added
# browser frontends will be blocked
# add CORSMiddleware with allowed origins
# without it the API is frontend-unusable

# BUG: upload folder created in __init__
# should be a startup lifecycle event
# use @app.on_event("startup") instead
# keeps app setup in one clear place

@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):

     error_envelope = {
        "status_code": exc.status_code,
        "success": False,
        "content": exc.detail,
     }

     return JSONResponse(status_code=exc.status_code, content=error_envelope)
