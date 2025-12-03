"""
Chunker service for splitting documents into fixed-size token chunks.
"""
from typing import List

from transformers import AutoTokenizer

from src.models.document import Document, Chunk
from src.utils.logger import get_logger
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL

logger = get_logger(__name__)


class Chunker:
    """Handles splitting documents into fixed-size token chunks."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize chunker with tokenizer matching the embedding model.

        Args:
            chunk_size: Maximum tokens per chunk (default from settings)
            chunk_overlap: Overlapping tokens between chunks (default from settings)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Use tokenizer matching the embedding model
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        logger.info(f"Chunker initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
        logger.info(f"Using tokenizer from: {EMBEDDING_MODEL}")

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Split document content into token chunks with optional overlap.

        Args:
            document: Document object with content to chunk

        Returns:
            List of Chunk objects
        """
        if not document.content:
            logger.warning(f"Empty document: {document.filename}")
            return []

        # Tokenize the entire content
        tokens = self.tokenizer.encode(document.content, add_special_tokens=False)
        total_tokens = len(tokens)

        chunks = []
        chunk_index = 0
        
        # Calculate step size (chunk_size - overlap)
        step_size = self.chunk_size - self.chunk_overlap
        if step_size <= 0:
            logger.warning(f"Invalid overlap {self.chunk_overlap} for chunk_size {self.chunk_size}, using no overlap")
            step_size = self.chunk_size

        # Split into chunks with overlap
        i = 0
        while i < total_tokens:
            # Get chunk tokens
            chunk_end = min(i + self.chunk_size, total_tokens)
            chunk_tokens = tokens[i:chunk_end]

            # Decode tokens back to text
            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)

            # Find character positions (approximate)
            start_char = len(self.tokenizer.decode(tokens[:i], skip_special_tokens=True))
            end_char = start_char + len(chunk_text)

            # Create chunk object
            chunk = Chunk(
                chunk_id=f"{document.file_path}:{chunk_index}",
                document_path=document.file_path,
                chunk_index=chunk_index,
                content=chunk_text,
                token_count=len(chunk_tokens),
                start_char=start_char,
                end_char=end_char,
            )

            chunks.append(chunk)
            chunk_index += 1
            
            # Move to next chunk position
            i += step_size
            
            # Break if we've reached the end
            if chunk_end >= total_tokens:
                break

        logger.info(
            f"Chunked {document.filename}: {total_tokens} tokens → {len(chunks)} chunks (overlap: {self.chunk_overlap})"
        )
        return chunks
