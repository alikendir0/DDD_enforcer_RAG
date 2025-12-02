"""
Data models for queries, responses, and conversations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


@dataclass
class Query:
    """Represents a user's question submitted to the chatbot."""

    query_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    retrieval_scores: list[float] = field(default_factory=list)
    retrieval_count: int = 0
    response_id: Optional[str] = None

    def __post_init__(self):
        """Validate query data."""
        if self.content:
            self.content = self.content.strip()
        if self.retrieval_count < 0 or self.retrieval_count > 5:
            raise ValueError("Retrieval count must be between 0 and 5")
        if len(self.retrieved_chunk_ids) != len(self.retrieval_scores):
            raise ValueError("Retrieved chunks and scores must have same length")
        if self.retrieval_scores and not all(
            0.0 <= score <= 1.0 for score in self.retrieval_scores
        ):
            raise ValueError("Retrieval scores must be between 0.0 and 1.0")


@dataclass
class Response:
    """Represents the chatbot's generated answer."""

    response_id: str = field(default_factory=lambda: str(uuid4()))
    query_id: str = ""
    content: str = ""
    model_name: str = "gemini-2.5-flash"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: int = 0
    token_count: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        """Validate response data."""
        if self.error is None and not self.content:
            raise ValueError("Content cannot be empty when error is None")
        if self.latency_ms < 0:
            raise ValueError("Latency must be non-negative")
        if self.token_count < 0:
            raise ValueError("Token count must be non-negative")


@dataclass
class Conversation:
    """Represents a session of queries and responses."""

    session_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self):
        """Validate conversation data."""
        if self.last_activity < self.started_at:
            raise ValueError("Last activity cannot be before start time")
        # Validate message structure
        for msg in self.messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Messages must have 'role' and 'content' fields")
            if msg["role"] not in ["user", "assistant"]:
                raise ValueError("Message role must be 'user' or 'assistant'")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        if role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")

        self.messages.append({"role": role, "content": content})
        self.message_count = len(self.messages)
        self.last_activity = datetime.utcnow()

        # Keep only last 10 messages (max conversation window)
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
            self.message_count = len(self.messages)

    def get_history(self) -> list[dict]:
        """Get conversation history (last 10 messages)."""
        return self.messages[-10:]


@dataclass
class QueryMetrics:
    """Performance and usage metrics for a single query/response cycle."""

    embedding_time_ms: int = 0
    retrieval_time_ms: int = 0
    generation_time_ms: int = 0
    total_time_ms: int = 0
    retrieved_chunks: int = 0
    average_score: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if self.embedding_time_ms < 0:
            raise ValueError("embedding_time_ms must be non-negative")
        if self.retrieval_time_ms < 0:
            raise ValueError("retrieval_time_ms must be non-negative")
        if self.generation_time_ms < 0:
            raise ValueError("generation_time_ms must be non-negative")
        if self.total_time_ms < 0:
            raise ValueError("total_time_ms must be non-negative")
        if self.retrieved_chunks < 0:
            raise ValueError("retrieved_chunks must be non-negative")
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise ValueError("Token counts must be non-negative")
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")


@dataclass
class IndexingMetrics:
    """Performance metrics for a document indexing run."""

    duration_ms: int = 0
    document_count: int = 0
    total_bytes: int = 0
    total_extracted_chars: int = 0

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.document_count < 0 or self.total_bytes < 0 or self.total_extracted_chars < 0:
            raise ValueError("Indexing aggregate values must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize indexing metrics for UI/logging."""
        return {
            "duration_ms": self.duration_ms,
            "document_count": self.document_count,
            "total_bytes": self.total_bytes,
            "total_extracted_chars": self.total_extracted_chars,
        }


    
