"""
Retriever service for finding relevant document chunks using semantic search.
"""
from typing import List, Tuple

from src.models.document import Chunk
from src.services.embedder import Embedder
from src.services.vector_store import VectorStore
from src.utils.logger import get_logger
from config.settings import TOP_K_DEFAULT

logger = get_logger(__name__)


class Retriever:
    """Handles semantic retrieval of relevant document chunks."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        """
        Initialize retriever with embedder and vector store.

        Args:
            embedder: Embedder instance for query embedding
            vector_store: VectorStore instance for similarity search
        """
        self.embedder = embedder
        self.vector_store = vector_store
        logger.info("Retriever initialized")

    def retrieve(
        self, query: str, top_k: int = TOP_K_DEFAULT
    ) -> Tuple[List[Chunk], List[float]]:
        """
        Retrieve most relevant chunks for a query.

        Args:
            query: User's question text
            top_k: Number of chunks to retrieve (3-5)

        Returns:
            Tuple of (retrieved_chunks, similarity_scores)
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return [], []

        # Validate top_k range
        if top_k < 3 or top_k > 5:
            logger.warning(f"top_k={top_k} outside recommended range [3,5], clamping")
            top_k = max(3, min(5, top_k))

        # Embed the query
        logger.info(f"Retrieving chunks for query: '{query[:50]}...'")
        query_embedding = self.embedder.embed_text(query)

        # Search vector store
        chunks, scores = self.vector_store.search(
            query_embedding=query_embedding, top_k=top_k
        )

        if chunks:
            logger.info(
                f"Retrieved {len(chunks)} chunks with scores: "
                f"{[f'{s:.3f}' for s in scores]}"
            )
        else:
            logger.warning("No chunks retrieved for query")

        return chunks, scores
