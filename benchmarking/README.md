# RAG System Benchmarking Suite

A comprehensive benchmarking system to evaluate the performance and accuracy of the RAG (Retrieval-Augmented Generation) chatbot implementation.

## Overview

This benchmarking suite tests the RAG system's ability to:
- Index documents correctly
- Retrieve relevant information
- Generate accurate answers to questions
- Maintain consistent performance across different topics
- Handle various difficulty levels

## Directory Structure

```
benchmarking/
├── benchmark.py           # Main benchmark script
├── README.md             # This file
├── test_documents/       # Test documents with known content
│   ├── artificial_intelligence.txt
│   ├── climate_change.txt
│   ├── space_exploration.txt
│   └── software_architecture.md
└── results/              # Generated benchmark reports (created during run)
```

## Test Documents

The suite includes 4 comprehensive test documents covering diverse topics:

1. **Artificial Intelligence** - Covers AI history, machine learning, deep learning, applications
2. **Climate Change** - Discusses greenhouse gases, impacts, mitigation strategies
3. **Space Exploration** - Details missions, technology, achievements
4. **Software Architecture** - Explains architectural patterns and best practices

Each document contains specific, verifiable facts and statistics that can be tested.

## Test Cases

The benchmark includes **16 test cases** across 4 categories:

### Categories
- **AI/ML**: 4 tests about artificial intelligence and machine learning
- **Climate**: 4 tests about climate change and environmental science
- **Space**: 4 tests about space exploration and astronomy
- **Software**: 4 tests about software architecture patterns

### Difficulty Levels
- **Easy**: Basic factual questions (e.g., dates, names)
- **Medium**: Specific statistics and technical details
- **Hard**: Complex information requiring precise retrieval

## Evaluation Metrics

Each test response is evaluated using multiple metrics:

### 1. Fact Score (50% weight)
- Checks if specific expected facts appear in the response
- Example: "1956", "Dartmouth Conference" for AI founding question

### 2. Keyword Score (30% weight)
- Verifies presence of relevant keywords
- Ensures topic relevance and coverage

### 3. Quality Checks (20% weight)
- Minimum response length (50 characters)
- No error messages or failures

### Overall Scoring
- **Pass threshold**: 70% or higher
- Weighted combination of all metrics
- Individual test scores and overall pass rate reported

## Running the Benchmark

### Prerequisites

1. GEMINI_API_KEY environment variable must be set
2. All RAG system dependencies installed
3. Python 3.8 or higher

### Execution

Run from the project root directory:

```bash
python benchmarking/benchmark.py
```

Or from the benchmarking directory:

```bash
cd benchmarking
python benchmark.py
```

### What Happens During Execution

1. **Environment Setup**: Creates isolated test environment
   - Points system to test documents
   - Creates temporary ChromaDB instance

2. **Document Indexing**: Indexes the 4 test documents
   - Reports indexing time and success rate

3. **Test Execution**: Runs all 16 test cases
   - Displays progress for each test
   - Shows response times and scores

4. **Report Generation**: Creates comprehensive reports
   - JSON report with full details
   - Human-readable text report
   - Console summary

5. **Cleanup**: Restores original environment
   - Removes test ChromaDB
   - Restores original settings

## Output Reports

Two report files are generated in `benchmarking/results/`:

### 1. JSON Report (`benchmark_report_YYYYMMDD_HHMMSS.json`)

Structured data including:
- Summary statistics
- Category and difficulty breakdowns
- Individual test results with full responses
- Detailed scoring metrics

### 2. Text Report (`benchmark_report_YYYYMMDD_HHMMSS.txt`)

Human-readable report with:
- Executive summary
- Performance breakdowns
- Complete test details
- Full question-answer pairs

## Interpreting Results

### Overall Performance
- **Average Score**: Mean of all test scores (target: ≥70%)
- **Pass Rate**: Percentage of tests scoring ≥70%
- **Response Time**: Average time per query

### Category Performance
Shows how well the system handles different topics:
- Identifies strengths (e.g., high accuracy on AI questions)
- Highlights weaknesses (e.g., lower scores on climate data)

### Difficulty Performance
Indicates retrieval quality across complexity levels:
- Easy questions should score very high (90%+)
- Medium questions target 70-85%
- Hard questions may score 60-75%

### Common Issues

**Low Fact Score**
- System may not be retrieving the most relevant chunks
- Consider adjusting TOP_K or chunk size settings

**Low Keyword Score**
- Responses may be too general
- Check if retrieval is finding correct documents

**High Response Time**
- May indicate performance issues
- Check embedding model and vector store efficiency

## Customization

### Adding New Test Cases

Edit `benchmark.py` and add to `initialize_test_cases()`:

```python
BenchmarkTest(
    question="Your question here?",
    expected_keywords=["keyword1", "keyword2"],
    expected_facts=["specific fact", "another fact"],
    category="YourCategory",
    difficulty="easy|medium|hard"
)
```

### Adding New Documents

1. Place new document in `test_documents/`
2. Add corresponding test cases in `benchmark.py`
3. Ensure expected facts are verifiable from document content

### Adjusting Thresholds

Modify in `benchmark.py`:

```python
# Passing threshold (default: 70%)
passing_threshold = 0.7

# Metric weights (must sum to 1.0)
overall_score = (
    fact_score * 0.5 +      # 50% weight
    keyword_score * 0.3 +    # 30% weight
    length_check * 0.1 +     # 10% weight
    error_check * 0.1        # 10% weight
)
```

## Troubleshooting

### "GEMINI_API_KEY not found"
Set the environment variable:
```bash
# Windows
set GEMINI_API_KEY=your_key_here

# Linux/Mac
export GEMINI_API_KEY=your_key_here
```

### "Test documents folder not found"
Ensure you're running from the correct directory or the test_documents folder exists.

### "No response received"
- Check if documents were indexed successfully
- Verify API key is valid
- Check network connectivity

### Low scores across all tests
- Review indexing output for errors
- Check chunk size and overlap settings
- Verify embedding model is loading correctly
- Ensure ChromaDB is functioning properly

## Performance Benchmarks

Expected performance on reference hardware:

- **Indexing Time**: 5-15 seconds for 4 documents
- **Average Query Time**: 2-8 seconds per question
- **Overall Pass Rate**: 70-90% (well-tuned system)
- **Category Scores**: 65-95% depending on complexity

## Integration with CI/CD

The benchmark returns appropriate exit codes:
- **Exit 0**: Pass rate ≥ 70%
- **Exit 1**: Pass rate < 70% or errors

Example GitHub Actions usage:

```yaml
- name: Run RAG Benchmarks
  run: python benchmarking/benchmark.py
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Future Enhancements

Potential improvements for the benchmark suite:

- [ ] Multi-turn conversation testing
- [ ] Semantic similarity scoring using embeddings
- [ ] Latency percentile tracking (p50, p95, p99)
- [ ] Concurrent query stress testing
- [ ] Memory usage profiling
- [ ] Cost tracking (API calls, tokens)
- [ ] Comparative analysis across runs
- [ ] Automated threshold tuning
- [ ] Adversarial question testing

## Notes

- This benchmark does NOT modify the original RAG system
- All tests run in an isolated environment
- Original documents and ChromaDB are never touched
- Safe to run repeatedly without side effects
- Results may vary based on API availability and model updates

## Support

For issues or questions about the benchmark:
1. Check this README for common issues
2. Review the generated reports for detailed failure analysis
3. Examine individual test responses for specific problems
4. Verify RAG system is functioning correctly with integration tests
