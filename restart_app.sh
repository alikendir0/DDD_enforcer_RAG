#!/bin/bash

echo "============================================"
echo "  RAG Chatbot - Clean Restart Script"
echo "============================================"
echo ""

echo "[1/4] Stopping any running Python processes..."
pkill -f "python -m src.main" 2>/dev/null || true
sleep 2

echo "[2/4] Cleaning Python cache files..."
find src -type f -name "*.pyc" -delete 2>/dev/null || true
find src -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "[3/4] Verifying code is up to date..."
python -m py_compile src/main.py

echo "[4/4] Starting application..."
echo ""
echo "============================================"
echo "  Opening browser to http://127.0.0.1:7860"
echo "  Press Ctrl+C to stop the server"
echo "============================================"
echo ""

python -m src.main
