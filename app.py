from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from api.file import router as file_router
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager


# 1.
@asynccontextmanager
async def lifespan(_app: FastAPI):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    yield  #  app stays active right here while it serves requests

# 2. Initializ FastAPI application instance and attach the lifespan
app = FastAPI(
    title="RAG Ingestion API",
    description="Backend ingestion pipeline for Files and PDFs",
    version="1.0.0",
    lifespan=lifespan
)

# 3. Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# 4. Include Routers and Endpoints
app.include_router(file_router)

@app.get("/")
async def home():
    return {
        "message": "RAG ingestion API is running"
    }
    
# 5. Global Exception Handlers
@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
    error_envelope = {
        "status_code": exc.status_code,
        "success": False,
        "content": exc.detail,  
    }
    return JSONResponse(status_code=exc.status_code, content=error_envelope)



 