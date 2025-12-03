"""Session statistics data model for tracking token usage and costs."""

from dataclasses import dataclass, field
import time
from typing import Optional


@dataclass
class SessionStatistics:
    """Tracks token usage, costs, and query metrics for a single browser session.

    Attributes:
        session_id: Browser session identifier (Gradio session hash)
        total_input_tokens: Cumulative input tokens across all queries
        total_output_tokens: Cumulative output tokens across all queries
        total_cost: Estimated total cost in USD for session
        query_count: Number of queries processed in session
        embedded_file_count: Current count of files with embeddings in ChromaDB
        total_chunk_count: Current count of chunks stored in vector database
        start_time: Session start time (Unix timestamp)
        last_updated: Time of last statistics update (Unix timestamp)
    """

    session_id: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    query_count: int = 0
    embedded_file_count: int = 0
    total_chunk_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate statistics values after initialization."""
        if self.total_input_tokens < 0:
            raise ValueError("total_input_tokens cannot be negative")
        if self.total_output_tokens < 0:
            raise ValueError("total_output_tokens cannot be negative")
        if self.total_cost < 0.0:
            raise ValueError("total_cost cannot be negative")
        if self.query_count < 0:
            raise ValueError("query_count cannot be negative")
        if self.last_updated < self.start_time:
            raise ValueError("last_updated must be >= start_time")

    @property
    def average_tokens_per_query(self) -> float:
        """Calculate average tokens per query, or 0 if no queries."""
        if self.query_count == 0:
            return 0.0
        total_tokens = self.total_input_tokens + self.total_output_tokens
        return total_tokens / self.query_count

    @property
    def session_duration(self) -> float:
        """Calculate session duration in seconds."""
        return time.time() - self.start_time
