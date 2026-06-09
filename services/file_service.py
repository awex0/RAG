import os
import uuid
import logging
from pathlib import Path
import aiofiles
from fastapi import UploadFile, HTTPException
from config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding, SparseTextEmbedding
from repositories.vector_base import VectorDatabaseInterface
from services import pdf_service
from repositories.qdrant_repo import QdrantRepository



logger = logging.getLogger(__name__)
class FileService:
    
    def __init__(self, db_storage: VectorDatabaseInterface):
        
       # Create upload directory if it does not exist
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 1. Initialize local-first Qdrant Client (Keep for vector ops/searches)
        self.db = db_storage
        
        # 2. CLEAR UNUSED ARGS BY EXPLICITLY INSTANTIATING THE CLASSES HERE
        # This gives service access to self.dense_model and self.sparse_model
        self.dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        

    def check_file_type(self, 
                        content_type: str) -> bool:
        
        return content_type in settings.ALLOWED_TYPES


    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_upload(self, 
                        file: UploadFile | None) -> tuple[bool, str]:

        if not file:
            logger.warning("File validation failed: No file uploaded")
            return False, "No file uploaded"
        if not file.filename:
            logger.warning("File validation failed: Filename is missing")
            return False, "Filename is missing"
        if not self.check_file_type(file.content_type or ""):
            logger.warning("File validation failed: Unsupported file type")
            return False, "Unsupported file type"
        
        
        if file.size is not None:
            file_size = file.size
        else:
            # Safe Fallback: Move file pointer to the end to read the exact byte count
            file.file.seek(0, 2)  # 2 means seek relative to the file's end
            file_size = file.file.tell()  
            file.file.seek(0)  

        if file_size > self.MAX_SIZE:
            logger.warning("File validation failed: File size exceeds the maximum limit of 10MB")
            return False, "File size exceeds the maximum limit of 10MB"

        return True, ""


    def generate_unique_filename(self,
                                 original_name: str) -> tuple[str, str]:

        file_id = str(uuid.uuid4())
        unique_name = f"{file_id}_{original_name}"

        return file_id, unique_name


    async def save_upload(self, 
                          file: UploadFile, 
                          target_path: Path) -> tuple[bool, str]:
        
        # Save uploaded file asynchronously with error handling
        try:
            async with aiofiles.open(target_path, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    await out.write(chunk)
            return True, "File saved successfully"

        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return False, f"Save failed: {str(e)}"


    # orchestration Method: Validates, names, stores, and packages metadata
    async def process_file_upload(self, 
                                  file: UploadFile) -> dict:

        # 1. Validate file presence, type restrictions, and maximum size limits
        is_valid, validation_message = self.validate_upload(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)

        # 2. Securely generate unique tracking credentials separately
        file_id, unique_name = self.generate_unique_filename(
            file.filename or "unnamed_file"
        )

        # 3. Build target path using the pre-initialized Path object instance
        target_path = self.upload_dir / unique_name

        # 4. Stream and save the file asynchronously to the storage sandbox
        success, message = await self.save_upload(file, target_path)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        logger.info(f"File uploaded and saved successfully: {target_path}")
        
        
        # A. Read content back for extraction
        raw_text = await self.read_text_file(unique_name)
        
        # B. Fragment text into structured paragraphs/sentences
        text_chunks = self.chunk_text(raw_text)
        
        processed_points = []
        # C. Loop over chunks to create Qdrant Points
        for idx, chunk in enumerate(text_chunks):
            vectors = self.generate_hybrid_embeddings(chunk)
            
            point = {
                "id": str(uuid.uuid4()),
                "vector": {
                    "dense": vectors["dense"],
                    "sparse": vectors["sparse"]
                },
                "payload": {
                    "file_id": file_id,
                    "chunk_index": idx,
                    "text_content": chunk
                }
            }
            processed_points.append(point)

        # D. Trigger the abstract driver contract without calling a specific SDK!
        await self.db.upsert_points(collection_name="rag_collection", points=processed_points)
        
        # 5. Pack raw dictionary variables ready for schema instantiation
        return {
            "file_id": file_id,
            "original_filename": file.filename or "unnamed_file",
            "stored_filename": unique_name,
            "size": file.size or 0,
            "total_chunks_indexed": len(processed_points), # Added for transparency
            "message": "File processed, embedded, and indexed into storage layer successfully.",
        }

        

    def chunk_text(self, 
                   text: str, 
                   chunk_size: int = 500, 
                   chunk_overlap: int = 50) -> list[str]:
        
        if not text or not text.strip():
            return []

        #  chunk_size: Max number of characters per chunk.
        #  chunk_overlap: Number of characters shared between chunks to keep context alive.

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        
        return text_splitter.split_text(text)
      
      
    # Read text file content with sanitization and error handling
    async def read_text_file(self,
                             filename: str) -> str:

        safe_name = Path(filename).name
        target_path = self.upload_dir / safe_name

        # Check if file exists before attempting to read
        if not target_path.exists():
            raise FileNotFoundError("File does not exist")

        # Read file content asynchronously with error handling
        try:
            
            _, file_extension = os.path.splitext(str(target_path).lower())

            if file_extension == ".pdf":
                # Calling the static method directly without instantiation
                content = await pdf_service.PDFService.extract_text(target_path)
            else:
            
              async with aiofiles.open(target_path, "r", encoding="utf-8") as file:
                content = await file.read()
            return content

        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise
        
        
    # Generate both dense and sparse embeddings for the given text using the explicitly instantiated models.
    def generate_hybrid_embeddings(self,
                                   text: str) -> dict:
        
        if not text or len(text.strip()) == 0:
            return {"dense": [], "sparse": {"indices": [], "values": []}}

        # 1. Extract Dense Vector using explicit class (Returns generator of np.ndarray)
        dense_generator = self.dense_model.embed([text])
        dense_list = list(dense_generator)
        dense_vector = dense_list[0].tolist()  # Converts 1st item numpy array to a list

        # 2. Extract Sparse Tokens & Weights using explicit class (Returns generator of SparseVector)
        sparse_generator = self.sparse_model.embed([text])
        sparse_list = list(sparse_generator)
        sparse_vector = sparse_list[0] # Grab the first SparseVector wrapper structure

        return {
            "dense": dense_vector,
            "sparse": {
                "indices": list(sparse_vector.indices),
                "values": list(sparse_vector.values)
            }
        }
    

def get_file_service() -> FileService:
                                                 # persistent local Docker instance
     active_db = QdrantRepository(connection_url="http://localhost:6333") 
     return FileService(db_storage=active_db)
    