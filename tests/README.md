# RAG Chatbot Tests

This directory contains automated tests for the RAG Chatbot system.

## Test Structure

```
tests/
├── integration/           # End-to-end integration tests
│   ├── test_user_story_1.py  # Tests for User Story 1 (T027-T029)
│   └── __init__.py
├── fixtures/             # Test data
│   └── sample_documents/ # Sample documents for testing
└── README.md            # This file
```

## Prerequisites

### For Integration Tests

Integration tests require:

1. **Gemini API Key**: Set the `GEMINI_API_KEY` environment variable
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY = "your-api-key-here"

   # Linux/macOS
   export GEMINI_API_KEY="your-api-key-here"

   # Or create a .env file in project root
   GEMINI_API_KEY=your-api-key-here
   ```

2. **Sample Documents**: Test documents in `tests/fixtures/sample_documents/`
   - Already provided: sample1.txt, sample2.md, sample3.txt
   - Cover topics: Machine Learning, Python, Databases

3. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Run All Integration Tests

```bash
# Run with pytest (recommended)
pytest tests/integration/ -v

# Run with verbose output and print statements
pytest tests/integration/ -v -s

# Run specific test file
pytest tests/integration/test_user_story_1.py -v
```

### Run Specific Test

```bash
# Run a specific test function
pytest tests/integration/test_user_story_1.py::TestUserStory1::test_t027_question_covered_in_documents -v

# Run a specific test class
pytest tests/integration/test_user_story_1.py::TestUserStory1 -v
```

### Run Tests Directly (for debugging)

```bash
# Run test file directly
python tests/integration/test_user_story_1.py
```

## Test Coverage

### User Story 1: Basic Chatbot Interaction (T027-T029)

**File**: `tests/integration/test_user_story_1.py`

- **T027**: Question covered in documents
  - Tests that system retrieves context from indexed documents
  - Verifies response includes information from relevant documents
  - Example: "What are the three main types of machine learning?"

- **T028**: Question not in documents
  - Tests that system uses general knowledge for out-of-scope questions
  - Verifies system doesn't fail on questions without document context
  - Example: "What is the capital of France?"

- **T029**: Empty or malformed query
  - Tests error handling for invalid inputs
  - Verifies helpful error messages are shown
  - Cases: empty string, whitespace only, very short input

**Additional Tests**:
- Special characters in queries
- Very long queries
- Robustness checks

## Expected Output

When all tests pass:

```
tests/integration/test_user_story_1.py::TestUserStory1::test_t027_question_covered_in_documents PASSED
tests/integration/test_user_story_1.py::TestUserStory1::test_t028_question_not_in_documents PASSED
tests/integration/test_user_story_1.py::TestUserStory1::test_t029_empty_or_malformed_query PASSED
tests/integration/test_user_story_1.py::TestUserStory1EdgeCases::test_query_with_special_characters PASSED
tests/integration/test_user_story_1.py::TestUserStory1EdgeCases::test_very_long_query PASSED

================================ 5 passed in 15.23s ================================
```

## Troubleshooting

### Tests Skip with "GEMINI_API_KEY not set"

**Solution**: Set your API key as described in Prerequisites

### Tests Fail with "Sample documents not found"

**Solution**: Ensure sample documents exist in `tests/fixtures/sample_documents/`
```bash
ls tests/fixtures/sample_documents/
# Should show: sample1.txt, sample2.md, sample3.txt
```

### Tests Fail with "Failed to index any documents"

**Possible causes**:
- ChromaDB initialization issue
- Document parsing errors
- Embedding model download needed (first run)

**Solution**: Check logs for detailed error messages

### Network/API Errors

If tests fail with API rate limits or network errors:
- Wait a few minutes and retry
- Check your internet connection
- Verify API key is valid

## Writing New Tests

To add new integration tests:

1. Create a new test file in `tests/integration/`
2. Import necessary modules from `src/`
3. Use the `setup_system` fixture or create your own
4. Follow pytest conventions:
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test functions: `test_*`

Example:
```python
import pytest
from src.main import answer_query

def test_my_scenario():
    response = answer_query("test question")
    assert response is not None
```

## Continuous Integration

To run tests in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run integration tests
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: |
    pip install -r requirements.txt
    pytest tests/integration/ -v
```

## Notes

- Integration tests make real API calls to Gemini
- Tests may take 10-30 seconds to complete
- First run downloads embedding model (~80MB)
- Tests create temporary ChromaDB storage in `data/chroma_db/`
