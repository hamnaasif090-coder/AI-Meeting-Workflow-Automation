#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# start.sh – One-command startup for Meeting-to-Task System
# Usage: bash start.sh
# ─────────────────────────────────────────────────────────────

set -e

echo ""
echo "🎯  Meeting-to-Task Automation System"
echo "======================================"
echo ""

# Copy .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📄  Creating .env from .env.example…"
    cp .env.example .env
    echo "✅  .env created. Edit it to add Gemini/Ollama keys (optional)."
    echo ""
fi

# Create directories
mkdir -p uploads reports transcripts database

# Start FastAPI backend in background
echo "🚀  Starting FastAPI backend on port 8000…"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "✅  Backend PID: $BACKEND_PID"
sleep 2

# Start Streamlit frontend
echo ""
echo "🌐  Starting Streamlit frontend on port 8501…"
echo "   Open your browser at: http://localhost:8501"
echo ""
streamlit run frontend/app.py --server.port 8501

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
