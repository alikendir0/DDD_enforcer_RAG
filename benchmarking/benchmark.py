"""
RAG System Benchmarking Suite

This script evaluates the RAG system's performance using a set of test documents
and predefined questions with expected answers.

Metrics evaluated:
- Factual accuracy
- Response relevance
- Response time
- Answer completeness
- Retrieval quality
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import after adding to path
from src.main import index_documents, answer_query
import config.settings as settings


class BenchmarkTest:
    """Represents a single benchmark test case."""

    def __init__(
        self,
        question: str,
        expected_keywords: List[str],
        expected_facts: List[str],
        category: str,
        difficulty: str = "medium"
    ):
        self.question = question
        self.expected_keywords = expected_keywords  # Keywords that should appear
        self.expected_facts = expected_facts  # Specific facts that should be mentioned
        self.category = category
        self.difficulty = difficulty
        self.response = None
        self.response_time = 0.0
        self.score = 0.0
        self.details = {}


class BenchmarkRunner:
    """Runs and evaluates RAG system benchmarks."""

    def __init__(self, test_docs_path: str):
        self.test_docs_path = Path(test_docs_path)
        self.results_path = Path(__file__).parent / "results"
        self.results_path.mkdir(exist_ok=True)

        self.original_docs_folder = Path(settings.DOCUMENTS_FOLDER)
        self.original_chroma_path = Path(settings.CHROMA_DB_PATH)

        self.test_cases: List[BenchmarkTest] = []
        self.session_id = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def setup_test_environment(self):
        """Temporarily point system to test documents."""
        print("\n" + "=" * 80)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 80)

        # Backup original paths
        self.backup_docs_path = settings.DOCUMENTS_FOLDER
        self.backup_chroma_path = settings.CHROMA_DB_PATH

        # Point to test documents
        settings.DOCUMENTS_FOLDER = self.test_docs_path
        settings.CHROMA_DB_PATH = Path(__file__).parent / "test_chroma_db"

        # Clean test ChromaDB if exists
        if settings.CHROMA_DB_PATH.exists():
            print(f"Cleaning existing test ChromaDB: {settings.CHROMA_DB_PATH}")
            shutil.rmtree(settings.CHROMA_DB_PATH)

        print(f"[OK] Test documents folder: {settings.DOCUMENTS_FOLDER}")
        print(f"[OK] Test ChromaDB path: {settings.CHROMA_DB_PATH}")

    def restore_environment(self):
        """Restore original settings."""
        print("\n" + "=" * 80)
        print("RESTORING ORIGINAL ENVIRONMENT")
        print("=" * 80)

        settings.DOCUMENTS_FOLDER = self.backup_docs_path
        settings.CHROMA_DB_PATH = self.backup_chroma_path

        # Clean up test ChromaDB
        test_chroma = Path(__file__).parent / "test_chroma_db"
        if test_chroma.exists():
            shutil.rmtree(test_chroma)
            print(f"[OK] Cleaned up test ChromaDB")

        print(f"[OK] Restored original settings")

    def initialize_test_cases(self):
        """Define all test cases with expected answers."""
        print("\n" + "=" * 80)
        print("INITIALIZING TEST CASES")
        print("=" * 80)

        # AI/ML Test Cases
        self.test_cases.extend([
            BenchmarkTest(
                question="When was the field of Artificial Intelligence founded?",
                expected_keywords=["1956", "Dartmouth", "Conference"],
                expected_facts=["1956", "Dartmouth Conference"],
                category="AI",
                difficulty="easy"
            ),
            BenchmarkTest(
                question="What accuracy did AlexNet achieve on ImageNet in 2012?",
                expected_keywords=["84.6%", "accuracy", "AlexNet", "ImageNet"],
                expected_facts=["84.6%"],
                category="AI",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="How much did training GPT-3 cost?",
                expected_keywords=["4.6 million", "355 GPU-years", "cost"],
                expected_facts=["$4.6 million", "355 GPU-years"],
                category="AI",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="What are the three primary types of machine learning?",
                expected_keywords=["supervised", "unsupervised", "reinforcement"],
                expected_facts=["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning"],
                category="AI",
                difficulty="easy"
            ),
        ])

        # Climate Change Test Cases
        self.test_cases.extend([
            BenchmarkTest(
                question="How much have global average temperatures increased since pre-industrial times?",
                expected_keywords=["1.1 degrees", "Celsius", "temperature"],
                expected_facts=["1.1 degrees Celsius"],
                category="Climate",
                difficulty="easy"
            ),
            BenchmarkTest(
                question="What percentage of warming is contributed by carbon dioxide?",
                expected_keywords=["76%", "CO2", "carbon dioxide"],
                expected_facts=["76%"],
                category="Climate",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="How many tons of CO2 are released annually from fossil fuel combustion?",
                expected_keywords=["37 billion", "tons", "CO2", "fossil fuel"],
                expected_facts=["37 billion tons"],
                category="Climate",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="What percentage of coral reefs have died since 1990?",
                expected_keywords=["50%", "coral", "died"],
                expected_facts=["50%", "1990"],
                category="Climate",
                difficulty="medium"
            ),
        ])

        # Space Exploration Test Cases
        self.test_cases.extend([
            BenchmarkTest(
                question="When did Yuri Gagarin become the first human in space?",
                expected_keywords=["April 12", "1961", "Yuri Gagarin"],
                expected_facts=["April 12, 1961"],
                category="Space",
                difficulty="easy"
            ),
            BenchmarkTest(
                question="How many satellites has SpaceX deployed for Starlink?",
                expected_keywords=["4,500", "satellites", "Starlink"],
                expected_facts=["4,500 satellites"],
                category="Space",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="What is the cost of the International Space Station?",
                expected_keywords=["150 billion", "ISS"],
                expected_facts=["$150 billion"],
                category="Space",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="How many exoplanets have been confirmed as of 2023?",
                expected_keywords=["5,502", "exoplanets", "confirmed"],
                expected_facts=["5,502"],
                category="Space",
                difficulty="hard"
            ),
        ])

        # Software Architecture Test Cases
        self.test_cases.extend([
            BenchmarkTest(
                question="How many microservices does Netflix operate?",
                expected_keywords=["700", "microservices", "Netflix"],
                expected_facts=["700+"],
                category="Software",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="What is Amazon's two-pizza team rule for microservices?",
                expected_keywords=["6-8", "developers", "two-pizza"],
                expected_facts=["6-8 developers"],
                category="Software",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="How many requests per second can Kafka handle?",
                expected_keywords=["1 million", "messages", "second", "Kafka"],
                expected_facts=["1 million messages/second"],
                category="Software",
                difficulty="medium"
            ),
            BenchmarkTest(
                question="What percentage of failed projects cite poor architecture as a contributing factor?",
                expected_keywords=["68%", "failed", "architecture"],
                expected_facts=["68%"],
                category="Software",
                difficulty="hard"
            ),
        ])

        print(f"[OK] Initialized {len(self.test_cases)} test cases")
        print(f"  - AI/ML: {sum(1 for t in self.test_cases if t.category == 'AI')}")
        print(f"  - Climate: {sum(1 for t in self.test_cases if t.category == 'Climate')}")
        print(f"  - Space: {sum(1 for t in self.test_cases if t.category == 'Space')}")
        print(f"  - Software: {sum(1 for t in self.test_cases if t.category == 'Software')}")

    def index_test_documents(self):
        """Index the test documents."""
        print("\n" + "=" * 80)
        print("INDEXING TEST DOCUMENTS")
        print("=" * 80)

        start_time = time.time()
        status = index_documents()
        indexing_time = time.time() - start_time

        print(f"\n[OK] Indexing completed in {indexing_time:.2f} seconds")
        print(f"  - Documents processed: {status.total_documents}")
        print(f"  - Successfully indexed: {status.indexed_documents}")
        print(f"  - Total chunks: {status.total_chunks}")
        print(f"  - Success rate: {status.success_rate:.1%}")

        return indexing_time

    def evaluate_response(self, test: BenchmarkTest) -> Dict[str, Any]:
        """Evaluate a single test response."""
        response_lower = test.response.lower()

        # Keyword matching
        keywords_found = sum(
            1 for kw in test.expected_keywords
            if kw.lower() in response_lower
        )
        keyword_score = keywords_found / len(test.expected_keywords)

        # Fact checking
        facts_found = sum(
            1 for fact in test.expected_facts
            if fact.lower() in response_lower
        )
        fact_score = facts_found / len(test.expected_facts)

        # Response quality checks
        min_length = 50
        length_ok = len(test.response) >= min_length

        not_error = not any(
            phrase in response_lower
            for phrase in ["error", "please index", "no documents", "failed"]
        )

        # Calculate overall score
        # Weighted: facts (50%), keywords (30%), quality (20%)
        overall_score = (
            fact_score * 0.5 +
            keyword_score * 0.3 +
            (0.1 if length_ok else 0) +
            (0.1 if not_error else 0)
        )

        return {
            "keyword_score": keyword_score,
            "fact_score": fact_score,
            "keywords_found": keywords_found,
            "keywords_total": len(test.expected_keywords),
            "facts_found": facts_found,
            "facts_total": len(test.expected_facts),
            "length_ok": length_ok,
            "no_errors": not_error,
            "overall_score": overall_score
        }

    def run_test(self, test: BenchmarkTest) -> BenchmarkTest:
        """Run a single benchmark test."""
        start_time = time.time()
        test.response = answer_query(test.question, session_id=self.session_id)
        test.response_time = time.time() - start_time

        # Evaluate response
        test.details = self.evaluate_response(test)
        test.score = test.details["overall_score"]

        return test

    def run_all_tests(self):
        """Execute all benchmark tests."""
        print("\n" + "=" * 80)
        print("RUNNING BENCHMARK TESTS")
        print("=" * 80)

        total_tests = len(self.test_cases)

        for idx, test in enumerate(self.test_cases, 1):
            print(f"\n[Test {idx}/{total_tests}] {test.category} - {test.difficulty}")
            print(f"Question: {test.question}")

            test = self.run_test(test)

            print(f"Response time: {test.response_time:.2f}s")
            print(f"Score: {test.score:.1%}")
            print(f"Facts found: {test.details['facts_found']}/{test.details['facts_total']}")
            print(f"Keywords found: {test.details['keywords_found']}/{test.details['keywords_total']}")

            # Show response preview
            preview_length = 150
            preview = test.response[:preview_length]
            if len(test.response) > preview_length:
                preview += "..."
            print(f"Response preview: {preview}")

    def generate_report(self, indexing_time: float):
        """Generate comprehensive benchmark report."""
        print("\n" + "=" * 80)
        print("GENERATING BENCHMARK REPORT")
        print("=" * 80)

        # Calculate statistics
        total_tests = len(self.test_cases)
        avg_score = sum(t.score for t in self.test_cases) / total_tests
        avg_response_time = sum(t.response_time for t in self.test_cases) / total_tests

        # Category breakdown
        categories = {}
        for test in self.test_cases:
            if test.category not in categories:
                categories[test.category] = []
            categories[test.category].append(test)

        category_scores = {
            cat: sum(t.score for t in tests) / len(tests)
            for cat, tests in categories.items()
        }

        # Difficulty breakdown
        difficulties = {}
        for test in self.test_cases:
            if test.difficulty not in difficulties:
                difficulties[test.difficulty] = []
            difficulties[test.difficulty].append(test)

        difficulty_scores = {
            diff: sum(t.score for t in tests) / len(tests)
            for diff, tests in difficulties.items()
        }

        # Passing tests (score >= 0.7)
        passing_threshold = 0.7
        passing_tests = [t for t in self.test_cases if t.score >= passing_threshold]
        pass_rate = len(passing_tests) / total_tests

        # Create report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": total_tests,
                "average_score": avg_score,
                "pass_rate": pass_rate,
                "passing_threshold": passing_threshold,
                "average_response_time": avg_response_time,
                "indexing_time": indexing_time
            },
            "category_performance": category_scores,
            "difficulty_performance": difficulty_scores,
            "test_results": [
                {
                    "question": t.question,
                    "category": t.category,
                    "difficulty": t.difficulty,
                    "score": t.score,
                    "response_time": t.response_time,
                    "details": t.details,
                    "response": t.response
                }
                for t in self.test_cases
            ]
        }

        # Save JSON report
        report_file = self.results_path / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"\n[OK] JSON report saved: {report_file}")

        # Generate text report
        text_report = self.generate_text_report(report)
        text_file = self.results_path / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)

        print(f"[OK] Text report saved: {text_file}")

        # Print summary to console
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"\nOverall Performance:")
        print(f"  Average Score: {avg_score:.1%}")
        print(f"  Pass Rate: {pass_rate:.1%} ({len(passing_tests)}/{total_tests} tests)")
        print(f"  Average Response Time: {avg_response_time:.2f}s")
        print(f"  Indexing Time: {indexing_time:.2f}s")

        print(f"\nPerformance by Category:")
        for cat, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {score:.1%}")

        print(f"\nPerformance by Difficulty:")
        for diff, score in sorted(difficulty_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {diff.capitalize()}: {score:.1%}")

        # Identify problem areas
        print(f"\nTests Below Threshold ({passing_threshold:.0%}):")
        failing_tests = [t for t in self.test_cases if t.score < passing_threshold]
        if failing_tests:
            for test in failing_tests[:5]:  # Show top 5
                print(f"  - [{test.category}] {test.question[:60]}... (Score: {test.score:.1%})")
        else:
            print("  None - All tests passed!")

        return report

    def generate_text_report(self, report: Dict) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("RAG SYSTEM BENCHMARK REPORT")
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {report['timestamp']}")

        # Summary
        lines.append("\n" + "=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        summary = report['summary']
        lines.append(f"\nTotal Tests: {summary['total_tests']}")
        lines.append(f"Average Score: {summary['average_score']:.1%}")
        lines.append(f"Pass Rate: {summary['pass_rate']:.1%} (threshold: {summary['passing_threshold']:.0%})")
        lines.append(f"Average Response Time: {summary['average_response_time']:.2f} seconds")
        lines.append(f"Indexing Time: {summary['indexing_time']:.2f} seconds")

        # Category Performance
        lines.append("\n" + "=" * 80)
        lines.append("PERFORMANCE BY CATEGORY")
        lines.append("=" * 80)
        for cat, score in sorted(report['category_performance'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"\n{cat}: {score:.1%}")

        # Difficulty Performance
        lines.append("\n" + "=" * 80)
        lines.append("PERFORMANCE BY DIFFICULTY")
        lines.append("=" * 80)
        for diff, score in sorted(report['difficulty_performance'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"\n{diff.capitalize()}: {score:.1%}")

        # Individual Test Results
        lines.append("\n" + "=" * 80)
        lines.append("DETAILED TEST RESULTS")
        lines.append("=" * 80)

        for idx, test in enumerate(report['test_results'], 1):
            lines.append(f"\n{'=' * 80}")
            lines.append(f"Test {idx}: {test['category']} - {test['difficulty'].upper()}")
            lines.append(f"{'=' * 80}")
            lines.append(f"\nQuestion: {test['question']}")
            lines.append(f"\nScore: {test['score']:.1%}")
            lines.append(f"Response Time: {test['response_time']:.2f}s")
            lines.append(f"\nMetrics:")
            lines.append(f"  - Facts Found: {test['details']['facts_found']}/{test['details']['facts_total']}")
            lines.append(f"  - Keywords Found: {test['details']['keywords_found']}/{test['details']['keywords_total']}")
            lines.append(f"  - Length Check: {'PASS' if test['details']['length_ok'] else 'FAIL'}")
            lines.append(f"  - No Errors: {'PASS' if test['details']['no_errors'] else 'FAIL'}")
            lines.append(f"\nResponse:\n{test['response']}")

        return "\n".join(lines)

    def run(self):
        """Execute complete benchmark suite."""
        try:
            print("\n" + "=" * 80)
            print("RAG SYSTEM BENCHMARK SUITE")
            print("=" * 80)
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Setup
            self.setup_test_environment()
            self.initialize_test_cases()

            # Index documents
            indexing_time = self.index_test_documents()

            # Run tests
            self.run_all_tests()

            # Generate report
            report = self.generate_report(indexing_time)

            print("\n" + "=" * 80)
            print("BENCHMARK COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            return report

        finally:
            # Always restore environment
            self.restore_environment()


def main():
    """Main entry point."""
    # Verify API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables")
        sys.exit(1)

    # Get test documents path
    test_docs = Path(__file__).parent / "test_documents"
    if not test_docs.exists():
        print(f"ERROR: Test documents folder not found: {test_docs}")
        sys.exit(1)

    # Run benchmark
    runner = BenchmarkRunner(str(test_docs))
    report = runner.run()

    # Exit with appropriate code
    if report['summary']['pass_rate'] >= 0.7:
        print("\n[SUCCESS] BENCHMARK PASSED")
        sys.exit(0)
    else:
        print("\n[FAILED] BENCHMARK FAILED")
        print(f"Pass rate {report['summary']['pass_rate']:.1%} below 70% threshold")
        sys.exit(1)


if __name__ == "__main__":
    main()
