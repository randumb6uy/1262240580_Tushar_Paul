@echo off
setlocal enabledelayedexpansion
title Kohler AI Sales Assistant & Spatial Studio

echo =====================================================================
echo  Kohler AI Sales Assistant & Spatial Studio (Gradio UI)
echo =====================================================================
echo.

:: 1. Activate Python virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [OK] Activating virtual environment (venv)...
    call venv\Scripts\activate.bat
) else (
    echo [Info] Using system Python environment...
)

:: 2. Check if .env exists, if not copy from .env.example
if not exist ".env" (
    echo [Setup] Creating .env from .env.example...
    copy .env.example .env
)

:: 3. Launch Gradio App
echo.
echo [Launch] Starting Gradio web server at http://localhost:7860 ...
python app.py %*

pause
