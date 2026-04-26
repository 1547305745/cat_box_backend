import chromadb
from typing import List, Optional, Tuple
import os

from config import settings


class VectorStoreManager:
    def __init__(self, collection_name: str = "memories"):
        self.vector_db_path = settings.vector_db_path
        os.makedirs(self.vector_db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[dict] = None
    ) -> None:
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata] if metadata else [None]
        )

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where_filter: Optional[dict] = None
    ) -> List[Tuple[str, str, dict]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        memories = []
        if results["ids"] and results["ids"][0]:
            for i, mem_id in enumerate(results["ids"][0]):
                doc = results["documents"][0][i] if results["documents"] else ""
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                memories.append((mem_id, doc, meta))
        return memories

    def delete(self, memory_id: str) -> None:
        self.collection.delete(ids=[memory_id])

    def delete_by_character(self, character_id: str) -> None:
        results = self.collection.get(where={"character_id": character_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def count(self) -> int:
        return self.collection.count()
