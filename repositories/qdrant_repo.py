from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PointStruct, SparseVector
from repositories.vector_base import VectorDatabaseInterface
from typing import Any, Optional
from qdrant_client import AsyncQdrantClient
import logging



logger = logging.getLogger(__name__)

# Qdrant implementation for abstract vector interface.
class QdrantRepository(VectorDatabaseInterface):

    # Changed api_key to None by default. Local Docker doesn't need a key 
    # unless you explicitly configured QDRANT__SERVICE__API_KEY.
    def __init__(self, connection_url: Optional[str] = None, api_key: Optional[str] = None):
        
        target_url = connection_url if connection_url else "http://localhost:6333"
        target_key = api_key if api_key else "my_local_password123"
        
        self.client = AsyncQdrantClient(
            url=target_url, 
            api_key=target_key
        )
        self.collection_name = "rag_collection"

    # Added = None to make arguments optional so your fallbacks actually work
    async def create_collection(self,
                                collection_name: Optional[str] = None,
                                vector_sizes: Optional[dict[str, int]] = None
        ) -> None:
        
        # Now if collection_name is omitted or empty, it correctly uses "rag_collection"
        target_name = collection_name if collection_name else self.collection_name
        sizes = vector_sizes if vector_sizes else {"dense": 384}
       
        try:
            exists = await self.client.collection_exists(collection_name=target_name)
            if exists:
                logger.info(f"[Qdrant]: Collection '{target_name}' already exists.")
                return

            await self.client.create_collection(
                collection_name= target_name,
                vectors_config={
                    "dense": VectorParams(
                        size=sizes.get("dense", 384), 
                        distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams()
                }
            )
            logger.info(f"[Qdrant Success]: Created collection '{target_name}' successfully.")
            
        except Exception as e:
            logger.error(f"[Qdrant Error]: Failed to create collection '{target_name}': {str(e)}")    

    # Added = None to make arguments optional
    async def upsert_points(self,
                            collection_name: Optional[str] = None,
                            points: Optional[list[dict[str, Any]]] = None
        ) -> bool:
        
        target_name = collection_name if collection_name else self.collection_name
        
        if not points:
            # Fixed: Log warning only when points are ACTUALLY missing or empty
            logger.warning(f"[Qdrant Warning]: Upsert called with empty points list for '{target_name}'.")
            return False
            
        try:
            qdrant_points = []
            for item in points:
                raw_sparse = item["vector"]["sparse"]
                sparse_obj = SparseVector(
                    indices=raw_sparse.get("indices", []),
                    values=raw_sparse.get("values", [])
                ) if isinstance(raw_sparse, dict) else raw_sparse
                
                point_box = PointStruct(
                    id=item["id"],                                
                    vector={
                        "dense": item["vector"]["dense"],          
                        "sparse": sparse_obj        
                    },
                    payload=item["payload"]                      
                )
                qdrant_points.append(point_box)
                
            await self.client.upsert(
                collection_name=target_name,
                points=qdrant_points,
                wait=True
            )
            
            logger.info(f"[Storage Success]: Successfully wrote {len(qdrant_points)} chunks to '{target_name}'.")
            return True
            
        except Exception as e:
            logger.error(f"[Storage Error]: Failed to save vector data structure to '{target_name}': {str(e)}")
            return False
