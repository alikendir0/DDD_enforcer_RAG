"""
Data models for queries, responses, and conversations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
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
