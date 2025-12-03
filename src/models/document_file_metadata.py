"""Document file metadata model for file management interface."""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass
class DocumentFileMetadata:
    """Represents file information for the file management interface.

    Attributes:
        filename: Name of the document file (e.g., "report.pdf")
        file_path: Full path to file in data/documents/
        file_type: Document type based on extension (PDF, TXT, MD, DOCX)
        file_size_bytes: File size in bytes
        file_size_display: Human-readable size (e.g., "1.5 MB")
        is_embedded: Whether file has chunks in ChromaDB
        embedding_status: Display status for UI ("✓ Embedded" or "⏳ Pending")
        last_modified: File system modification timestamp
        upload_timestamp: When uploaded via UI (None for pre-existing files)
        chunk_count: Number of chunks if embedded, else 0
    """

    filename: str
    file_path: Path
    file_type: str  # PDF, TXT, MD, DOCX
    file_size_bytes: int
    file_size_display: str
    is_embedded: bool
    embedding_status: str  # "✓ Embedded" or "⏳ Pending"
    last_modified: datetime
    upload_timestamp: Optional[datetime]
    chunk_count: int

    def __post_init__(self):
        """Validate metadata values after initialization."""
        if not self.filename:
            raise ValueError("filename cannot be empty")
        if self.file_type not in ("PDF", "TXT", "MD", "DOCX"):
            raise ValueError(f"file_type must be PDF, TXT, MD, or DOCX, got: {self.file_type}")
        if self.file_size_bytes < 0:
            raise ValueError("file_size_bytes cannot be negative")
        if self.chunk_count < 0:
            raise ValueError("chunk_count cannot be negative")
        if self.embedding_status not in ("✓ Embedded", "⏳ Pending"):
            raise ValueError(f"embedding_status must be '✓ Embedded' or '⏳ Pending', got: {self.embedding_status}")
        # Validate consistency: if embedded, chunk_count should be > 0
        if self.is_embedded and self.chunk_count == 0:
            raise ValueError("If is_embedded is True, chunk_count must be > 0")
