# 🎯 Meeting-to-Task Automation System

> Convert meeting transcripts into structured, actionable tasks — **100% free, no paid APIs, CPU-only.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Cost: $0](https://img.shields.io/badge/API%20Cost-$0.00-brightgreen)](README.md)

---

## 📸 Screenshots

```
Home Page → Clean dark UI with feature overview
Process Meeting → Upload audio or paste transcript
Results → Summary, task table, action items
Download → MD / JSON / TXT reports
Dashboard → Meeting history and stats
```

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🎙️ Audio Transcription | Local Whisper (CPU-only, no API) |
| 🤖 AI Task Extraction | Regex + optional Ollama / Gemini free tier |
| 📋 Structured Output | Tasks with owner, priority, due date |
| 📝 Report Export | Markdown, JSON, Plain Text download |
| 💾 Meeting History | SQLite — stored locally on your machine |
| 🌐 Clean UI | Streamlit — runs in any browser |
| 💰 Cost | **$0.00** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                    │
│         (Upload → View Results → Download)              │
└────────────────────┬────────────────────────────────────┘
                     │  HTTP (REST API)
┌────────────────────▼────────────────────────────────────┐
│                   FASTAPI BACKEND                        │
│  /upload-audio  /submit-transcript  /download  /meetings │
└──────┬──────────────┬──────────────────────┬────────────┘
       │              │                      │
┌──────▼──────┐ ┌─────▼──────┐  ┌──────────▼──────────┐
│  WHISPER    │ │   TASK     │  │   REPORT GENERATOR  │
│ TRANSCRIBE  │ │ EXTRACTOR  │  │  (MD / JSON / TXT)  │
│  (CPU only) │ │(regex/LLM) │  └──────────┬──────────┘
└─────────────┘ └─────┬──────┘             │
                      │                    │
              ┌───────▼────────────────────▼──────────┐
              │           SQLITE DATABASE              │
              │        + LOCAL FILE STORAGE            │
              └────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
meeting_tasks/
├── backend/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, all endpoints
│   ├── models.py            ← Pydantic schemas
│   ├── transcription.py     ← faster-whisper pipeline
│   ├── task_extractor.py    ← regex + LLM extraction
│   ├── report_generator.py  ← MD / JSON / TXT reports
│   └── database.py          ← SQLite CRUD operations
├── frontend/
│   └── app.py               ← Streamlit UI (all pages)
├── prompts/
│   └── task_extraction.txt  ← LLM prompt template
├── templates/
│   ├── example_transcript.txt
│   └── example_output.json
├── uploads/                 ← Audio files (git-ignored)
├── reports/                 ← Generated reports (git-ignored)
├── transcripts/             ← Saved transcripts (git-ignored)
├── database/                ← SQLite DB file (git-ignored)
├── docs/                    ← Additional documentation
├── screenshots/             ← App screenshots
├── .env.example             ← Environment variable template
├── requirements.txt         ← Full dependencies
├── requirements-minimal.txt ← Minimal (no Whisper)
├── start.sh                 ← Linux/Mac one-command start
├── start.bat                ← Windows one-command start
└── README.md
```

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.10+ (download from [python.org](https://python.org))
- 4 GB RAM minimum (6 GB recommended for Whisper base model)
- No GPU required

### Step 1 – Clone & Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/meeting-to-task.git
cd meeting-to-task

# Create virtual environment (strongly recommended)
python -m venv venv

# Activate it
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2 – Configure

```bash
# Copy the example environment file
cp .env.example .env

# Open .env and set your preferences
# (Default settings work out of the box — no API keys needed)
```

### Step 3 – Run

**Linux/Mac:**
```bash
bash start.sh
```

**Windows:**
```
Double-click start.bat
```

**Manual (two terminals):**
```bash
# Terminal 1 – Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 – Frontend
streamlit run frontend/app.py
```

### Step 4 – Open Browser

```
http://localhost:8501
```

---

## 🤖 LLM Configuration

The system works in **4 modes**, configured via `LLM_BACKEND` in your `.env` file:

### Mode 1: Regex (Default — no setup)
```env
LLM_BACKEND=regex
```
✅ Works offline, no API, no GPU, instant

### Mode 2: Ollama (Best quality — local, free)
```bash
# 1. Install Ollama: https://ollama.ai
# 2. Pull a model:
ollama pull mistral     # 4 GB RAM, good quality
# or
ollama pull llama3.2   # lighter option

# 3. Set in .env:
LLM_BACKEND=ollama
OLLAMA_MODEL=mistral
```

### Mode 3: Google Gemini (Free tier — cloud)
```bash
# 1. Get free API key: https://aistudio.google.com/app/apikey
# 2. Set in .env:
LLM_BACKEND=gemini
GEMINI_API_KEY=your_key_here
```
Free limits: 15 requests/min, 1 million tokens/day

### Mode 4: OpenRouter (Free Mistral-7B)
```bash
# 1. Sign up free: https://openrouter.ai
# 2. Set in .env:
LLM_BACKEND=openrouter
OPENROUTER_KEY=your_key_here
```

---

## 🎙️ Audio Transcription

Uses **faster-whisper** — a CPU-optimised Whisper implementation.

| Model | RAM Usage | Speed (5 min audio) | Accuracy |
|-------|-----------|---------------------|----------|
| `tiny` | ~300 MB | ~30 sec | Good |
| `base` | ~500 MB | ~1 min | **Better ← recommended** |
| `small` | ~1 GB | ~2 min | Great |
| `medium` | ~3 GB | ~5 min | Excellent |

Set in `.env`:
```env
WHISPER_MODEL=base
```

The model downloads automatically on first use.

**Supported audio formats:** MP3, WAV, MP4, M4A, OGG, WEBM

---

## 📊 Output Format

### Task JSON Structure
```json
{
  "tasks": [
    {
      "task": "Fix the login bug blocking QA",
      "owner": "Mark",
      "priority": "High",
      "due_date": "by Wednesday",
      "status": "Pending"
    }
  ]
}
```

### Markdown Report
- Meeting summary
- Action items list  
- Tasks table with priority colour codes
- Full transcript

### Plain Text Report
- Clean, printer-friendly format
- Same data as Markdown, no formatting

---

## ☁️ Deployment (Free)

### Option A: Streamlit Cloud (Easiest — frontend only)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set `frontend/app.py` as entry point
5. Add environment variables in the Streamlit dashboard
6. Deploy — free forever

> **Note:** For audio transcription on cloud, use transcript-only mode.
> Set `API_BASE_URL` to point to your Railway backend.

### Option B: Railway (Backend API)

1. Sign up at [railway.app](https://railway.app) (free tier: $5 credit/month)
2. Click "Deploy from GitHub"
3. Add environment variables
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Option C: Render (Backend API)

1. Sign up at [render.com](https://render.com)
2. New → Web Service → Connect GitHub
3. Build command: `pip install -r requirements-minimal.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Option D: Run Locally (Full features — recommended for students)

No deployment needed. Just `bash start.sh` and share via ngrok if needed:
```bash
pip install pyngrok
ngrok http 8501  # Get a public URL for your local app
```

---

## 🧪 Testing the System

Use the included example transcript:

```bash
# Copy example transcript contents
cat templates/example_transcript.txt
```

Paste it into the UI under **Process Meeting → Paste Transcript**.

Expected output: 8 tasks extracted with owners, priorities, and due dates.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to backend` | Make sure `uvicorn` is running on port 8000 |
| `faster-whisper not found` | Run `pip install faster-whisper` |
| Transcription is slow | Use `WHISPER_MODEL=tiny` for faster processing |
| Out of memory | Use `WHISPER_MODEL=tiny` and `compute_type=int8` |
| No tasks extracted | Try a more detailed transcript or switch to Ollama/Gemini mode |
| Gemini API error | Check your API key and free tier limits |

---

## 📚 Learning Resources

This project covers:
- **FastAPI** – [fastapi.tiangolo.com/tutorial](https://fastapi.tiangolo.com/tutorial)
- **Streamlit** – [docs.streamlit.io](https://docs.streamlit.io)
- **Whisper** – [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **Ollama** – [ollama.ai/docs](https://ollama.ai/docs)
- **SQLite** – [sqlite.org/docs](https://sqlite.org/docs.html)

---

## 🗓️ 5-Day Build Plan (For Students)

| Day | Tasks |
|-----|-------|
| **Day 1** | Set up environment, install dependencies, test FastAPI + Streamlit |
| **Day 2** | Build `database.py` and `models.py`, test SQLite CRUD |
| **Day 3** | Build `task_extractor.py` with regex, test with example transcript |
| **Day 4** | Build `report_generator.py`, integrate all backend endpoints |
| **Day 5** | Build Streamlit UI, connect to backend, test end-to-end |
| **Day 6** | Add Whisper transcription, test with audio file |
| **Day 7** | Deploy to Streamlit Cloud + Railway, write documentation |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) for the transcription model
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for CPU optimisation  
- [FastAPI](https://fastapi.tiangolo.com) for the elegant API framework
- [Streamlit](https://streamlit.io) for making Python UIs effortless
- [Ollama](https://ollama.ai) for free local LLMs

---

*Built with ❤️ for university students — zero cost, maximum learning.*
