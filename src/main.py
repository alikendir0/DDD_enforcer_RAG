"""
Main entry point for the RAG Chatbot application.
"""
import sys
from pathlib import Path
from typing import Optional

from src.services.document_processor import DocumentProcessor, ParseError
from src.services.chunker import Chunker
from src.services.embedder import Embedder
from src.services.vector_store import VectorStore
from src.services.retriever import Retriever
from src.services.generator import Generator
from src.services.conversation_manager import ConversationManager
from src.models.document import IndexingStatus
from src.models.conversation import Query, Response
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
stats_tracker = None  # Will be initialized after vector_store
config_manager = None  # Will be initialized with configuration loading
file_manager = None  # Will be initialized with vector_store reference


def initialize_services():
    """
    Initialize all core services.

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    global embedder, vector_store, retriever, generator, conversation_manager, stats_tracker, config_manager, file_manager

    logger.info("Initializing RAG Chatbot services...")

    # Ensure data/documents/ directory exists on startup (T047)
    DOCUMENTS_FOLDER.mkdir(parents=True, exist_ok=True)
    logger.info(f"Documents directory ensured: {DOCUMENTS_FOLDER}")

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

    # Initialize stats tracker with vector store reference
    from src.services.stats_tracker import StatsTracker
    stats_tracker = StatsTracker(vector_store=vector_store)

    # Initialize config manager and load configuration
    from src.services.config_manager import ConfigManager
    config_manager = ConfigManager()
    config_manager.load_config()

    # Initialize file manager with vector store reference
    from src.services.file_manager import FileManager
    file_manager = FileManager(
        documents_folder=str(DOCUMENTS_FOLDER),
        vector_store=vector_store
    )

    logger.info("All services initialized successfully")


def index_documents(
    documents_folder: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> IndexingStatus:
    """
    Index all documents from the specified folder.

    Orchestrates:
    1. Load documents from folder
    2. Chunk documents (using configured chunk_size/overlap if not specified)
    3. Embed chunks
    4. Store embeddings in vector store

    Args:
        documents_folder: Path to folder containing documents (default: from settings)
        chunk_size: Token count per chunk (overrides config if provided)
        chunk_overlap: Overlapping tokens between chunks (overrides config if provided)

    Returns:
        IndexingStatus with summary of indexing operation
    """
    global embedder, vector_store, config_manager

    # Ensure services are initialized
    if vector_store is None or embedder is None or config_manager is None:
        initialize_services()

    # Type assertions for Pylance
    assert embedder is not None
    assert vector_store is not None
    assert config_manager is not None

    # Get chunk parameters from config if not provided
    if chunk_size is None or chunk_overlap is None:
        config = config_manager.get_current_config()
        if chunk_size is None:
            chunk_size = config.chunk_size
        if chunk_overlap is None:
            chunk_overlap = config.chunk_overlap

    if documents_folder is None:
        documents_folder = str(DOCUMENTS_FOLDER)

    logger.info(f"Starting document indexing from: {documents_folder}")

    # Clear existing embeddings before re-indexing
    logger.info("Clearing existing embeddings from vector store...")
    vector_store.clear()

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
    chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    logger.info(f"Using chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")

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

    return status


def answer_query(
    query_text: str,
    session_id: str = "default",
    top_k: Optional[int] = None,
    return_context: bool = False
) -> tuple[str, list[dict]] | str:
    """
    Answer a user query using RAG pipeline with conversation history.

    Orchestrates:
    1. Create Query object
    2. Retrieve relevant chunks (using configured top_k if not specified)
    3. Get conversation history
    4. Generate response with context and history
    5. Track statistics (token usage, costs)
    6. Add exchange to conversation
    7. Return response text (and optionally context metadata)

    Args:
        query_text: User's question
        session_id: Session identifier (for conversation history)
        top_k: Number of chunks to retrieve (overrides config if provided)
        return_context: If True, return (response_text, context_metadata)

    Returns:
        Response text to display to user, or tuple of (response_text, context_metadata)
        context_metadata is a list of dicts with chunk_text, score, document_name
    """
    global vector_store, retriever, generator, conversation_manager, stats_tracker, config_manager

    # Ensure services are initialized
    if (vector_store is None or retriever is None or
        generator is None or conversation_manager is None or
        stats_tracker is None or config_manager is None):
        initialize_services()

    # Type assertions for Pylance
    assert vector_store is not None
    assert retriever is not None
    assert generator is not None
    assert conversation_manager is not None
    assert stats_tracker is not None
    assert config_manager is not None

    # Get top_k from config if not provided
    if top_k is None:
        config = config_manager.get_current_config()
        top_k = config.top_k

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

    try:
        # Create Query object
        query = Query(session_id=session_id, content=query_text)

        # Retrieve relevant chunks
        logger.info(f"Processing query: '{query_text[:100]}...'")
        chunks, scores = retriever.retrieve(query_text, top_k=top_k)

        # Update query with retrieval results
        query.retrieved_chunk_ids = [chunk.chunk_id for chunk in chunks]
        query.retrieval_scores = scores
        query.retrieval_count = len(chunks)

        # Get conversation history for context (last 10 messages)
        conversation_history = conversation_manager.get_conversation_history(
            session_id, max_messages=10
        )

        # Generate response with conversation context
        response, input_tokens, output_tokens = generator.generate_response(
            query=query_text,
            context_chunks=chunks,
            conversation_history=conversation_history
        )

        # Link query and response
        response.query_id = query.query_id
        query.response_id = response.response_id

        # Track statistics (token usage and costs)
        from config.settings import GEMINI_MODEL
        stats_tracker.track_query_stats(
            session_id=session_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=GEMINI_MODEL
        )

        # Track retrieval quality (successful if we got chunks)
        stats_tracker.track_retrieval_quality(success=(len(chunks) > 0))

        # Add user query and assistant response to conversation history
        conversation_manager.add_message(session_id, "user", query_text)
        conversation_manager.add_message(session_id, "assistant", response.content)

        # Log retrieval metadata (NFR-008: Constitution compliance)
        if chunks:
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            logger.info(
                f"Retrieval operation - Query: '{query_text[:50]}...', "
                f"Retrieved {len(chunks)} chunks (IDs: {chunk_ids}), "
                f"Similarity scores: {[f'{s:.3f}' for s in scores]}, "
                f"Timestamp: {query.timestamp}"
            )

        logger.debug(
            f"Session {session_id}: Added exchange to conversation "
            f"(total messages: {len(conversation_history) + 2})"
        )

        # Build context metadata if requested
        if return_context and chunks:
            import os
            context_metadata = []
            for chunk, score in zip(chunks, scores):
                # Extract just the filename from the full path
                filename = os.path.basename(chunk.document_path)
                context_metadata.append({
                    "chunk_text": chunk.content,
                    "score": float(score),
                    "document_name": filename,
                    "chunk_index": chunk.chunk_index
                })
            return response.content, context_metadata

        return response.content

    except Exception as e:
        error_msg = f"Error processing query: {e}"
        logger.error(error_msg, exc_info=True)
        error_response = (
            "I apologize, but I encountered an error processing your question. "
            "Please try again or rephrase your question."
        )
        if return_context:
            return error_response, []
        return error_response


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
