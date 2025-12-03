"""
Verification script to check if benchmarking setup is correct.
Run this before executing the full benchmark.
"""

import sys
import os
from pathlib import Path


def verify_setup():
    """Verify benchmark environment is properly set up."""
    print("=" * 80)
    print("BENCHMARKING SETUP VERIFICATION")
    print("=" * 80)

    all_checks_passed = True

    # Check 1: Verify we're in the correct directory
    print("\n[Check 1] Directory structure...")
    current_dir = Path(__file__).parent

    if not (current_dir / "benchmark.py").exists():
        print("  [X] benchmark.py not found")
        all_checks_passed = False
    else:
        print("  [OK] benchmark.py found")

    if not (current_dir / "test_documents").exists():
        print("  [X] test_documents folder not found")
        all_checks_passed = False
    else:
        print("  [OK] test_documents folder found")

    # Check 2: Verify test documents
    print("\n[Check 2] Test documents...")
    expected_docs = [
        "artificial_intelligence.txt",
        "climate_change.txt",
        "space_exploration.txt",
        "software_architecture.md"
    ]

    docs_path = current_dir / "test_documents"
    for doc in expected_docs:
        doc_path = docs_path / doc
        if not doc_path.exists():
            print(f"  [X] {doc} not found")
            all_checks_passed = False
        else:
            file_size = doc_path.stat().st_size
            print(f"  [OK] {doc} ({file_size:,} bytes)")

    # Check 3: Verify Python path setup
    print("\n[Check 3] Python imports...")
    project_root = current_dir.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

    config_found = False
    main_found = False

    try:
        import config.settings
        config_found = True
        print("  [OK] Can import config.settings")
    except ImportError:
        # Try alternative import
        try:
            from config import settings
            config_found = True
            print("  [OK] Can import config.settings (alternative)")
        except ImportError as e:
            print(f"  [WARNING] Cannot import config.settings: {e}")
            print("           This may be fine if the structure is correct")

    try:
        from src.main import index_documents, answer_query
        main_found = True
        print("  [OK] Can import src.main functions")
    except ImportError as e:
        print(f"  [WARNING] Cannot import src.main: {e}")
        print("           This may be fine if the structure is correct")

    # Check if main files exist even if import fails
    if not config_found:
        if (project_root / "config" / "settings.py").exists():
            print("  [OK] config/settings.py file exists")
    if not main_found:
        if (project_root / "src" / "main.py").exists():
            print("  [OK] src/main.py file exists")

    # Check 4: Verify API key
    print("\n[Check 4] Environment variables...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  [X] GEMINI_API_KEY not set")
        print("     Set it with: set GEMINI_API_KEY=your_key (Windows)")
        print("     or: export GEMINI_API_KEY=your_key (Linux/Mac)")
        all_checks_passed = False
    else:
        print(f"  [OK] GEMINI_API_KEY set (length: {len(api_key)} characters)")

    # Check 5: Results folder
    print("\n[Check 5] Results folder...")
    results_path = current_dir / "results"
    if not results_path.exists():
        print("  - Results folder doesn't exist (will be created)")
        try:
            results_path.mkdir(exist_ok=True)
            print("  [OK] Results folder created")
        except Exception as e:
            print(f"  [X] Cannot create results folder: {e}")
            all_checks_passed = False
    else:
        print("  [OK] Results folder exists")

    # Check 6: Count total test document words
    print("\n[Check 6] Test document statistics...")
    total_words = 0
    total_chars = 0

    for doc in expected_docs:
        doc_path = docs_path / doc
        if doc_path.exists():
            content = doc_path.read_text(encoding='utf-8')
            words = len(content.split())
            chars = len(content)
            total_words += words
            total_chars += chars

    print(f"  Total words across all documents: {total_words:,}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Average document size: {total_words // len(expected_docs):,} words")

    # Final summary
    print("\n" + "=" * 80)
    if all_checks_passed:
        print("[SUCCESS] ALL CHECKS PASSED - Ready to run benchmark!")
        print("=" * 80)
        print("\nRun the benchmark with:")
        print("  python benchmarking/benchmark.py")
        print("\nOr use the launcher scripts:")
        print("  Windows: benchmarking\\run_benchmark.bat")
        print("  Linux/Mac: bash benchmarking/run_benchmark.sh")
        return 0
    else:
        print("[FAILED] SOME CHECKS FAILED - Please fix issues before running benchmark")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = verify_setup()
    sys.exit(exit_code)
