"""Statistics tracking service for monitoring token usage and costs."""

import time
from typing import Dict, Optional
from src.models.session_statistics import SessionStatistics
from config.model_pricing import get_model_price
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StatsTracker:
    """Tracks and formats statistics for user sessions.

    Stores session statistics in-memory (destroyed on server restart).
    """

    def __init__(self, vector_store=None):
        """Initialize stats tracker with optional vector store for DB queries.

        Args:
            vector_store: Vector store instance for querying file/chunk counts
        """
        self.sessions: Dict[str, SessionStatistics] = {}
        self.vector_store = vector_store
        self.successful_retrievals = 0
        self.failed_retrievals = 0
        logger.info("StatsTracker initialized")

    def track_query_stats(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int,
        model_name: str = "gemini-2.5-flash"
    ) -> SessionStatistics:
        """Track query statistics and update session data.

        Args:
            session_id: Browser session identifier
            input_tokens: Input tokens used in query
            output_tokens: Output tokens generated
            model_name: AI model name for pricing lookup

        Returns:
            Updated SessionStatistics object

        Raises:
            ValueError: If token counts are negative
        """
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionStatistics(session_id=session_id)
            logger.info(f"Created new session: {session_id}")

        session = self.sessions[session_id]

        # Update token counts
        session.total_input_tokens += input_tokens
        session.total_output_tokens += output_tokens
        session.query_count += 1

        # Calculate cost
        pricing = get_model_price(model_name)
        input_cost = (input_tokens / 1_000_000) * pricing["input_price_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_price_per_million"]
        session.total_cost += input_cost + output_cost

        # Update database metrics
        session.embedded_file_count = self._get_embedded_file_count()
        session.total_chunk_count = self._get_total_chunk_count()

        # Update timestamp
        session.last_updated = time.time()

        logger.debug(
            f"Session {session_id}: {session.query_count} queries, "
            f"{session.total_input_tokens + session.total_output_tokens} total tokens, "
            f"${session.total_cost:.6f} cost"
        )

        return session

    def get_session_stats(self, session_id: str) -> Optional[SessionStatistics]:
        """Get statistics for a specific session.

        Args:
            session_id: Browser session identifier

        Returns:
            SessionStatistics object or None if session doesn't exist
        """
        return self.sessions.get(session_id)

    def format_stats_for_display(self, session_id: str) -> Dict[str, str]:
        """Format session statistics for UI display.

        Args:
            session_id: Browser session identifier

        Returns:
            Dictionary with formatted statistics for display
        """
        session = self.get_session_stats(session_id)

        if not session:
            return {
                "status": "No session data",
                "query_count": "0 queries",
                "total_tokens": "0 tokens",
                "input_tokens": "0 tokens",
                "output_tokens": "0 tokens",
                "average_tokens_per_query": "0 tokens/query",
                "total_cost": "$0.0000",
                "embedded_files": "0 files",
                "total_chunks": "0 chunks",
                "session_duration": "0s"
            }

        return {
            "status": "Active session",
            "query_count": f"{session.query_count} queries",
            "total_tokens": f"{session.total_input_tokens + session.total_output_tokens:,} tokens",
            "input_tokens": f"{session.total_input_tokens:,} tokens",
            "output_tokens": f"{session.total_output_tokens:,} tokens",
            "average_tokens_per_query": f"{session.average_tokens_per_query:.1f} tokens/query",
            "total_cost": f"${session.total_cost:.6f}",
            "embedded_files": f"{session.embedded_file_count} files",
            "total_chunks": f"{session.total_chunk_count} chunks",
            "session_duration": f"{session.session_duration:.0f}s",
            "retrieval_success_rate": f"{self._get_retrieval_success_rate():.1f}%"
        }

    def _get_embedded_file_count(self) -> int:
        """Get count of files with embeddings in ChromaDB.

        Returns:
            Number of embedded files, or 0 if vector store unavailable
        """
        if not self.vector_store:
            logger.warning("Vector store not available, returning 0 for embedded_file_count")
            return 0

        try:
            # Query unique document names from metadata
            results = self.vector_store.collection.get(
                include=['metadatas']
            )

            if not results or 'metadatas' not in results:
                return 0

            # Extract unique document names
            document_names = set()
            for metadata in results['metadatas']:
                if metadata and 'document_name' in metadata:
                    document_names.add(metadata['document_name'])

            return len(document_names)

        except Exception as e:
            logger.error(f"Failed to get embedded file count: {e}")
            return 0

    def _get_total_chunk_count(self) -> int:
        """Get total count of chunks in ChromaDB.

        Returns:
            Number of chunks, or 0 if vector store unavailable
        """
        if not self.vector_store:
            logger.warning("Vector store not available, returning 0 for total_chunk_count")
            return 0

        try:
            # Get total count from collection
            count = self.vector_store.collection.count()
            return count

        except Exception as e:
            logger.error(f"Failed to get total chunk count: {e}")
            return 0

    def track_retrieval_quality(self, success: bool):
        """Track successful vs failed retrieval attempts.

        Args:
            success: Whether the retrieval was successful
        """
        if success:
            self.successful_retrievals += 1
        else:
            self.failed_retrievals += 1

    def _get_retrieval_success_rate(self) -> float:
        """Calculate retrieval success rate.

        Returns:
            Success rate as percentage (0-100)
        """
        total = self.successful_retrievals + self.failed_retrievals
        if total == 0:
            return 100.0
        return (self.successful_retrievals / total) * 100
