@echo off
echo ============================================
echo   RAG Chatbot - Clean Restart Script
echo ============================================
echo.

echo [1/4] Stopping any running Python processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *src.main*" 2>nul
timeout /t 2 >nul

echo [2/4] Cleaning Python cache files...
del /s /q src\*.pyc 2>nul
for /d /r src %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [3/4] Cleaning ChromaDB cache...
del /s /q src\services\__pycache__\*.pyc 2>nul

echo [4/4] Starting application...
echo.
echo Application will start in 3 seconds...
timeout /t 3 >nul
echo.
echo ============================================
echo   Opening browser to http://127.0.0.1:7860
echo   Press Ctrl+C to stop the server
echo ============================================
echo.

python -m src.main
