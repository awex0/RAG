# database/vector_base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


# Abstract contract for vector database infrastructure.
class VectorDatabaseInterface(ABC):
    # Initialize collection schemas with specified vector configurations.
    @abstractmethod
    async def create_collection(
        self, collection_name: str, vector_sizes: Dict[str, int]
    ) -> None:
        pass

    @abstractmethod
    async def upsert_points(
        self, collection_name: str, points: List[Dict[str, Any]]
    ) -> bool:
        pass
