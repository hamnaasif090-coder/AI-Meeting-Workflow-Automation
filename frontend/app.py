"""
Meeting-to-Task Automation System
Streamlit Frontend
"""

import os
import io
import json
import requests
import streamlit as st
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Meeting → Tasks",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* ── Cards ── */
    .card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    /* ── Priority badges ── */
    .badge-high   { background:#ef4444; color:#fff; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:600; }
    .badge-medium { background:#f59e0b; color:#fff; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:600; }
    .badge-low    { background:#10b981; color:#fff; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:600; }

    /* ── Metric cards ── */
    .metric-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-number { font-size: 2.5rem; font-weight: 700; color: #a78bfa; line-height: 1; }
    .metric-label  { font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-top: 0.3rem; }

    /* ── Header ── */
    .hero-title {
        font-size: 2.8rem; font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .hero-sub { color: rgba(255,255,255,0.55); font-size: 1.05rem; margin-top: 0.5rem; }

    /* ── Task row ── */
    .task-row {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
    }
    .task-title { font-weight: 500; color: #e2e8f0; font-size: 0.95rem; }
    .task-meta  { font-size: 0.8rem; color: rgba(255,255,255,0.45); margin-top: 0.3rem; }

    /* ── Section heading ── */
    .section-heading {
        font-size: 1.15rem; font-weight: 600;
        color: #c4b5fd; margin: 1.5rem 0 0.8rem;
        display: flex; align-items: center; gap: 0.5rem;
    }

    /* ── Sidebar ── */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.9) !important;
    }

    /* ── Inputs ── */
    .stTextArea textarea, .stTextInput input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stFileUploader {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
        border: 2px dashed rgba(167,139,250,0.4) !important;
    }

    /* ── Button ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white; border: none; border-radius: 10px;
        padding: 0.6rem 1.5rem; font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(124,58,237,0.4);
    }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def priority_badge(p: str) -> str:
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(p, "badge-medium")
    return f'<span class="{cls}">{p}</span>'


def call_api(endpoint: str, method="GET", **kwargs):
    try:
        url = f"{API_BASE}{endpoint}"
        resp = requests.request(method, url, timeout=180, **kwargs)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to backend. Make sure the FastAPI server is running."
    except Exception as e:
        return None, f"❌ API error: {e}"


# ─── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 MeetingTask AI")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏠 Home", "🎙️ Process Meeting", "📊 Dashboard", "📂 Past Meetings", "ℹ️ About"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Backend Status**")
    health, err = call_api("/health")
    if health:
        st.success("🟢 API Online")
    else:
        st.error("🔴 API Offline")

    st.markdown("---")
    st.markdown(
        "<small style='color:rgba(255,255,255,0.35)'>v1.0.0 • Free & Open-Source<br>"
        "Built for students 🎓</small>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown('<div class="hero-title">Meeting → Task AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Upload a meeting audio or paste a transcript — '
        'get structured tasks, summaries, and reports instantly. 100% free.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("🎙️", "Audio Transcription", "Local Whisper — no API cost"),
        ("🤖", "AI Task Extraction", "Regex + LLM (Ollama/Gemini free)"),
        ("📋", "Structured Output", "JSON, Markdown, TXT download"),
        ("💾", "Meeting History", "SQLite local storage"),
    ]
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:2rem">{icon}</div>'
                f'<div style="font-weight:600;color:#e2e8f0;margin-top:.5rem">{title}</div>'
                f'<div class="metric-label">{desc}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. Click **Process Meeting** in the sidebar  
    2. Upload an audio file **or** paste your transcript  
    3. Click **Analyse Meeting**  
    4. Download your reports in MD / JSON / TXT
    """)

    st.info("💡 **No GPU required.** Everything runs on a normal laptop CPU.", icon="💡")


# ════════════════════════════════════════════════════════════════════════════════
# PROCESS MEETING
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🎙️ Process Meeting":
    st.markdown('<div class="hero-title" style="font-size:2rem">Process a Meeting</div>',
                unsafe_allow_html=True)
    st.markdown("")

    meeting_title = st.text_input("Meeting Title", placeholder="e.g. Sprint Planning – Week 22")
    input_mode = st.radio("Input Type", ["📄 Paste Transcript", "🎵 Upload Audio"],
                          horizontal=True)

    transcript_text = ""
    audio_file = None

    if input_mode == "📄 Paste Transcript":
        transcript_text = st.text_area(
            "Transcript",
            height=260,
            placeholder="Paste your meeting transcript here…\n\n"
                        "e.g.\nJohn: We need to finish the API by Friday.\n"
                        "Sarah: I'll handle the documentation by next Monday.\n"
                        "Mark: The login bug is urgent — please fix it ASAP.",
        )
    else:
        audio_file = st.file_uploader(
            "Upload Audio File",
            type=["mp3", "wav", "mp4", "m4a", "ogg", "webm"],
        )
        st.caption("Supported: MP3, WAV, MP4, M4A, OGG, WEBM • Transcribed locally via Whisper (no API)")

    st.markdown("")
    analyse_btn = st.button("🔍 Analyse Meeting", use_container_width=True)

    if analyse_btn:
        if not meeting_title.strip():
            meeting_title = f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        if input_mode == "📄 Paste Transcript":
            if not transcript_text.strip():
                st.error("Please paste a transcript first.")
                st.stop()
            with st.spinner("🤖 Extracting tasks and generating summary…"):
                result, err = call_api(
                    "/submit-transcript",
                    method="POST",
                    json={"transcript": transcript_text, "meeting_title": meeting_title},
                )
        else:
            if audio_file is None:
                st.error("Please upload an audio file first.")
                st.stop()
            with st.spinner("🎙️ Transcribing audio… (this may take 1–3 minutes for CPU)"):
                result, err = call_api(
                    "/upload-audio",
                    method="POST",
                    files={"file": (audio_file.name, audio_file.read(), audio_file.type)},
                    data={"meeting_title": meeting_title},
                )

        if err:
            st.error(err)
            st.stop()

        st.session_state["last_result"] = result
        st.success("✅ Analysis complete!")

    # ── Display results ──────────────────────────────────────────────────────
    if "last_result" in st.session_state:
        r = st.session_state["last_result"]
        mid = r.get("meeting_id")

        st.markdown("---")
        st.markdown(f"### 📋 Results: {r.get('title', 'Meeting')}")

        # Metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="metric-card"><div class="metric-number">{len(r.get("tasks",[]))}</div>'
                f'<div class="metric-label">Tasks Extracted</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="metric-card"><div class="metric-number">{len(r.get("action_items",[]))}</div>'
                f'<div class="metric-label">Action Items</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            high = sum(1 for t in r.get("tasks", []) if t.get("priority") == "High")
            st.markdown(
                f'<div class="metric-card"><div class="metric-number" style="color:#ef4444">{high}</div>'
                f'<div class="metric-label">High Priority</div></div>',
                unsafe_allow_html=True,
            )

        # Summary
        st.markdown('<div class="section-heading">📝 Summary</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card">{r.get("summary", "_No summary available._")}</div>',
            unsafe_allow_html=True,
        )

        # Tasks
        st.markdown('<div class="section-heading">✅ Extracted Tasks</div>', unsafe_allow_html=True)
        if r.get("tasks"):
            for i, t in enumerate(r["tasks"], 1):
                st.markdown(
                    f'<div class="task-row">'
                    f'<div class="task-title">#{i} {t.get("task","")}</div>'
                    f'<div class="task-meta">'
                    f'👤 {t.get("owner","Unassigned")} &nbsp;|&nbsp; '
                    f'{priority_badge(t.get("priority","Medium"))} &nbsp;|&nbsp; '
                    f'📅 {t.get("due_date","Not specified")} &nbsp;|&nbsp; '
                    f'⏳ {t.get("status","Pending")}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No tasks found in transcript.")

        # Action Items
        if r.get("action_items"):
            st.markdown('<div class="section-heading">📌 Action Items</div>', unsafe_allow_html=True)
            for item in r["action_items"]:
                st.markdown(f"- {item}")

        # Downloads
        st.markdown("---")
        st.markdown("### 📥 Download Reports")
        d1, d2, d3 = st.columns(3)

        for col, fmt, label, mime in [
            (d1, "md",   "📝 Markdown",   "text/markdown"),
            (d2, "json", "🗂️ JSON",        "application/json"),
            (d3, "txt",  "📄 Plain Text",  "text/plain"),
        ]:
            with col:
                dl_data, dl_err = call_api(f"/download/{mid}/{fmt}")
                if dl_err:
                    # Fallback: generate locally from session data
                    if fmt == "json":
                        content = json.dumps(r, indent=2, ensure_ascii=False).encode()
                    else:
                        content = str(r).encode()
                else:
                    # We got JSON from the API but we want raw file bytes
                    # Re-request as raw
                    try:
                        raw = requests.get(f"{API_BASE}/download/{mid}/{fmt}", timeout=10)
                        content = raw.content
                    except Exception:
                        content = b""

                if content:
                    col.download_button(
                        label=label,
                        data=content,
                        file_name=f"meeting_{mid}_report.{fmt}",
                        mime=mime,
                        use_container_width=True,
                    )


# ════════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.markdown('<div class="hero-title" style="font-size:2rem">📊 Dashboard</div>',
                unsafe_allow_html=True)
    st.markdown("")

    meetings_data, err = call_api("/meetings")
    if err:
        st.error(err)
        st.stop()

    meetings = meetings_data.get("meetings", [])
    total = len(meetings)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{total}</div>'
            f'<div class="metric-label">Total Meetings Processed</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number" style="color:#60a5fa">Free</div>'
            f'<div class="metric-label">API Cost ($ 0.00)</div></div>',
            unsafe_allow_html=True,
        )

    if meetings:
        st.markdown("### Recent Meetings")
        for m in meetings[:10]:
            st.markdown(
                f'<div class="card"><b>{m["title"]}</b> &nbsp;'
                f'<small style="color:rgba(255,255,255,0.45)">ID #{m["id"]} • {m["created_at"]}</small></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No meetings processed yet. Go to **Process Meeting** to get started.")


# ════════════════════════════════════════════════════════════════════════════════
# PAST MEETINGS
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📂 Past Meetings":
    st.markdown('<div class="hero-title" style="font-size:2rem">📂 Meeting History</div>',
                unsafe_allow_html=True)

    meetings_data, err = call_api("/meetings")
    if err:
        st.error(err)
        st.stop()

    meetings = meetings_data.get("meetings", [])
    if not meetings:
        st.info("No meetings yet.")
        st.stop()

    selected_id = st.selectbox(
        "Select a meeting",
        [f"#{m['id']} – {m['title']}" for m in meetings],
    )
    mid = int(selected_id.split("–")[0].replace("#", "").strip())

    if st.button("Load Meeting"):
        data, err = call_api(f"/meetings/{mid}")
        if err:
            st.error(err)
        else:
            st.markdown(f"### {data['title']}")
            st.markdown(f"**Summary:** {data.get('summary', 'N/A')}")
            st.markdown("**Tasks:**")
            for t in data.get("tasks", []):
                st.markdown(
                    f'<div class="task-row"><div class="task-title">{t["task"]}</div>'
                    f'<div class="task-meta">👤 {t["owner"]} | {priority_badge(t["priority"])} | 📅 {t["due_date"]}</div></div>',
                    unsafe_allow_html=True,
                )

            # Download buttons
            st.markdown("**Download:**")
            dc1, dc2, dc3 = st.columns(3)
            for col, fmt in [(dc1, "md"), (dc2, "json"), (dc3, "txt")]:
                with col:
                    try:
                        raw = requests.get(f"{API_BASE}/download/{mid}/{fmt}", timeout=10)
                        col.download_button(
                            f"⬇️ .{fmt.upper()}",
                            data=raw.content,
                            file_name=f"meeting_{mid}.{fmt}",
                            use_container_width=True,
                        )
                    except Exception:
                        pass


# ════════════════════════════════════════════════════════════════════════════════
# ABOUT
# ════════════════════════════════════════════════════════════════════════════════
elif page == "ℹ️ About":
    st.markdown('<div class="hero-title" style="font-size:2rem">ℹ️ About</div>',
                unsafe_allow_html=True)
    st.markdown("""
    ## Meeting-to-Task Automation System

    A **100% free**, student-friendly tool that converts meeting audio or transcripts into
    structured, actionable tasks.

    ### Tech Stack
    | Layer | Technology |
    |-------|-----------|
    | Backend API | Python + FastAPI |
    | Frontend | Streamlit |
    | Transcription | faster-whisper (CPU) |
    | AI Extraction | Regex + Ollama / Gemini free tier |
    | Database | SQLite (built-in) |
    | Reports | Markdown, JSON, TXT |

    ### Free LLM Options
    - **Regex mode** – no API, works offline
    - **Ollama** – run Mistral / Llama 3 locally (free, 8 GB RAM)
    - **Google Gemini** – free tier (15 req/min)
    - **OpenRouter** – free Mistral-7B tier

    ### Cost
    **$0.00** – no paid APIs required.

    ---
    Built with ❤️ for university students.
    """)
