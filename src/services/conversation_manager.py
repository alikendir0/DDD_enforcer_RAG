"""
Conversation history management service.

Manages conversation history for multi-turn dialogues.
Implements in-memory storage with configurable message window.
"""
from typing import Dict, List, Optional
from datetime import datetime

from src.models.conversation import Conversation
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """
    Manages conversation history across sessions.

    Stores conversations in-memory with automatic trimming to max window size.
    Each session maintains an independent conversation history.
    """

    def __init__(self, max_messages: int = 10):
        """
        Initialize the conversation manager.

        Args:
            max_messages: Maximum number of messages to keep in history (default: 10)
                         This includes both user messages and assistant responses.
        """
        self.conversations: Dict[str, Conversation] = {}
        self.max_messages = max_messages
        logger.info(f"ConversationManager initialized with max_messages={max_messages}")

    def get_or_create_conversation(self, session_id: str) -> Conversation:
        """
        Get existing conversation or create new one for session.

        Args:
            session_id: Unique session identifier

        Returns:
            Conversation object for this session
        """
        if session_id not in self.conversations:
            logger.info(f"Creating new conversation for session: {session_id}")
            self.conversations[session_id] = Conversation(session_id=session_id)

        return self.conversations[session_id]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Automatically trims history to max_messages after adding.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content text
        """
        conversation = self.get_or_create_conversation(session_id)

        # Add message
        conversation.messages.append({
            "role": role,
            "content": content
        })
        conversation.message_count = len(conversation.messages)
        conversation.last_activity = datetime.utcnow()

        # Trim to max window
        self._trim_history(session_id)

        logger.debug(
            f"Added {role} message to session {session_id}. "
            f"Total messages: {conversation.message_count}"
        )

    def get_conversation_history(
        self, session_id: str, max_messages: Optional[int] = None
    ) -> List[dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            max_messages: Optional override for max messages to return

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        conversation = self.get_or_create_conversation(session_id)

        if max_messages is not None:
            return conversation.messages[-max_messages:]

        return conversation.messages.copy()

    def clear_conversation(self, session_id: str) -> None:
        """
        Clear conversation history for a session.

        Args:
            session_id: Session identifier to clear
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation for session: {session_id}")

    def _trim_history(self, session_id: str) -> None:
        """
        Trim conversation history to max_messages limit.

        Keeps only the most recent messages, discarding older ones.

        Args:
            session_id: Session to trim
        """
        conversation = self.conversations[session_id]

        if len(conversation.messages) > self.max_messages:
            removed_count = len(conversation.messages) - self.max_messages
            conversation.messages = conversation.messages[-self.max_messages:]
            conversation.message_count = len(conversation.messages)

            logger.debug(
                f"Trimmed {removed_count} messages from session {session_id}. "
                f"Remaining: {conversation.message_count}"
            )

    def get_session_count(self) -> int:
        """
        Get the number of active sessions.

        Returns:
            Number of sessions being tracked
        """
        return len(self.conversations)
