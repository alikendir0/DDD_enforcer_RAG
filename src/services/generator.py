"""
Generator service for creating responses using Gemini API.
"""
import time
from typing import List, Optional

import google.generativeai as genai

from src.models.document import Chunk
from src.models.conversation import Response
from src.utils.logger import get_logger
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

logger = get_logger(__name__)


class GeneratorError(Exception):
    """Raised when response generation fails."""

    pass


class Generator:
    """Handles response generation using Gemini API."""

    def __init__(self, api_key: Optional[str] = GEMINI_API_KEY):
        """
        Initialize generator with Gemini API.

        Args:
            api_key: Gemini API key from environment

        Raises:
            ValueError: If API key is missing or invalid
        """
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        self.api_key = api_key
        self.model_name = GEMINI_MODEL

        # Configure Gemini API
        genai.configure(api_key=self.api_key)  # type: ignore
        self.model = genai.GenerativeModel(self.model_name)  # type: ignore

        logger.info(f"Generator initialized with model: {self.model_name}")

    def generate_response(
        self,
        query: str,
        context_chunks: List[Chunk],
        conversation_history: Optional[List[dict]] = None,
    ) -> Response:
        """
        Generate response using Gemini API with context.

        Args:
            query: User's question
            context_chunks: Retrieved document chunks for context
            conversation_history: Previous messages (for multi-turn)

        Returns:
            Response object with generated answer

        Raises:
            GeneratorError: If API call fails after retries
        """
        start_time = time.time()

        try:
            # Build prompt with context
            prompt = self._build_prompt(query, context_chunks, conversation_history)

            # Call Gemini API with retry logic
            response_text = self._call_gemini_with_retry(prompt)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Estimate token count (rough approximation)
            token_count = len(response_text.split())

            response = Response(
                query_id="",  # Will be set by caller
                content=response_text,
                model_name=self.model_name,
                latency_ms=latency_ms,
                token_count=token_count,
                error=None,
            )

            logger.info(
                f"Generated response: {len(response_text)} chars, "
                f"{latency_ms}ms latency"
            )

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Failed to generate response: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Return error response
            return Response(
                query_id="",
                content="I apologize, but I encountered an error generating a response. Please try again.",
                model_name=self.model_name,
                latency_ms=latency_ms,
                token_count=0,
                error=error_msg,
            )

    def _build_prompt(
        self,
        query: str,
        context_chunks: List[Chunk],
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """
        Build prompt with context chunks and conversation history.

        Args:
            query: User's question
            context_chunks: Retrieved chunks for context
            conversation_history: Previous messages

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add system instruction
        prompt_parts.append(
            "You are a helpful assistant that answers questions based on the provided context. "
            "If the context contains relevant information, use it in your answer. "
            "If the context doesn't contain relevant information, answer using your general knowledge "
            "and mention that the information isn't in the provided documents."
        )

        # Add context chunks
        if context_chunks:
            prompt_parts.append("\n\nContext from documents:")
            for i, chunk in enumerate(context_chunks, 1):
                prompt_parts.append(
                    f"\n--- Document excerpt {i} (from {chunk.document_path}) ---"
                )
                prompt_parts.append(chunk.content)

        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("\n\nConversation history:")
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"\n{role.capitalize()}: {content}")

        # Add current query
        prompt_parts.append(f"\n\nCurrent question: {query}")
        prompt_parts.append("\nAnswer:")

        return "".join(prompt_parts)

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Gemini API with exponential backoff retry.

        Handles rate limiting and transient errors with automatic retry.

        Args:
            prompt: Formatted prompt
            max_retries: Maximum number of retry attempts

        Returns:
            Generated response text

        Raises:
            GeneratorError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)

                if not response or not response.text:
                    raise GeneratorError("Empty response from Gemini API")

                return response.text

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error
                is_rate_limit = any(
                    keyword in error_str
                    for keyword in ["rate limit", "quota", "too many requests", "429"]
                )

                if attempt < max_retries - 1:
                    # Use longer backoff for rate limits
                    if is_rate_limit:
                        wait_time = 2 ** (attempt + 2)  # 4s, 8s, 16s for rate limits
                        logger.warning(
                            f"Rate limit encountered (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s"
                        )
                    else:
                        wait_time = 2**attempt  # Standard exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"Gemini API call failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                    time.sleep(wait_time)
                else:
                    if is_rate_limit:
                        logger.error(
                            f"Rate limit exceeded after {max_retries} attempts. "
                            "Please wait a few minutes and try again."
                        )
                    else:
                        logger.error(
                            f"Gemini API call failed after {max_retries} attempts: {e}"
                        )

        # Provide user-friendly error message for rate limits
        if last_error and "rate limit" in str(last_error).lower():
            raise GeneratorError(
                "API rate limit exceeded. Please wait a few minutes before trying again."
            )

        raise GeneratorError(f"Failed after {max_retries} retries: {last_error}")
