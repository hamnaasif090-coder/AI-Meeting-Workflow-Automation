"""
Meeting-to-Task Automation System
FastAPI Backend - Main Entry Point
"""

import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

from .transcription import transcribe_audio
from .task_extractor import extract_tasks_and_summary
from .report_generator import generate_markdown_report, generate_json_report, generate_txt_report
from .database import init_db, save_meeting, get_all_meetings, get_meeting_by_id
from .models import MeetingResponse, TranscriptInput

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Directories ──────────────────────────────────────────────────────────────
UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), "..", "uploads")
REPORT_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "transcripts")

for d in [UPLOAD_DIR, REPORT_DIR, TRANSCRIPT_DIR]:
    os.makedirs(d, exist_ok=True)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – initialising database...")
    init_db()
    yield
    logger.info("Shutting down.")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meeting-to-Task API",
    description="Convert meeting audio/transcripts into structured tasks automatically.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Meeting-to-Task API is running"}


# ─── Upload Audio ─────────────────────────────────────────────────────────────
@app.post("/upload-audio", response_model=MeetingResponse)
async def upload_audio(
    file: UploadFile = File(...),
    meeting_title: str = Form(default="Untitled Meeting"),
):
    """
    Accept an audio file, transcribe it locally with faster-whisper,
    extract tasks/summary, persist to SQLite, and return structured data.
    """
    # Validate file type
    allowed = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/x-m4a",
               "audio/ogg", "audio/webm", "video/mp4"}
    if file.content_type and file.content_type not in allowed:
        logger.warning("Unsupported content type: %s", file.content_type)

    # Save upload
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        logger.info("Audio saved: %s", save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Transcribe
    try:
        transcript = transcribe_audio(save_path)
        logger.info("Transcription complete (%d chars)", len(transcript))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    # Extract tasks & summary
    try:
        result = extract_tasks_and_summary(transcript)
        logger.info("Extraction complete – %d tasks found", len(result.get("tasks", [])))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task extraction failed: {e}")

    # Persist
    meeting_id = save_meeting(
        title=meeting_title,
        transcript=transcript,
        summary=result.get("summary", ""),
        tasks=result.get("tasks", []),
        action_items=result.get("action_items", []),
    )

    # Generate reports
    _generate_reports(meeting_id, meeting_title, transcript, result)

    return MeetingResponse(
        meeting_id=meeting_id,
        title=meeting_title,
        transcript=transcript,
        summary=result.get("summary", ""),
        tasks=result.get("tasks", []),
        action_items=result.get("action_items", []),
    )


# ─── Submit Raw Transcript ────────────────────────────────────────────────────
@app.post("/submit-transcript", response_model=MeetingResponse)
async def submit_transcript(data: TranscriptInput):
    """
    Accept raw transcript text, extract tasks/summary, persist and return results.
    """
    transcript = data.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript text is empty.")

    try:
        result = extract_tasks_and_summary(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task extraction failed: {e}")

    meeting_id = save_meeting(
        title=data.meeting_title or "Untitled Meeting",
        transcript=transcript,
        summary=result.get("summary", ""),
        tasks=result.get("tasks", []),
        action_items=result.get("action_items", []),
    )

    _generate_reports(meeting_id, data.meeting_title or "Meeting", transcript, result)

    return MeetingResponse(
        meeting_id=meeting_id,
        title=data.meeting_title or "Untitled Meeting",
        transcript=transcript,
        summary=result.get("summary", ""),
        tasks=result.get("tasks", []),
        action_items=result.get("action_items", []),
    )


# ─── Download Reports ─────────────────────────────────────────────────────────
@app.get("/download/{meeting_id}/{format}")
def download_report(meeting_id: int, format: str):
    """Download a report in md / json / txt format."""
    fmt = format.lower()
    if fmt not in ("md", "json", "txt"):
        raise HTTPException(status_code=400, detail="Format must be md, json, or txt.")

    file_path = os.path.join(REPORT_DIR, f"meeting_{meeting_id}.{fmt}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found.")

    media = {"md": "text/markdown", "json": "application/json", "txt": "text/plain"}
    return FileResponse(file_path, media_type=media[fmt],
                        filename=f"meeting_{meeting_id}_report.{fmt}")


# ─── List All Meetings ────────────────────────────────────────────────────────
@app.get("/meetings")
def list_meetings():
    return {"meetings": get_all_meetings()}


# ─── Get Single Meeting ───────────────────────────────────────────────────────
@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting


# ─── Internal Helper ──────────────────────────────────────────────────────────
def _generate_reports(meeting_id: int, title: str, transcript: str, result: dict):
    """Write md / json / txt reports to disk."""
    base = os.path.join(REPORT_DIR, f"meeting_{meeting_id}")
    try:
        with open(f"{base}.md", "w", encoding="utf-8") as f:
            f.write(generate_markdown_report(title, transcript, result))
        with open(f"{base}.json", "w", encoding="utf-8") as f:
            f.write(generate_json_report(title, transcript, result))
        with open(f"{base}.txt", "w", encoding="utf-8") as f:
            f.write(generate_txt_report(title, transcript, result))
        logger.info("Reports written for meeting %d", meeting_id)
    except Exception as e:
        logger.error("Report generation failed: %s", e)
