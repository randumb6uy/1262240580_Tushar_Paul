#!/usr/bin/env bash
set -e

echo "====================================================================="
echo " Kohler AI Sales Assistant & Spatial Studio (Gradio UI)"
echo "====================================================================="
echo ""

# 1. Activate Python virtual environment if present
if [ -d ".venv" ]; then
    echo "[OK] Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "[OK] Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# 2. Check if .env exists, if not copy from .env.example
if [ ! -f ".env" ]; then
    echo "[Setup] Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Launch Gradio App
echo ""
echo "[Launch] Starting Gradio web server at http://localhost:7860 ..."
python app.py "$@"
