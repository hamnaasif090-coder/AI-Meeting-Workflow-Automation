"""
Task Extraction Pipeline
========================
Strategy (in order of preference):
  1. Ollama local model  (free, offline, best quality)
  2. Google Gemini API   (free tier – 15 req/min, 1 M tokens/day)
  3. OpenRouter free     (free models like mistral-7b-free)
  4. Pure regex fallback (always works, no API needed)

Set LLM_BACKEND in .env to: ollama | gemini | openrouter | regex
"""

import os
import re
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

LLM_BACKEND     = os.getenv("LLM_BACKEND", "regex")       # default: no API required
OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "mistral")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_KEY  = os.getenv("OPENROUTER_KEY", "")

# ─── Load prompt template ──────────────────────────────────────────────────────
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "task_extraction.txt")

def _load_prompt(transcript: str) -> str:
    try:
        with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
            template = f.read()
        return template.replace("{{TRANSCRIPT}}", transcript)
    except FileNotFoundError:
        # Inline fallback prompt
        return f"""
You are an expert meeting analyst. Read the meeting transcript below and extract:
1. A short summary (2-4 sentences)
2. All tasks/action items mentioned
3. Action item bullet list

For each task return JSON with: task, owner, priority (High/Medium/Low), due_date, status.

Respond ONLY with valid JSON in this exact format:
{{
  "summary": "...",
  "tasks": [
    {{"task": "...", "owner": "...", "priority": "Medium", "due_date": "...", "status": "Pending"}}
  ],
  "action_items": ["...", "..."]
}}

TRANSCRIPT:
{transcript}
"""


# ─── Main entry point ─────────────────────────────────────────────────────────
def extract_tasks_and_summary(transcript: str) -> Dict[str, Any]:
    """
    Extract tasks, summary, and action items from a meeting transcript.
    Tries LLM backends in order; falls back to regex if all fail.
    """
    if LLM_BACKEND == "ollama":
        result = _try_ollama(transcript)
        if result:
            return result

    elif LLM_BACKEND == "gemini" and GEMINI_API_KEY:
        result = _try_gemini(transcript)
        if result:
            return result

    elif LLM_BACKEND == "openrouter" and OPENROUTER_KEY:
        result = _try_openrouter(transcript)
        if result:
            return result

    # Always-available fallback
    logger.info("Using regex-based extraction (LLM_BACKEND=%s)", LLM_BACKEND)
    return _regex_extraction(transcript)


# ─── Ollama ────────────────────────────────────────────────────────────────────
def _try_ollama(transcript: str) -> Dict | None:
    try:
        import requests
        prompt = _load_prompt(transcript)
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        return _parse_llm_json(raw)
    except Exception as e:
        logger.warning("Ollama failed: %s", e)
        return None


# ─── Gemini ────────────────────────────────────────────────────────────────────
def _try_gemini(transcript: str) -> Dict | None:
    try:
        import requests
        prompt = _load_prompt(transcript)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=body, timeout=30)
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_llm_json(raw)
    except Exception as e:
        logger.warning("Gemini failed: %s", e)
        return None


# ─── OpenRouter ───────────────────────────────────────────────────────────────
def _try_openrouter(transcript: str) -> Dict | None:
    try:
        import requests
        prompt = _load_prompt(transcript)
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=body, timeout=30
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return _parse_llm_json(raw)
    except Exception as e:
        logger.warning("OpenRouter failed: %s", e)
        return None


# ─── Parse LLM JSON output ────────────────────────────────────────────────────
def _parse_llm_json(raw: str) -> Dict | None:
    """Extract and parse JSON from LLM response (handles markdown code fences)."""
    try:
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        # Find first { ... } block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM output")
        data = json.loads(match.group())
        # Normalise tasks
        tasks = []
        for t in data.get("tasks", []):
            tasks.append({
                "task": t.get("task", "").strip(),
                "owner": t.get("owner", "Unassigned").strip() or "Unassigned",
                "priority": t.get("priority", "Medium").strip() or "Medium",
                "due_date": t.get("due_date", "Not specified").strip() or "Not specified",
                "status": t.get("status", "Pending").strip() or "Pending",
            })
        return {
            "summary": data.get("summary", "").strip(),
            "tasks": tasks,
            "action_items": [str(a).strip() for a in data.get("action_items", [])],
        }
    except Exception as e:
        logger.warning("JSON parse failed: %s | raw: %s", e, raw[:200])
        return None


# ─── Regex Fallback ───────────────────────────────────────────────────────────
def _regex_extraction(transcript: str) -> Dict[str, Any]:
    """
    Pure-regex task extraction – works 100% offline, no ML required.
    Detects action phrases, names, and common deadline patterns.
    """
    tasks: List[Dict] = []
    action_items: List[str] = []

    # ── Sentence tokenisation (simple) ────────────────────────────────────────
    sentences = re.split(r"(?<=[.!?])\s+", transcript)

    # ── Trigger phrases that usually precede a task ───────────────────────────
    ACTION_TRIGGERS = re.compile(
        r"\b(will|should|must|need to|needs to|has to|have to|going to|"
        r"action item|follow[- ]up|please|make sure|ensure|take care of|"
        r"responsible for|assigned to|deadline|by [A-Z][a-z]|complete|finish|"
        r"send|prepare|review|schedule|update|create|write|fix|deploy|test|"
        r"implement|design|research|investigate|confirm|book|coordinate)\b",
        re.IGNORECASE,
    )

    # ── Name detection heuristic (Capitalised words not at sentence start) ────
    NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")

    # ── Deadline patterns ──────────────────────────────────────────────────────
    DEADLINE_PATTERNS = [
        re.compile(r"\bby\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", re.I),
        re.compile(r"\bby\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b", re.I),
        re.compile(r"\bby\s+(end of (?:day|week|month|the week))\b", re.I),
        re.compile(r"\bby\s+(next\s+\w+)\b", re.I),
        re.compile(r"\bdue\s+(on\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?)\b", re.I),
        re.compile(r"\b(tomorrow|this Friday|this week|next week|ASAP|immediately)\b", re.I),
        re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                   r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
                   r"Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b", re.I),
    ]

    # ── Priority keywords ──────────────────────────────────────────────────────
    HIGH_KW   = re.compile(r"\b(urgent|asap|critical|immediately|high[- ]priority|blocker)\b", re.I)
    LOW_KW    = re.compile(r"\b(low[- ]priority|nice[- ]to[- ]have|when possible|eventually|backlog)\b", re.I)

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue
        if not ACTION_TRIGGERS.search(sent):
            continue

        # Extract due date
        due_date = "Not specified"
        for pat in DEADLINE_PATTERNS:
            m = pat.search(sent)
            if m:
                due_date = m.group().strip()
                break

        # Extract owner
        owner = "Unassigned"
        names = NAME_PATTERN.findall(sent)
        # Filter out common non-name capitalised words
        SKIP = {"I", "We", "The", "This", "That", "It", "He", "She", "They",
                 "Please", "Will", "Should", "Must", "Make", "Sure", "Action",
                 "Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",
                 "January","February","March","April","May","June","July",
                 "August","September","October","November","December"}
        filtered = [n for n in names if n not in SKIP and len(n) > 1]
        if filtered:
            owner = filtered[0]

        # Determine priority
        if HIGH_KW.search(sent):
            priority = "High"
        elif LOW_KW.search(sent):
            priority = "Low"
        else:
            priority = "Medium"

        # Clean task text (remove filler words at start)
        task_text = re.sub(r"^(okay|so|also|and|right|well)[,\s]+", "", sent, flags=re.I).strip()

        task = {
            "task": task_text,
            "owner": owner,
            "priority": priority,
            "due_date": due_date,
            "status": "Pending",
        }
        tasks.append(task)
        action_items.append(f"[{owner}] {task_text}")

    # ── Summary: first 3 non-trivial sentences ────────────────────────────────
    summary_sents = [s.strip() for s in sentences if len(s.strip()) > 40][:3]
    summary = " ".join(summary_sents) if summary_sents else "Meeting transcript processed."

    # Deduplicate tasks (simple)
    seen = set()
    unique_tasks = []
    for t in tasks:
        key = t["task"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique_tasks.append(t)

    logger.info("Regex extraction: %d tasks, %d action items", len(unique_tasks), len(action_items))
    return {
        "summary": summary,
        "tasks": unique_tasks,
        "action_items": list(dict.fromkeys(action_items)),  # deduplicate, keep order
    }
