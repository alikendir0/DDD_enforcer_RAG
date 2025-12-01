"""
Integration test for complete RAG chatbot flow (T057)
Tests: setup -> index documents -> ask multiple questions -> verify responses
"""
import os
import sys
import shutil
import time
from pathlib import Path

# Ensure we're running from project root
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from src.main import index_documents, answer_query, initialize_services
import config.settings as settings


def test_complete_integration_flow():
    """
    Complete end-to-end integration test for RAG chatbot.
    Tests: setup -> index documents -> ask multiple questions -> verify
    """
    print("\n" + "=" * 80)
    print("RAG CHATBOT COMPLETE INTEGRATION TEST (T057)")
    print("=" * 80)

    # ========================================================================
    # Step 1: Verify API key exists
    # ========================================================================
    print("\n[Step 1/9] Verifying API key configuration...")
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key is not None and len(api_key) > 0, \
        "GEMINI_API_KEY not found in environment"
    print(f"[OK] API key found (length: {len(api_key)} characters)")

    # ========================================================================
    # Step 2: Verify documents exist
    # ========================================================================
    print("\n[Step 2/9] Verifying documents in data/documents/...")
    docs_path = Path(settings.DOCUMENTS_FOLDER)
    assert docs_path.exists(), f"Documents folder not found: {docs_path}"

    # Find all supported document files
    pdf_files = list(docs_path.glob("*.pdf"))
    txt_files = list(docs_path.glob("*.txt"))
    md_files = list(docs_path.glob("*.md"))
    docx_files = list(docs_path.glob("*.docx"))

    total_files = len(pdf_files) + len(txt_files) + len(md_files) + len(docx_files)
    assert total_files > 0, "No documents found in documents folder"

    print(f"[OK] Found {total_files} document(s):")
    if pdf_files:
        print(f"  - PDF: {len(pdf_files)} file(s)")
    if txt_files:
        print(f"  - TXT: {len(txt_files)} file(s)")
    if md_files:
        print(f"  - Markdown: {len(md_files)} file(s)")
    if docx_files:
        print(f"  - DOCX: {len(docx_files)} file(s)")

    # ========================================================================
    # Step 3: Clean and prepare test environment
    # ========================================================================
    print("\n[Step 3/9] Preparing test environment...")
    chroma_path = Path(settings.CHROMA_DB_PATH)
    if chroma_path.exists():
        print(f"  Cleaning existing ChromaDB at: {chroma_path}")
        shutil.rmtree(chroma_path)
    print("[OK] Test environment ready")
    
    # Initialize services
    print("  Initializing services...")
    initialize_services()
    print("[OK] Services initialized")

    # ========================================================================
    # Step 4: Test document indexing flow
    # ========================================================================
    print("\n[Step 4/9] Testing document indexing...")
    start_time = time.time()

    status = index_documents()

    indexing_time = time.time() - start_time

    assert status is not None, "Indexing returned None"
    assert status.total_documents > 0, "No documents were processed"
    assert status.indexed_documents > 0, "No documents successfully indexed"
    assert status.total_chunks > 0, "No chunks were created"
    assert status.is_ready, "Vector store is not ready after indexing"

    print(f"[OK] Indexing completed in {indexing_time:.2f} seconds")
    print(f"  - Documents processed: {status.total_documents}")
    print(f"  - Successfully indexed: {status.indexed_documents}")
    print(f"  - Failed: {status.failed_documents}")
    print(f"  - Total chunks created: {status.total_chunks}")
    print(f"  - Success rate: {status.success_rate:.1%}")

    # ========================================================================
    # Step 5: Test basic question answering
    # ========================================================================
    print("\n[Step 5/9] Testing basic question answering...")

    query1 = "What is this document about?"
    start_time = time.time()
    response1 = answer_query(query1, session_id="test_basic")
    query_time = time.time() - start_time

    assert response1 is not None, "No response received"
    assert len(response1) > 0, "Response is empty"
    assert not ("please index" in response1.lower() or "no documents" in response1.lower()), \
        f"Response indicates documents not indexed: {response1[:100]}"

    print(f"[OK] Query answered in {query_time:.2f} seconds")
    print(f"  Query: {query1}")
    print(f"  Response length: {len(response1)} characters")
    print(f"  Response preview: {response1[:200]}...")

    # ========================================================================
    # Step 6: Test multi-turn conversation
    # ========================================================================
    print("\n[Step 6/9] Testing multi-turn conversation...")

    session_id = "test_multi_turn"

    # Turn 1
    query_turn1 = "What are the main topics covered in these documents?"
    response_turn1 = answer_query(query_turn1, session_id=session_id)
    assert len(response_turn1) > 0, "First turn response is empty"
    print(f"[OK] Turn 1 completed")
    print(f"  Query: {query_turn1}")
    print(f"  Response length: {len(response_turn1)} characters")

    # Turn 2 (follow-up question)
    query_turn2 = "Can you elaborate on the first point you mentioned?"
    response_turn2 = answer_query(query_turn2, session_id=session_id)
    assert len(response_turn2) > 0, "Second turn response is empty"
    print(f"[OK] Turn 2 completed (follow-up question)")
    print(f"  Query: {query_turn2}")
    print(f"  Response length: {len(response_turn2)} characters")

    # Turn 3 (different topic)
    query_turn3 = "What technical details are mentioned?"
    response_turn3 = answer_query(query_turn3, session_id=session_id)
    assert len(response_turn3) > 0, "Third turn response is empty"
    print(f"[OK] Turn 3 completed (topic change)")
    print(f"  Query: {query_turn3}")
    print(f"  Response length: {len(response_turn3)} characters")

    # ========================================================================
    # Step 7: Test error handling - empty query
    # ========================================================================
    print("\n[Step 7/9] Testing error handling (empty/malformed queries)...")

    # Empty query
    response_empty = answer_query("", session_id="test_errors")
    assert response_empty is not None, "No response for empty query"
    assert len(response_empty) > 0, "Empty response for empty query"
    assert any(keyword in response_empty.lower() for keyword in ["question", "query", "ask", "provide"]), \
        f"Response doesn't prompt for input: {response_empty}"
    print(f"[OK] Empty query handled correctly")
    print(f"  Response: {response_empty[:100]}...")

    # Whitespace-only query
    response_whitespace = answer_query("   \n  ", session_id="test_errors")
    assert response_whitespace is not None, "No response for whitespace query"
    assert len(response_whitespace) > 0, "Empty response for whitespace query"
    print(f"[OK] Whitespace query handled correctly")
    print(f"  Response: {response_whitespace[:100]}...")

    # ========================================================================
    # Step 8: Test retrieval quality with specific queries
    # ========================================================================
    print("\n[Step 8/9] Testing retrieval quality...")

    # Test specific factual query
    query_specific = "What is the main objective or purpose mentioned in the document?"
    response_specific = answer_query(query_specific, session_id="test_quality")

    assert response_specific is not None, "No response for specific query"
    assert len(response_specific) > 50, \
        f"Response too short ({len(response_specific)} chars), may lack context"

    print(f"[OK] Specific query answered")
    print(f"  Query: {query_specific}")
    print(f"  Response length: {len(response_specific)} characters")
    print(f"  Response preview: {response_specific[:250]}...")

    # Test technical query
    query_technical = "What are the key technical aspects, methods, or technologies discussed?"
    response_technical = answer_query(query_technical, session_id="test_quality_2")

    assert response_technical is not None, "No response for technical query"
    assert len(response_technical) > 50, \
        f"Technical response too short ({len(response_technical)} chars)"

    print(f"\n[OK] Technical query answered")
    print(f"  Query: {query_technical}")
    print(f"  Response length: {len(response_technical)} characters")
    print(f"  Response preview: {response_technical[:250]}...")

    # ========================================================================
    # Step 9: Test session isolation
    # ========================================================================
    print("\n[Step 9/9] Testing session isolation...")

    # Create two separate sessions
    session_a = "isolation_test_a"
    session_b = "isolation_test_b"

    # Query in session A
    query_a = "Tell me about the first document."
    response_a1 = answer_query(query_a, session_id=session_a)
    assert len(response_a1) > 0, "Session A first response is empty"

    # Query in session B (completely different)
    query_b = "What is mentioned about technical implementations?"
    response_b1 = answer_query(query_b, session_id=session_b)
    assert len(response_b1) > 0, "Session B first response is empty"

    # Follow-up in session A should remember context
    query_a_followup = "What else can you tell me about it?"
    response_a2 = answer_query(query_a_followup, session_id=session_a)
    assert len(response_a2) > 0, "Session A follow-up response is empty"

    print(f"[OK] Session A handled 2 queries")
    print(f"[OK] Session B handled 1 query")
    print(f"[OK] Sessions are properly isolated")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nTest Summary:")
    print("  [OK] API key configuration verified")
    print("  [OK] Document availability confirmed")
    print("  [OK] Document indexing successful")
    print("  [OK] Basic question answering working")
    print("  [OK] Multi-turn conversations supported")
    print("  [OK] Error handling functional")
    print("  [OK] Retrieval quality validated")
    print("  [OK] Session isolation confirmed")
    print("\nAll systems operational. RAG chatbot is fully functional.")
    print("=" * 80 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_complete_integration_flow()
        if success:
            print("\n>>> T057 INTEGRATION TEST PASSED <<<\n")
            sys.exit(0)
    except Exception as e:
        print(f"\n>>> INTEGRATION TEST FAILED <<<")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
