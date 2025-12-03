#!/bin/bash
# Quick launcher for RAG benchmarking suite
# Run this from the project root directory

echo "================================================================================"
echo "RAG System Benchmark Suite Launcher"
echo "================================================================================"
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable not set"
    echo ""
    echo "Please set your API key:"
    echo "  export GEMINI_API_KEY=your_api_key_here"
    echo ""
    exit 1
fi

echo "API Key: Found"
echo ""

# Run benchmark
echo "Starting benchmark..."
echo ""
python3 benchmarking/benchmark.py

RESULT=$?

echo ""
echo "================================================================================"
echo "Benchmark Complete"
echo "================================================================================"
echo ""
echo "Check the benchmarking/results/ folder for detailed reports."
echo ""

exit $RESULT
