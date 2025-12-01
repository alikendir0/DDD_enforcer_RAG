"""
Chunker service for splitting documents into fixed-size token chunks.
"""
from typing import List

import tiktoken

from src.models.document import Document, Chunk
from src.utils.logger import get_logger
from config.settings import CHUNK_SIZE

logger = get_logger(__name__)


class Chunker:
    """Handles splitting documents into fixed-size token chunks."""

    def __init__(self, chunk_size: int = CHUNK_SIZE):
        """
        Initialize chunker with tiktoken encoding.

        Args:
            chunk_size: Maximum tokens per chunk (default: 512)
        """
        self.chunk_size = chunk_size
        # Use cl100k_base encoding (used by GPT-4, compatible tokenizer)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        logger.info(f"Chunker initialized with chunk_size={chunk_size}")

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Split document content into 512-token chunks.

        Args:
            document: Document object with content to chunk

        Returns:
            List of Chunk objects
        """
        if not document.content:
            logger.warning(f"Empty document: {document.filename}")
            return []

        # Tokenize the entire content
        tokens = self.encoding.encode(document.content)
        total_tokens = len(tokens)

        chunks = []
        chunk_index = 0

        # Split into fixed-size chunks (no overlap)
        for i in range(0, total_tokens, self.chunk_size):
            chunk_tokens = tokens[i : i + self.chunk_size]

            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Find character positions in original text
            # This is approximate since token boundaries don't align with char boundaries
            start_char = len(self.encoding.decode(tokens[:i]))
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

        logger.info(
            f"Chunked {document.filename}: {total_tokens} tokens → {len(chunks)} chunks"
        )
        return chunks
