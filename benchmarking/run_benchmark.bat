@echo off
REM Quick launcher for RAG benchmarking suite
REM Run this from the project root directory

echo ================================================================================
echo RAG System Benchmark Suite Launcher
echo ================================================================================
echo.

REM Check if GEMINI_API_KEY is set
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY environment variable not set
    echo.
    echo Please set your API key:
    echo   set GEMINI_API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

echo API Key: Found
echo.

REM Run benchmark
echo Starting benchmark...
echo.
python benchmarking\benchmark.py

echo.
echo ================================================================================
echo Benchmark Complete
echo ================================================================================
echo.
echo Check the benchmarking\results\ folder for detailed reports.
echo.
pause
