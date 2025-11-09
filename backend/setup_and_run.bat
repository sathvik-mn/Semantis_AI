@echo off
REM Semantis AI - Quick Setup & Run Script for Windows

echo ========================================
echo Semantis AI - Semantic Cache Backend
echo ========================================
echo.

REM Check if .venv exists
if not exist ".venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment already exists
)

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env\" (
    echo [4/4] Creating .env from template...
    copy .env.example .env >nul 2>&1
    echo.
    echo WARNING: Please edit .env and set your OPENAI_API_KEY before running!
    echo.
) else (
    echo [4/4] .env file already exists
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Starting server...
echo.

python semantic_cache_server.py

pause

