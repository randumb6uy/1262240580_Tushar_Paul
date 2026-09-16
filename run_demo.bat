@echo off
setlocal enabledelayedexpansion
title Kohler Autonomous AI Agent - Setup & Launch

echo ===============================================================================
echo   KOHLER AUTONOMOUS AI AGENT - RAPID DEMO LAUNCHER
echo   Zero API Cost ^| Sub-Second Latency ^| INR Psychological Pricing (₹xx,999)
echo ===============================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Check/Create Virtual Environment
if not exist ".venv" (
    echo [1/4] Creating isolated virtual environment in .venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

:: 3. Check/Install Requirements
echo [2/4] Verifying dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

:: 4. Check .env configuration
if not exist ".env" (
    echo [3/4] Initializing .env configuration from template...
    copy .env.example .env >nul
    echo       Created .env with default offline Ollama configuration.
) else (
    echo [3/4] Found existing .env configuration.
)

:: 5. Launch Prototype
echo [4/4] Starting Kohler Autonomous Agent Prototype...
echo       - Local Web UI: http://localhost:7860
echo.
python app.py --share

pause
