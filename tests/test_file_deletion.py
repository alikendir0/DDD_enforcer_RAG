"""Test file deletion functionality."""

import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.file_manager import FileManager


def test_file_deletion():
    """Test document deletion functionality."""
    print("\n=== Testing File Deletion Functionality ===\n")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        test_files = ['test1.txt', 'test2.txt', 'test3.pdf']
        for filename in test_files:
            (temp_path / filename).write_text(f"Content of {filename}")

        # Initialize FileManager without vector store
        file_manager = FileManager(
            documents_folder=str(temp_path),
            vector_store=None
        )

        # Test 1: List documents
        print("Test 1: List documents")
        documents = file_manager.list_documents()
        print(f"  Found {len(documents)} documents")
        assert len(documents) == 3, f"Expected 3 documents, got {len(documents)}"
        print("  PASS\n")

        # Test 2: Delete single document
        print("Test 2: Delete single document")
        success, message = file_manager.delete_document('test1.txt', delete_embeddings=False)
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        assert success, "Deletion should succeed"
        assert not (temp_path / 'test1.txt').exists(), "File should be deleted"
        print("  PASS\n")

        # Test 3: Verify file list updated
        print("Test 3: Verify file list updated")
        documents = file_manager.list_documents()
        print(f"  Remaining documents: {len(documents)}")
        assert len(documents) == 2, f"Expected 2 documents, got {len(documents)}"
        filenames = [doc.filename for doc in documents]
        assert 'test1.txt' not in filenames, "Deleted file should not be in list"
        print("  PASS\n")

        # Test 4: Delete multiple documents
        print("Test 4: Delete multiple documents")
        success, message, file_list = file_manager.delete_documents(
            ['test2.txt', 'test3.pdf'],
            delete_embeddings=False
        )
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        assert success, "Deletion should succeed"
        assert len(file_list) == 0, "All files should be deleted"
        print("  PASS\n")

        # Test 5: Delete non-existent file
        print("Test 5: Delete non-existent file")
        success, message = file_manager.delete_document('nonexistent.txt', delete_embeddings=False)
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        assert not success, "Should fail for non-existent file"
        assert "not found" in message.lower(), "Should indicate file not found"
        print("  PASS\n")

        # Test 6: Delete with empty list
        print("Test 6: Delete with empty list")
        success, message, file_list = file_manager.delete_documents([], delete_embeddings=False)
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        assert not success, "Should fail for empty list"
        assert "no files" in message.lower(), "Should indicate no files selected"
        print("  PASS\n")

    print("=" * 60)
    print("All deletion tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_file_deletion()
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
