"""
Vector store service using ChromaDB for storing and searching embeddings.
"""
from typing import List, Tuple, Optional, Any, Dict, cast
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

from src.models.document import Chunk, Embedding, IndexingStatus
from src.utils.logger import get_logger
from config.settings import CHROMA_DB_PATH, COLLECTION_NAME, DISTANCE_METRIC

logger = get_logger(__name__)


class VectorStore:
    """Handles vector storage and similarity search using ChromaDB."""

    def __init__(self):
        """Initialize VectorStore (call initialize() to set up client)."""
        self.client: Optional[Any] = None
        self.collection: Optional[Collection] = None

    def initialize(self, persist_directory: Optional[str] = None) -> None:
        """
        Initialize ChromaDB client and collection.

        Args:
            persist_directory: Path for persistent storage (default from settings)
        """
        if persist_directory is None:
            persist_directory = str(CHROMA_DB_PATH)

        logger.info(f"Initializing ChromaDB at {persist_directory}")

        # Create persistent client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection with cosine distance
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": DISTANCE_METRIC},
        )
        
        assert self.collection is not None

        logger.info(
            f"ChromaDB initialized: collection '{COLLECTION_NAME}' "
            f"({self.collection.count()} existing chunks)"
        )

    def add_embeddings(self, embeddings: List[Embedding], chunks: List[Chunk]) -> None:
        """
        Store embeddings with chunk metadata.

        Args:
            embeddings: List of Embedding objects
            chunks: Corresponding Chunk objects (same order)
        """
        if not embeddings or not chunks:
            logger.warning("No embeddings or chunks to add")
            return

        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings and chunks lists must have same length")
        
        assert self.collection is not None

        # Prepare data for ChromaDB
        ids = [emb.chunk_id for emb in embeddings]
        vectors = [emb.vector for emb in embeddings]
        metadatas: List[Dict[str, Any]] = [
            {
                "chunk_id": chunk.chunk_id,
                "document_path": chunk.document_path,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "content": chunk.content[:500],  # Store first 500 chars for display
            }
            for chunk in chunks
        ]

        # Add to collection
        self.collection.add(embeddings=vectors, metadatas=metadatas, ids=ids)  # type: ignore

        logger.info(f"Added {len(embeddings)} embeddings to vector store")

    def search(
        self, query_embedding: List[float], top_k: int = 3
    ) -> Tuple[List[Chunk], List[float]]:
        """
        Search for most similar chunks using cosine similarity.

        Args:
            query_embedding: Query vector (384-dim)
            top_k: Number of results to return (3-5)

        Returns:
            Tuple of (retrieved_chunks, similarity_scores)
        """
        if not query_embedding:
            logger.warning("Empty query embedding")
            return [], []

        if top_k < 1 or top_k > 5:
            logger.warning(f"top_k={top_k} outside recommended range [3,5], clamping")
            top_k = max(3, min(5, top_k))
        
        assert self.collection is not None

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )

        if not results["ids"] or not results["ids"][0]:
            logger.info("No results found for query")
            return [], []

        # Parse results
        chunk_ids = results["ids"][0]
        distances = cast(List[float], results["distances"][0]) if results["distances"] else []
        metadatas = cast(List[Dict[str, Any]], results["metadatas"][0]) if results["metadatas"] else []

        # Convert distances to similarity scores (cosine similarity)
        # ChromaDB returns L2 distance for cosine, need to convert
        # Similarity = 1 - (distance / 2) for normalized vectors
        similarities = [1 - (d / 2) for d in distances]

        # Reconstruct Chunk objects from metadata
        chunks = []
        for metadata in metadatas:
            chunk = Chunk(
                chunk_id=str(metadata["chunk_id"]),
                document_path=str(metadata["document_path"]),
                chunk_index=int(metadata["chunk_index"]),
                content=str(metadata.get("content", "")),
                token_count=int(metadata["token_count"]),
                start_char=0,  # Not stored in metadata
                end_char=len(str(metadata.get("content", ""))),
            )
            chunks.append(chunk)

        logger.info(
            f"Retrieved {len(chunks)} chunks (scores: "
            f"{[f'{s:.3f}' for s in similarities]})"
        )

        return chunks, similarities

    def get_index_status(self) -> IndexingStatus:
        """
        Get current indexing status.

        Returns:
            IndexingStatus object with collection stats
        """
        if not self.collection:
            return IndexingStatus()

        total_chunks = self.collection.count()

        # Get unique documents (count distinct document_path values)
        # This is approximate - we count from metadata
        try:
            all_data = self.collection.get()
            metadatas = cast(List[Dict[str, Any]], all_data.get("metadatas", []))
            unique_docs = len(set(str(m.get("document_path", "")) for m in metadatas if m))
        except Exception as e:
            logger.error(f"Failed to get unique document count: {e}")
            unique_docs = 0

        status = IndexingStatus(
            total_documents=unique_docs,
            indexed_documents=unique_docs,
            failed_documents=0,  # Not tracked in vector store
            total_chunks=total_chunks,
            last_indexed=datetime.utcnow() if total_chunks > 0 else None,
        )

        return status

    def clear(self) -> None:
        """Clear all embeddings from the collection."""
        if not self.collection:
            logger.warning("Collection not initialized")
            return
        
        assert self.client is not None

        logger.info(f"Clearing collection '{COLLECTION_NAME}'")

        # Delete and recreate collection
        self.client.delete_collection(name=COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": DISTANCE_METRIC}
        )

        logger.info("Collection cleared")
