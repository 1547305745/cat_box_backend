from typing import List, Optional, Tuple
from datetime import datetime
import uuid

from memory.vector_store import VectorStoreManager
from memory.embedding import EmbeddingManager
from config import settings


class MemoryManager:
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.embedding_manager = EmbeddingManager()

    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str,
        character_id: Optional[str] = None,
        importance_score: int = 5
    ) -> str:
        memory_id = str(uuid.uuid4())
        embedding = await self.embedding_manager.aembed_text(content)

        metadata = {
            "user_id": user_id,
            "memory_type": memory_type,
            "created_at": datetime.utcnow().isoformat(),
            "importance_score": importance_score
        }
        if character_id:
            metadata["character_id"] = character_id

        self.vector_store.add_memory(
            memory_id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata
        )

        return memory_id

    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        character_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Tuple[str, str, float]]:
        query_embedding = await self.embedding_manager.aembed_text(query)

        where_filter = {"user_id": user_id}
        if character_id:
            where_filter["character_id"] = character_id

        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where_filter=where_filter
        )

        memories_with_scores = []
        for mem_id, content, metadata in results:
            score = 1.0 - (metadata.get("importance_score", 5) / 10.0)
            memories_with_scores.append((mem_id, content, score))

        memories_with_scores.sort(key=lambda x: x[2], reverse=True)
        return memories_with_scores

    def delete_memory(self, memory_id: str) -> None:
        self.vector_store.delete(memory_id)

    def clear_character_memories(self, character_id: str) -> None:
        self.vector_store.delete_by_character(character_id)

    def clear_user_memories(self, user_id: str) -> None:
        pass

    def count_memories(self) -> int:
        return self.vector_store.count()
