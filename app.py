from fastapi import FastAPI

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
