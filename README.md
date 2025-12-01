# RAG-Enabled Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers questions using context from local documents, powered by Google Gemini API.

## Features

- **Document Indexing**: Supports .txt, .md, .pdf, and .docx files
- **Semantic Search**: Uses ChromaDB for efficient vector similarity search
- **Local Embeddings**: Sentence transformers for privacy-preserving embeddings
- **Web Interface**: Simple Gradio-based chat interface
- **Conversation History**: Multi-turn dialogue support within sessions

## Prerequisites

- Python 3.10 or higher
- Gemini API key from [Google AI Studio](https://ai.google.dev/)
- At least 4GB RAM (8GB recommended for larger document corpora)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd RAG_system
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variable**:

   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

   Or set it directly:
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY = "your-api-key-here"

   # Linux/macOS
   export GEMINI_API_KEY="your-api-key-here"
   ```

## Usage

1. **Add documents** to `data/documents/` folder

2. **Run the application**:
   ```bash
   python src/main.py
   ```

3. **Open your browser** to the URL shown (typically `http://127.0.0.1:7860`)

4. **Click "Index Documents"** to process your document corpus

5. **Ask questions** in the chat interface

## Project Structure

```
RAG_system/
├── src/
│   ├── models/          # Data models
│   ├── services/        # Core services (processing, embedding, retrieval)
│   ├── ui/              # Gradio interface
│   └── main.py          # Application entry point
├── config/
│   └── settings.py      # Configuration
├── tests/               # Unit and integration tests
├── data/
│   ├── documents/       # Your document corpus
│   └── chroma_db/       # Vector database storage
└── requirements.txt     # Python dependencies
```

## Configuration

Edit `config/settings.py` to customize:
- Document folder location
- Chunk size (default: 512 tokens)
- Number of retrieved chunks (default: 3-5)
- Embedding model
- Conversation history length

## Testing

### Manual Testing

To test the application with sample documents:

1. Sample documents are provided in `tests/fixtures/sample_documents/`
2. Copy these to `data/documents/`:
   ```bash
   cp tests/fixtures/sample_documents/* data/documents/
   ```
3. Run the application and index these documents
4. Try questions like:
   - "What are the types of machine learning?"
   - "How do I create a dictionary in Python?"
   - "What is a vector database?"

### Automated Testing

Run the integration test suite to verify all acceptance scenarios:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific User Story 1 tests
pytest tests/integration/test_user_story_1.py -v

# Run with detailed output
pytest tests/integration/ -v -s
```

**Note**: Integration tests require a valid `GEMINI_API_KEY` environment variable.

See `tests/README.md` for detailed testing documentation.

## Troubleshooting

### API Key Not Found
Ensure `GEMINI_API_KEY` environment variable is set before running the application.
Check `.env.example` for the correct format.

### PDF Parsing Fails
Some PDFs (scanned images) don't have extractable text. Convert to text-based PDF first.
For encrypted PDFs, remove password protection before indexing.

### Slow Indexing
Large documents take time to process. Check console for progress logs.
The first run also downloads the embedding model (~80MB), which may take a few minutes.

### Poor Answer Quality
- Ensure documents contain relevant information
- Try adjusting the number of retrieved chunks in settings (TOP_K_DEFAULT)
- Check retrieval logs for similarity scores
- Ensure your documents are well-structured and readable

### Memory Errors
If you encounter memory errors during indexing:
- Index documents in batches (remove some documents from folder)
- Increase system RAM
- Reduce chunk size in settings (trade-off: may affect quality)

### Conversation History Not Working
Ensure you're in the same browser session. Refreshing the page starts a new session.
Conversation history is not persisted across application restarts.

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
