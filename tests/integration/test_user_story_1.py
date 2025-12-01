"""
Integration tests for User Story 1: Basic Chatbot Interaction

Tests the acceptance scenarios:
- T027: Question covered in documents
- T028: Question not in documents
- T029: Empty/malformed query
"""
import os
import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import initialize_services, index_documents, answer_query
from config.settings import GEMINI_API_KEY


@pytest.fixture(scope="module")
def setup_system():
    """
    Setup fixture: Initialize services and index sample documents.

    This runs once before all tests in this module.
    """
    # Skip tests if no API key is available
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set - skipping integration tests")

    # Initialize all services
    initialize_services()

    # Index the sample test documents
    sample_docs_path = Path(__file__).parent.parent / "fixtures" / "sample_documents"

    if not sample_docs_path.exists():
        pytest.skip(f"Sample documents not found at {sample_docs_path}")

    # Index documents
    status = index_documents(str(sample_docs_path))

    # Verify indexing was successful
    assert status.indexed_documents > 0, "Failed to index any documents"
    assert status.total_chunks > 0, "No chunks were created"

    print(f"\nIndexing complete: {status.indexed_documents} docs, {status.total_chunks} chunks")

    yield status

    # Cleanup (if needed)
    pass


class TestUserStory1:
    """
    Test User Story 1: Basic Chatbot Interaction

    Acceptance Scenarios:
    1. Question covered in documents → response includes document context
    2. Question not in documents → response uses general knowledge
    3. Empty/malformed query → helpful error message
    """

    def test_t027_question_covered_in_documents(self, setup_system):
        """
        T027: Test US1 acceptance scenario 1

        Given: Chatbot is running and documents are indexed
        When: User asks question about topic in documents
        Then: Response includes information from relevant documents

        Sample documents cover:
        - Machine Learning (supervised, unsupervised, reinforcement learning)
        - Python Programming (syntax, data structures, libraries)
        - Databases (relational, NoSQL, vector databases)
        """
        # Ask question about machine learning (covered in sample1.txt)
        query = "What are the three main types of machine learning?"
        response = answer_query(query)

        # Verify we got a response
        assert response, "No response received"
        assert len(response) > 0, "Empty response received"

        # Verify response is not an error message
        assert "error" not in response.lower() or "Error" not in response, \
            f"Got error response: {response}"
        assert "Please index documents first" not in response, \
            "System indicated documents not indexed"

        # Verify response mentions the three types of ML
        # The response should include context from the document
        response_lower = response.lower()

        # Check for key concepts from the document
        has_supervised = "supervised" in response_lower
        has_unsupervised = "unsupervised" in response_lower
        has_reinforcement = "reinforcement" in response_lower

        # At least 2 of the 3 types should be mentioned
        types_mentioned = sum([has_supervised, has_unsupervised, has_reinforcement])
        assert types_mentioned >= 2, \
            f"Response doesn't include ML types from document. Response: {response}"

        print(f"\n✓ T027 PASS: Question about ML types answered with document context")
        print(f"  Query: {query}")
        print(f"  Response length: {len(response)} chars")
        print(f"  Types mentioned: {types_mentioned}/3")

    def test_t028_question_not_in_documents(self, setup_system):
        """
        T028: Test US1 acceptance scenario 2

        Given: Chatbot is running
        When: User asks question not covered in documents
        Then: Response uses general knowledge from language model

        Sample documents don't cover topics like:
        - Quantum computing
        - Ancient history
        - Cooking recipes
        """
        # Ask question not in any sample document
        query = "What is the capital of France?"
        response = answer_query(query)

        # Verify we got a response
        assert response, "No response received"
        assert len(response) > 0, "Empty response received"

        # Verify response is not an error message
        assert "error" not in response.lower() or "Error" not in response, \
            f"Got error response: {response}"

        # Verify the response answers the question
        # Should mention Paris
        response_lower = response.lower()
        assert "paris" in response_lower, \
            f"Response doesn't answer basic geography question. Response: {response}"

        print(f"\n✓ T028 PASS: Question not in docs answered with general knowledge")
        print(f"  Query: {query}")
        print(f"  Response includes correct answer: Paris")

    def test_t029_empty_or_malformed_query(self, setup_system):
        """
        T029: Test US1 acceptance scenario 3

        Given: Chatbot is running
        When: User sends empty or malformed query
        Then: Helpful error message or prompt for valid question

        Test cases:
        - Empty string
        - Only whitespace
        - Very short input
        """
        # Test 1: Empty string
        response_empty = answer_query("")
        assert response_empty, "No response for empty query"
        assert len(response_empty) > 0, "Empty response for empty query"

        # Should be a helpful prompt, not a crash
        assert "Please enter" in response_empty or "question" in response_empty.lower(), \
            f"Empty query response not helpful: {response_empty}"

        # Test 2: Only whitespace
        response_whitespace = answer_query("   \n\t  ")
        assert response_whitespace, "No response for whitespace query"
        assert "Please enter" in response_whitespace or "question" in response_whitespace.lower(), \
            f"Whitespace query response not helpful: {response_whitespace}"

        # Test 3: Just a few characters (should still work, not an error)
        response_short = answer_query("hi")
        assert response_short, "No response for short query"
        # Short queries should get a response, not necessarily an error
        # Just verify we got something back

        print(f"\n✓ T029 PASS: Empty/malformed queries handled gracefully")
        print(f"  Empty string: {response_empty[:50]}...")
        print(f"  Whitespace: {response_whitespace[:50]}...")
        print(f"  Short input: Got response")


class TestUserStory1EdgeCases:
    """
    Additional edge case tests for robustness
    """

    def test_query_with_special_characters(self, setup_system):
        """Test that queries with special characters are handled"""
        query = "What is machine learning? (please explain!)"
        response = answer_query(query)

        assert response, "No response for query with special chars"
        assert "error" not in response.lower() or "Error" not in response

        print(f"\n✓ Special characters handled")

    def test_very_long_query(self, setup_system):
        """Test that very long queries are handled"""
        # Create a long but valid query
        query = "Can you please explain " + "in great detail " * 10 + \
                "what machine learning is and how it works?"
        response = answer_query(query)

        assert response, "No response for long query"
        assert len(response) > 0

        print(f"\n✓ Long query handled (query length: {len(query)} chars)")


if __name__ == "__main__":
    """
    Run tests directly for manual testing/debugging.

    Usage:
        python tests/integration/test_user_story_1.py

    Or with pytest:
        pytest tests/integration/test_user_story_1.py -v
    """
    pytest.main([__file__, "-v", "-s"])
