"""Main entry point for the RAG Chatbot application."""
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.services.document_processor import DocumentProcessor, ParseError
from src.services.chunker import Chunker
from src.services.embedder import Embedder
from src.services.vector_store import VectorStore
from src.services.retriever import Retriever
from src.services.generator import Generator
from src.services.conversation_manager import ConversationManager
from src.models.document import IndexingStatus, Document
from src.models.conversation import Query, Response, QueryMetrics, IndexingMetrics
from src.utils.metrics_logger import metrics_logger
from src.utils.logger import get_logger
from config.settings import (
    GEMINI_API_KEY,
    DOCUMENTS_FOLDER,
    CHROMA_DB_PATH,
    TOP_K_DEFAULT,
)

logger = get_logger(__name__)

# Global service instances
embedder: Optional[Embedder] = None
vector_store: Optional[VectorStore] = None
retriever: Optional[Retriever] = None
generator: Optional[Generator] = None
conversation_manager: Optional[ConversationManager] = None


def initialize_services():
    """
    Initialize all core services.

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    global embedder, vector_store, retriever, generator, conversation_manager

    logger.info("Initializing RAG Chatbot services...")

    # Check API key
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please create a .env file with your API key (see .env.example)"
        )

    # Initialize embedder
    embedder = Embedder()

    # Initialize vector store
    vector_store = VectorStore()
    vector_store.initialize(persist_directory=str(CHROMA_DB_PATH))

    # Initialize retriever
    retriever = Retriever(embedder=embedder, vector_store=vector_store)

    # Initialize generator
    generator = Generator(api_key=GEMINI_API_KEY)

    # Initialize conversation manager (max 10 messages = 5 exchanges)
    conversation_manager = ConversationManager(max_messages=10)

    logger.info("All services initialized successfully")


def index_documents(documents_folder: Optional[str] = None) -> IndexingStatus:
    """
    Index all documents from the specified folder.

    Orchestrates:
    1. Load documents from folder
    2. Chunk documents
    3. Embed chunks
    4. Store embeddings in vector store

    Args:
        documents_folder: Path to folder containing documents (default: from settings)

    Returns:
        IndexingStatus with summary of indexing operation
    """
    global embedder, vector_store

    # Ensure services are initialized
    if vector_store is None or embedder is None:
        initialize_services()
    
    # Type assertions for Pylance
    assert embedder is not None
    assert vector_store is not None

    if documents_folder is None:
        documents_folder = str(DOCUMENTS_FOLDER)

    logger.info(f"Starting document indexing from: {documents_folder}")

    indexing_start = datetime.utcnow()

    # Verify folder exists
    folder_path = Path(documents_folder)
    if not folder_path.exists():
        logger.error(f"Documents folder not found: {documents_folder}")
        return IndexingStatus(
            total_documents=0,
            indexed_documents=0,
            failed_documents=0,
            total_chunks=0,
            last_indexed=None,
        )

    # Initialize processors
    doc_processor = DocumentProcessor()
    chunker = Chunker()

    # Load all documents
    logger.info("Loading documents from folder...")
    documents = doc_processor.load_documents_from_folder(documents_folder)

    if not documents:
        logger.warning("No documents found in folder")
        return IndexingStatus(
            total_documents=0,
            indexed_documents=0,
            failed_documents=0,
            total_chunks=0,
            last_indexed=None,
        )

    # Track statistics
    total_docs = len(documents)
    successful_docs = 0
    failed_docs = 0
    total_chunks = 0
    total_bytes = 0
    total_extracted_chars = 0

    # Process each document
    for doc in documents:
        if doc.status == "failed":
            failed_docs += 1
            logger.warning(f"Skipping failed document: {doc.filename}")
            continue

        try:
            # Chunk the document
            chunks = chunker.chunk_document(doc)

            if not chunks:
                failed_docs += 1
                logger.warning(f"No chunks generated for: {doc.filename}")
                continue

            # Embed chunks
            embeddings = embedder.embed_chunks(chunks)

            # Store in vector database
            vector_store.add_embeddings(embeddings, chunks)

            successful_docs += 1
            total_chunks += len(chunks)
            total_bytes += doc.size_bytes
            total_extracted_chars += len(doc.content)
            logger.info(
                f"Successfully indexed {doc.filename}: {len(chunks)} chunks"
            )

        except MemoryError as e:
            failed_docs += 1
            logger.error(
                f"Memory error while indexing {doc.filename}: {e}. "
                "Consider indexing fewer documents or increasing system memory.",
                exc_info=True
            )
        except OSError as e:
            failed_docs += 1
            if "disk" in str(e).lower() or "space" in str(e).lower():
                logger.error(
                    f"Disk space error while indexing {doc.filename}: {e}. "
                    "Please free up disk space and try again.",
                    exc_info=True
                )
            else:
                logger.error(f"OS error while indexing {doc.filename}: {e}", exc_info=True)
        except Exception as e:
            failed_docs += 1
            logger.error(f"Failed to index {doc.filename}: {e}", exc_info=True)

    # Get final status
    status = vector_store.get_index_status()
    status.total_documents = total_docs
    status.indexed_documents = successful_docs
    status.failed_documents = failed_docs

    logger.info(
        f"Indexing complete: {successful_docs}/{total_docs} documents indexed, "
        f"{total_chunks} total chunks, {failed_docs} failed"
    )

    # Attach simple timing metrics and aggregates for UI/logging
    duration_ms = int((datetime.utcnow() - indexing_start).total_seconds() * 1000)
    status.indexing_metrics = IndexingMetrics(
        duration_ms=duration_ms,
        document_count=successful_docs,
        total_bytes=total_bytes,
        total_extracted_chars=total_extracted_chars,
    )  # type: ignore[attr-defined]

    return status


def answer_query(
    query_text: str, session_id: str = "default", top_k: int = TOP_K_DEFAULT
) -> str:
    """
    Answer a user query using RAG pipeline with conversation history.

    Orchestrates:
    1. Create Query object
    2. Retrieve relevant chunks
    3. Get conversation history
    4. Generate response with context and history
    5. Add exchange to conversation
    6. Return response text

    Args:
        query_text: User's question
        session_id: Session identifier (for conversation history)
        top_k: Number of chunks to retrieve (3-5)

    Returns:
        Response text to display to user
    """
    global vector_store, retriever, generator, conversation_manager

    # Ensure services are initialized
    if (vector_store is None or retriever is None or 
        generator is None or conversation_manager is None):
        initialize_services()
    
    # Type assertions for Pylance
    assert vector_store is not None
    assert retriever is not None
    assert generator is not None
    assert conversation_manager is not None

    # Validate input
    if not query_text or not query_text.strip():
        logger.warning("Empty query received")
        return "Please enter a question to get started."

    query_text = query_text.strip()

    # Check if index is ready
    status = vector_store.get_index_status()
    if not status.is_ready:
        logger.warning("Vector store not ready - no documents indexed")
        return (
            "Please index documents first by clicking the 'Index Documents' button. "
            "No documents have been indexed yet."
        )

    # Create Query object and metrics container
    query = Query(session_id=session_id, content=query_text)
    metrics = QueryMetrics()
    overall_start = datetime.utcnow()

    try:
        # Retrieve relevant chunks
        logger.info(f"Processing query: '{query_text[:100]}...'")
        chunks, scores, retrieval_metrics = retriever.retrieve(query_text, top_k=top_k)
        metrics.embedding_time_ms = retrieval_metrics.embedding_time_ms
        metrics.retrieval_time_ms = retrieval_metrics.retrieval_time_ms
        metrics.retrieved_chunks = retrieval_metrics.retrieved_chunks
        metrics.average_score = retrieval_metrics.average_score

        # Update query with retrieval results
        query.retrieved_chunk_ids = [chunk.chunk_id for chunk in chunks]
        query.retrieval_scores = scores
        query.retrieval_count = len(chunks)

        # Get conversation history for context (last 10 messages)
        conversation_history = conversation_manager.get_conversation_history(
            session_id, max_messages=10
        )

        # Generate response with conversation context
        response, generation_metrics = generator.generate_response(
            query=query_text,
            context_chunks=chunks,
            conversation_history=conversation_history
        )

        # Simple completeness check: retry once if answer is too short
        if len(response.content.strip()) < 120 and chunks:
            logger.info("Response appears short; retrying generation once for completeness")
            retry_query = (
                query_text
                + "\n\nYour previous answer was too brief. Provide a more complete summary covering all relevant points from the context."
            )
            response, generation_metrics = generator.generate_response(
                query=retry_query,
                context_chunks=chunks,
                conversation_history=conversation_history,
            )

        metrics.generation_time_ms = generation_metrics.generation_time_ms
        metrics.total_time_ms = int((datetime.utcnow() - overall_start).total_seconds() * 1000)
        metrics.completion_tokens = generation_metrics.completion_tokens
        metrics.total_tokens = generation_metrics.total_tokens

        # Link query and response
        response.query_id = query.query_id
        query.response_id = response.response_id

        # Add user query and assistant response to conversation history
        conversation_manager.add_message(session_id, "user", query_text)
        conversation_manager.add_message(session_id, "assistant", response.content)

        # Log retrieval metadata
        if chunks:
            logger.info(
                f"Retrieved {len(chunks)} chunks with scores: "
                f"{[f'{s:.3f}' for s in scores]}"
            )

        logger.debug(
            f"Session {session_id}: Added exchange to conversation "
            f"(total messages: {len(conversation_history) + 2})"
        )

        # Append lightweight metrics summary for UI visibility
        metrics_summary = (
            f"\n\n---\n"
            f"Retrieval: {metrics.retrieval_time_ms} ms | "
            f"Generation: {metrics.generation_time_ms} ms | "
            f"Total: {metrics.total_time_ms} ms | "
            f"Chunks: {metrics.retrieved_chunks} | "
            f"Avg score: {metrics.average_score:.3f} | "
            f"Tokens (approx): {metrics.total_tokens}"
        )

        return response.content + metrics_summary

    except Exception as e:
        error_msg = f"Error processing query: {e}"
        logger.error(error_msg, exc_info=True)
        # On error we keep metrics as-is (may be partially filled) but
        # ensure token counts are non-negative.
        metrics.total_time_ms = max(
            metrics.total_time_ms,
            int((datetime.utcnow() - overall_start).total_seconds() * 1000),
        )
        metrics.total_tokens = max(metrics.total_tokens, 0)
        return (
            "I apologize, but I encountered an error processing your question. "
            "Please try again or rephrase your question."
        )

    finally:
        # Always log metrics so session aggregates (e.g. total tokens) remain accurate
        try:
            metrics_logger.log_query(session_id=session_id, metrics=metrics)
        except Exception as log_err:
            logger.error(f"Failed to log query metrics: {log_err}")


def main():
    """
    Main entry point for the application.

    Initializes services and launches Gradio interface.
    """
    try:
        # Initialize all services
        initialize_services()

        # Import and launch UI
        from src.ui.app import create_interface

        logger.info("Launching Gradio interface...")
        app = create_interface()
        app.launch(share=False, server_name="127.0.0.1")

    except ValueError as e:
        # Handle missing API key
        logger.error(str(e))
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print(
            "\nTo fix this:\n"
            "1. Copy .env.example to .env\n"
            "2. Add your Gemini API key to the .env file\n"
            "3. Run the application again\n",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as e:
        logger.error(f"Application startup failed: {e}", exc_info=True)
        print(f"\n❌ Error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
