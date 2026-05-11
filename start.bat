@echo off
REM ─────────────────────────────────────────────────────────────
REM  start.bat – Windows startup for Meeting-to-Task System
REM  Usage: Double-click or run in CMD
REM ─────────────────────────────────────────────────────────────

echo.
echo  Meeting-to-Task Automation System
echo ======================================
echo.

REM Create .env if missing
IF NOT EXIST .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo .env created. Edit it to add API keys (optional).
    echo.
)

REM Create directories
IF NOT EXIST uploads mkdir uploads
IF NOT EXIST reports mkdir reports
IF NOT EXIST transcripts mkdir transcripts
IF NOT EXIST database mkdir database

REM Start FastAPI backend in a new window
echo Starting FastAPI backend on port 8000...
start "FastAPI Backend" cmd /k "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

REM Start Streamlit frontend
echo Starting Streamlit frontend on port 8501...
echo Open your browser at: http://localhost:8501
echo.
streamlit run frontend/app.py --server.port 8501

pause
