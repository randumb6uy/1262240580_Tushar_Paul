#!/usr/bin/env bash
set -e

echo "==============================================================================="
echo "  KOHLER AUTONOMOUS AI AGENT - RAPID DEMO LAUNCHER"
echo "  Zero API Cost | Sub-Second Latency | INR Psychological Pricing (₹xx,999)"
echo "==============================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed or not in your PATH."
    exit 1
fi

# 2. Check/Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment in .venv..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 3. Verify Dependencies
echo "[2/4] Verifying dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check

# 4. Check .env
if [ ! -f ".env" ]; then
    echo "[3/4] Creating .env from template..."
    cp .env.example .env
fi

# 5. Launch Prototype
echo "[4/4] Launching Gradio Prototype..."
echo "      Local UI: http://localhost:7860"
echo ""
python3 app.py --share
