"""
Local Transcription Pipeline
Uses faster-whisper (CPU-optimised Whisper implementation).

Model sizes vs RAM usage (approximate):
  tiny   ~390 MB  – fastest, lower accuracy
  base   ~740 MB  – good balance for student laptops  ← default
  small  ~1.5 GB
  medium ~3 GB
Set WHISPER_MODEL in .env to override.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Read model size from env (default: base – good CPU/RAM balance)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using faster-whisper locally.
    Falls back to a helpful error message if faster-whisper isn't installed.

    Args:
        audio_path: Absolute path to the audio file.

    Returns:
        Full transcript as a single string.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        from faster_whisper import WhisperModel  # lazy import – not needed at startup
    except ImportError:
        raise ImportError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )

    logger.info("Loading Whisper model '%s' (CPU mode)…", WHISPER_MODEL)

    # cpu_threads=4 keeps RAM < 2 GB even for the 'small' model on most laptops
    model = WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8",   # int8 quantisation – fastest on CPU, tiny quality loss
        cpu_threads=4,
    )

    logger.info("Transcribing: %s", audio_path)
    segments, info = model.transcribe(audio_path, beam_size=5, language=None)

    transcript_parts = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            transcript_parts.append(text)
        logger.debug("[%.1fs → %.1fs] %s", segment.start, segment.end, text)

    full_transcript = " ".join(transcript_parts)
    logger.info(
        "Transcription done. Language detected: %s | Chars: %d",
        info.language,
        len(full_transcript),
    )
    return full_transcript
