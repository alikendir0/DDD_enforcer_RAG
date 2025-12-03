"""
Configuration settings for the RAG Chatbot system.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Document Processing
DOCUMENTS_FOLDER = DATA_DIR / "documents"
SUPPORTED_FORMATS = [".txt", ".md", ".pdf", ".docx"]

# Chunking Configuration
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 0  # no overlap per specification

# Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Vector Store Configuration
CHROMA_DB_PATH = DATA_DIR / "chroma_db"
COLLECTION_NAME = "document_chunks"
DISTANCE_METRIC = "cosine"

# Retrieval Configuration
TOP_K_MIN = 1
TOP_K_MAX = 10
TOP_K_DEFAULT = 3

# Conversation Configuration
MAX_CONVERSATION_HISTORY = 10  # messages (5 exchanges)

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
