"""UI configuration data model for RAG parameters."""

from dataclasses import dataclass, field
import time


@dataclass
class UIConfiguration:
    """Stores user-configurable RAG parameters.

    Attributes:
        top_k: Number of chunks to retrieve per query (1-10)
        chunk_size: Token count per document chunk (256-1024)
        chunk_overlap: Overlapping tokens between chunks (0-256)
        show_context_enabled: Whether to show retrieval context by default
        last_modified: When configuration was last changed (Unix timestamp)
    """

    top_k: int = 3
    chunk_size: int = 512
    chunk_overlap: int = 0
    show_context_enabled: bool = False
    last_modified: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate configuration values after initialization."""
        if not (1 <= self.top_k <= 10):
            raise ValueError("top_k must be between 1 and 10 (inclusive)")
        if not (256 <= self.chunk_size <= 1024):
            raise ValueError("chunk_size must be between 256 and 1024 (inclusive)")
        if not (0 <= self.chunk_overlap <= 256):
            raise ValueError("chunk_overlap must be between 0 and 256 (inclusive)")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
