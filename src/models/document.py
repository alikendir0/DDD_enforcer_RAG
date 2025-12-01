"""
Data models for documents, chunks, and embeddings.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Document:
    """Represents a source file from the local corpus."""

    file_path: str
    filename: str
    format: str  # .txt, .md, .pdf, .docx
    size_bytes: int
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None
    chunk_count: int = 0
    status: str = "pending"  # pending, processing, indexed, failed
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate document data."""
        if self.format not in [".txt", ".md", ".pdf", ".docx"]:
            raise ValueError(f"Unsupported format: {self.format}")
        if self.size_bytes <= 0:
            raise ValueError("File size must be greater than 0")
        if self.status not in ["pending", "processing", "indexed", "failed"]:
            raise ValueError(f"Invalid status: {self.status}")


@dataclass
class Chunk:
    """Represents a fixed-size segment of a document."""

    chunk_id: str  # Format: {file_path}:{chunk_index}
    document_path: str
    chunk_index: int
    content: str
    token_count: int
    start_char: int
    end_char: int
    embedding: Optional[list[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate chunk data."""
        if self.chunk_index < 0:
            raise ValueError("Chunk index must be non-negative")
        if self.token_count <= 0 or self.token_count > 512:
            raise ValueError("Token count must be between 1 and 512")
        if self.start_char >= self.end_char:
            raise ValueError("Start char must be less than end char")
        if not self.content:
            raise ValueError("Content cannot be empty")
        if self.embedding is not None and len(self.embedding) != 384:
            raise ValueError("Embedding must be 384-dimensional")


@dataclass
class Embedding:
    """Represents a vector representation of a chunk."""

    chunk_id: str
    vector: list[float]
    model_name: str
    model_version: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate embedding data."""
        if len(self.vector) != 384:
            raise ValueError("Vector must be 384-dimensional")
        if not all(isinstance(v, (int, float)) for v in self.vector):
            raise ValueError("Vector must contain only numeric values")


@dataclass
class IndexingStatus:
    """Represents the current state of the document corpus index."""

    total_documents: int = 0
    indexed_documents: int = 0
    failed_documents: int = 0
    total_chunks: int = 0
    last_indexed: Optional[datetime] = None

    @property
    def is_ready(self) -> bool:
        """Check if index has at least one indexed document."""
        return self.indexed_documents > 0

    @property
    def success_rate(self) -> float:
        """Calculate indexing success rate."""
        if self.total_documents == 0:
            return 0.0
        return self.indexed_documents / self.total_documents
