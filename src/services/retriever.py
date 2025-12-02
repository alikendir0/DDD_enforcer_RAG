"""Retriever service for finding relevant document chunks using semantic search."""
from typing import List, Tuple
import time

from src.models.document import Chunk
from src.models.conversation import QueryMetrics
from src.services.embedder import Embedder
from src.services.vector_store import VectorStore
from src.utils.logger import get_logger
from config.settings import TOP_K_DEFAULT, MIN_SIMILARITY_THRESHOLD

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
    ) -> Tuple[List[Chunk], List[float], QueryMetrics]:
        """
        Retrieve most relevant chunks for a query.

        Args:
            query: User's question text
            top_k: Number of chunks to retrieve (3-5)

        Returns:
            Tuple of (retrieved_chunks, similarity_scores, metrics)
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return [], [], QueryMetrics()

        # Validate top_k range (allow a bit more flexibility but clamp extremes)
        if top_k < 1 or top_k > 8:
            logger.warning(f"top_k={top_k} outside recommended range [1,8], clamping")
            top_k = max(1, min(8, top_k))

        logger.info(f"Retrieving chunks for query: '{query[:50]}...'")

        metrics = QueryMetrics()

        # Embed the query (measure latency)
        embed_start = time.perf_counter()
        query_embedding = self.embedder.embed_text(query)
        metrics.embedding_time_ms = int((time.perf_counter() - embed_start) * 1000)

        # Search vector store (measure latency)
        retrieval_start = time.perf_counter()
        chunks, scores = self.vector_store.search(
            query_embedding=query_embedding, top_k=top_k
        )
        metrics.retrieval_time_ms = int((time.perf_counter() - retrieval_start) * 1000)
        # Optionally filter low-similarity chunks to reduce noise
        filtered_chunks: List[Chunk] = []
        filtered_scores: List[float] = []
        threshold = max(0.0, min(1.0, MIN_SIMILARITY_THRESHOLD))
        for c, s in zip(chunks, scores):
            if s >= threshold:
                filtered_chunks.append(c)
                filtered_scores.append(s)

        if threshold > 0.0 and filtered_chunks:
            chunks, scores = filtered_chunks, filtered_scores

        metrics.retrieved_chunks = len(chunks)
        if scores:
            metrics.average_score = sum(scores) / len(scores)

        if chunks:
            logger.info(
                f"Retrieved {len(chunks)} chunks with scores: "
                f"{[f'{s:.3f}' for s in scores]}"
            )
        else:
            logger.warning("No chunks retrieved for query")

        return chunks, scores, metrics
