"""
Embedder service for generating vector embeddings using sentence transformers.
"""
from typing import List

from sentence_transformers import SentenceTransformer

from src.models.document import Chunk, Embedding
from src.utils.logger import get_logger
from config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSION

logger = get_logger(__name__)


class Embedder:
    """Handles embedding generation using sentence transformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize embedder with sentence transformer model.

        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded (dimension: {EMBEDDING_DIMENSION})")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text string.

        Args:
            text: Text to embed

        Returns:
            384-dimensional embedding vector as list of floats
        """
        if not text:
            logger.warning("Empty text provided for embedding")
            return [0.0] * EMBEDDING_DIMENSION

        # Generate embedding (returns numpy array)
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Convert to list and return
        return embedding.tolist()

    def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """
        Generate embeddings for multiple chunks (batch operation).

        Args:
            chunks: List of Chunk objects

        Returns:
            List of Embedding objects (same order as input)
        """
        if not chunks:
            logger.warning("No chunks provided for embedding")
            return []

        # Extract text from chunks
        texts = [chunk.content for chunk in chunks]

        # Batch embed (more efficient than one-by-one)
        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings_array = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10
        )

        # Create Embedding objects
        embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = Embedding(
                chunk_id=chunk.chunk_id,
                vector=embeddings_array[i].tolist(),
                model_name=self.model_name,
                model_version="1.0",  # Could be extracted from model metadata
            )
            embeddings.append(embedding)

            # Update chunk with embedding reference
            chunk.embedding = embedding.vector

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
