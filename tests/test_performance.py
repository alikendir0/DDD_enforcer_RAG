"""Performance tests for NFR validation (T042-T044c)."""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.stats_tracker import StatsTracker
from src.services.config_manager import ConfigManager
from src.services.file_manager import FileManager
from src.services.vector_store import VectorStore


def test_nfr_001_statistics_performance():
    """T042: Verify NFR-001 - Statistics update within 200ms."""
    print("\n=== T042: Testing NFR-001 - Statistics Performance ===")

    # Initialize stats tracker
    stats_tracker = StatsTracker(vector_store=None)
    session_id = "test_session"

    # Test track_query_stats performance
    start = time.time()
    stats_tracker.track_query_stats(
        session_id=session_id,
        input_tokens=100,
        output_tokens=50,
        model_name="gemini-2.5-flash"
    )
    track_time = (time.time() - start) * 1000  # Convert to ms

    # Test format_stats_for_display performance
    start = time.time()
    stats_tracker.format_stats_for_display(session_id)
    format_time = (time.time() - start) * 1000

    total_time = track_time + format_time

    print(f"  track_query_stats: {track_time:.2f}ms")
    print(f"  format_stats_for_display: {format_time:.2f}ms")
    print(f"  Total: {total_time:.2f}ms")
    print(f"  NFR-001 Requirement: < 200ms")
    status = "PASS" if total_time < 200 else "FAIL"
    print(f"  Status: {status}")

    return total_time < 200


def test_nfr_004_config_persistence_performance():
    """T044: Verify NFR-004 - Configuration persists within 100ms."""
    print("\n=== T044: Testing NFR-004 - Config Persistence Performance ===")

    # Initialize config manager
    config_manager = ConfigManager(config_path="config/test_ui_config.json")

    # Test save_config performance
    start = time.time()
    success, message = config_manager.save_config(
        top_k=5,
        chunk_size=512,
        chunk_overlap=64,
        show_context_enabled=True
    )
    save_time = (time.time() - start) * 1000

    print(f"  save_config: {save_time:.2f}ms")
    print(f"  Success: {success}")
    print(f"  NFR-004 Requirement: < 100ms")
    status = "PASS" if save_time < 100 else "FAIL"
    print(f"  Status: {status}")

    # Cleanup test file
    test_config = Path("config/test_ui_config.json")
    if test_config.exists():
        test_config.unlink()

    return save_time < 100


def test_nfr_006_chromadb_failure_handling():
    """T044a: Verify NFR-006 - ChromaDB connection failure handling."""
    print("\n=== T044a: Testing NFR-006 - ChromaDB Failure Handling ===")

    # Initialize stats tracker without vector store (simulating disconnection)
    stats_tracker = StatsTracker(vector_store=None)

    # Test that it returns default values instead of crashing
    file_count = stats_tracker._get_embedded_file_count()
    chunk_count = stats_tracker._get_total_chunk_count()

    print(f"  Embedded file count (no vector store): {file_count}")
    print(f"  Total chunk count (no vector store): {chunk_count}")
    print(f"  Expected: 0 for both")
    status = "PASS" if file_count == 0 and chunk_count == 0 else "FAIL"
    print(f"  Status: {status}")

    return file_count == 0 and chunk_count == 0


def test_nfr_007_config_validation_boundaries():
    """T044b: Verify NFR-007 - Configuration validation with boundary values."""
    print("\n=== T044b: Testing NFR-007 - Config Validation Boundaries ===")

    config_manager = ConfigManager()

    test_cases = [
        (0, 512, 0, False, "top_k=0 (below min)"),
        (1, 512, 0, True, "top_k=1 (min boundary)"),
        (10, 512, 0, True, "top_k=10 (max boundary)"),
        (11, 512, 0, False, "top_k=11 (above max)"),
        (5, 256, 0, True, "chunk_size=256 (min boundary)"),
        (5, 1024, 0, True, "chunk_size=1024 (max boundary)"),
        (5, 512, 512, False, "overlap=chunk_size (invalid)"),
        (5, 512, 511, False, "overlap >= chunk_size (invalid)"),
        (5, 512, 256, True, "overlap=256 at boundary (valid if < chunk_size)"),
        (5, 512, 128, True, "overlap < chunk_size (valid)"),
    ]

    all_passed = True
    for top_k, chunk_size, chunk_overlap, should_pass, description in test_cases:
        from src.models.ui_configuration import UIConfiguration
        try:
            config = UIConfiguration(
                top_k=top_k,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                show_context_enabled=False
            )
            is_valid, error_msg = config_manager.validate_config(config)

            passed = (is_valid == should_pass)
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {description}: valid={is_valid}, expected={should_pass}")
            if not passed:
                print(f"    Error message: {error_msg}")
                all_passed = False
        except Exception as e:
            # Validation might happen in __post_init__
            is_valid = False
            passed = (is_valid == should_pass)
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {description}: exception raised (expected={should_pass})")
            if not passed:
                all_passed = False

    status = "PASS" if all_passed else "FAIL"
    print(f"  Overall Status: {status}")
    return all_passed


def test_nfr_008_retrieval_logging():
    """T044c: Verify NFR-008 - Retrieval logging verification."""
    print("\n=== T044c: Testing NFR-008 - Retrieval Logging ===")
    print("  Note: This test checks that logging infrastructure is in place.")
    print("  Actual log verification requires running the application and checking log output.")

    # Check that main.py contains the retrieval logging code
    main_py = Path("src/main.py")
    if not main_py.exists():
        print("  [FAIL]: src/main.py not found")
        return False

    content = main_py.read_text(encoding='utf-8')

    # Check for required logging elements
    checks = [
        ("query_text" in content, "Query text logging"),
        ("chunk_ids" in content or "chunk.chunk_id" in content, "Chunk IDs logging"),
        ("scores" in content or "similarity" in content, "Similarity scores logging"),
        ("timestamp" in content or "query.timestamp" in content, "Timestamp logging"),
        ("Retrieval operation" in content or "retrieval" in content.lower(), "Retrieval operation logging"),
    ]

    all_passed = True
    for passed, description in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {description}")
        if not passed:
            all_passed = False

    status = "PASS" if all_passed else "FAIL"
    print(f"  Overall Status: {status}")
    return all_passed


def main():
    """Run all performance and validation tests."""
    print("=" * 60)
    print("Performance and Validation Tests (T042-T044c)")
    print("=" * 60)

    results = {
        "T042 (NFR-001)": test_nfr_001_statistics_performance(),
        "T044 (NFR-004)": test_nfr_004_config_persistence_performance(),
        "T044a (NFR-006)": test_nfr_006_chromadb_failure_handling(),
        "T044b (NFR-007)": test_nfr_007_config_validation_boundaries(),
        "T044c (NFR-008)": test_nfr_008_retrieval_logging(),
    }

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}]: {test_name}")

    all_passed = all(results.values())
    overall = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"\nOverall: {overall}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
