# 🏗️ System Architecture

## High-Level Design

```
┌──────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│              http://localhost:8501 (Streamlit)               │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTP REST
┌─────────────────────────────▼────────────────────────────────┐
│                    FASTAPI BACKEND                            │
│                  http://localhost:8000                        │
│                                                              │
│  POST /upload-audio        → Transcribe + Extract + Save     │
│  POST /submit-transcript   → Extract + Save                  │
│  GET  /download/{id}/{fmt} → Serve report file               │
│  GET  /meetings            → List all meetings               │
│  GET  /meetings/{id}       → Get single meeting              │
│  GET  /health              → Health check                    │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────┴───────────────────────────────────────────┐
    │                  CORE MODULES                    │
    │                                                  │
    │  transcription.py    → faster-whisper (CPU)      │
    │  task_extractor.py   → regex / Ollama / Gemini   │
    │  report_generator.py → MD / JSON / TXT           │
    │  database.py         → SQLite CRUD               │
    └──────────────────────────────────────────────────┘
           │
    ┌──────┴───────────────────────────────────────────┐
    │                   STORAGE                        │
    │                                                  │
    │  database/meetings.db   (SQLite)                 │
    │  uploads/               (audio files)            │
    │  reports/               (generated reports)      │
    │  transcripts/           (saved transcripts)      │
    └──────────────────────────────────────────────────┘
```

## Data Flow

### Audio Upload Path
```
User uploads audio
       ↓
FastAPI saves to uploads/
       ↓
faster-whisper transcribes (CPU, int8 quantised)
       ↓
task_extractor.py processes transcript
  ├── regex patterns detect action phrases
  ├── name detection for owner assignment
  ├── deadline pattern matching
  └── priority keyword detection
       ↓
report_generator.py creates MD + JSON + TXT files
       ↓
database.py saves meeting record to SQLite
       ↓
Response JSON returned to Streamlit
       ↓
UI renders tasks, summary, download buttons
```

### Transcript Upload Path
```
User pastes text → FastAPI → task_extractor → reports → SQLite → UI
(skips transcription step)
```

## Key Design Decisions

### Why faster-whisper over whisper.cpp?
- Pure Python — easier to install via pip
- int8 quantisation built-in → 2-3x faster on CPU
- Better accuracy than whisper.cpp at same speed
- Same model weights as OpenAI Whisper

### Why SQLite over PostgreSQL?
- Zero setup — built into Python
- Single file database
- More than enough for this use case
- Deploys anywhere without a database server

### Why regex fallback?
- Works 100% offline with zero RAM overhead
- Students can use the app immediately without any API setup
- Deterministic, predictable outputs
- LLM is opt-in, not required

### Why modular LLM backend?
- Students can start with regex (free, instant)
- Upgrade to Gemini (free API key, better accuracy)
- Or use Ollama for full privacy (local, best quality)
- No code changes needed — just update .env

## Database Schema

```sql
CREATE TABLE meetings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    transcript   TEXT    NOT NULL,
    summary      TEXT,
    tasks        TEXT,        -- JSON array of task objects
    action_items TEXT,        -- JSON array of strings
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Response Schema

```json
{
  "meeting_id": 1,
  "title": "Sprint Planning",
  "transcript": "Full transcript text...",
  "summary": "2-4 sentence summary...",
  "tasks": [
    {
      "task": "Fix login bug",
      "owner": "Mark",
      "priority": "High",
      "due_date": "by Wednesday",
      "status": "Pending"
    }
  ],
  "action_items": [
    "[Mark] Fix login bug – by Wednesday"
  ]
}
```
