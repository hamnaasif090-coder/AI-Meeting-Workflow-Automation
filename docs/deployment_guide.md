# 🚀 Free Deployment Guide

## Overview of Free Hosting Options

| Platform | Best For | Free Tier | Limitations |
|----------|----------|-----------|-------------|
| **Streamlit Cloud** | Frontend UI | Forever free | No local Whisper |
| **Railway** | Backend API | $5 credit/month | Sleeps after inactivity |
| **Render** | Backend API | 750 hrs/month | Spins down after 15 min |
| **Ngrok** | Local sharing | Free tunnel | Temporary URL |

---

## 🌐 Option 1: Streamlit Cloud (Frontend) + Railway (Backend)

### Step 1: Prepare Repository

```bash
# Add .gitignore
cat > .gitignore << 'EOF'
.env
uploads/
reports/
transcripts/
database/
__pycache__/
*.pyc
venv/
.venv/
*.db
*.sqlite
EOF

# Commit everything
git add .
git commit -m "Initial commit: Meeting-to-Task System"
git push origin main
```

### Step 2: Deploy Backend to Railway

1. Go to **railway.app** → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway auto-detects Python — click **"Deploy"**
5. Add environment variables (Settings → Variables):
   ```
   LLM_BACKEND=regex
   WHISPER_MODEL=base
   ```
6. Go to Settings → **Custom Start Command**:
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
7. Copy your Railway public URL (e.g. `https://your-app.up.railway.app`)

### Step 3: Deploy Frontend to Streamlit Cloud

1. Go to **share.streamlit.io** → Sign in with GitHub
2. Click **"New app"**
3. Select your repo, branch `main`, file `frontend/app.py`
4. Expand **"Advanced settings"** → add secret:
   ```
   API_BASE_URL = https://your-app.up.railway.app
   ```
5. Click **"Deploy"**
6. Your app is live at: `https://YOUR_APP.streamlit.app`

---

## 🏠 Option 2: Run Locally + Share with Ngrok

Best for demos and development without deployment.

```bash
# Install ngrok
pip install pyngrok

# Or download from ngrok.com (free account)

# Run your app normally
bash start.sh

# In a third terminal, expose it
ngrok http 8501

# You'll get a URL like: https://abc123.ngrok.io
# Share this URL — anyone can access your app!
```

---

## 🎓 Student Tips

### Keep RAM Low
```env
WHISPER_MODEL=tiny   # Uses ~300 MB instead of ~500 MB
LLM_BACKEND=regex    # No extra RAM for LLM
```

### Speed Up Transcription on CPU
```python
# In transcription.py, already set:
compute_type="int8"   # quantised = 2-3x faster
cpu_threads=4         # uses multiple cores
```

### Free Gemini Key (Recommended for Better Extraction)
1. Go to https://aistudio.google.com/app/apikey
2. Create a free API key
3. Set in `.env`: `LLM_BACKEND=gemini` and `GEMINI_API_KEY=your_key`
4. Free tier: 15 requests/minute, 1 million tokens/day — more than enough!

---

## 🔒 Security Notes for Deployment

1. **Never commit your `.env` file** — it's in `.gitignore`
2. **Use environment variables** on cloud platforms, not hardcoded keys
3. The SQLite database is **local only** — don't expose it publicly
4. For production, add authentication to the FastAPI endpoints

---

## 📊 Resource Requirements

| Component | Min RAM | Recommended |
|-----------|---------|-------------|
| FastAPI backend | 128 MB | 256 MB |
| Streamlit frontend | 256 MB | 512 MB |
| Whisper tiny | 300 MB | — |
| Whisper base | 500 MB | 1 GB |
| Ollama mistral | 4 GB | 8 GB |
| **Total (regex mode)** | **~700 MB** | **1.5 GB** |
| **Total (Ollama mode)** | **~5 GB** | **8 GB** |

*All CPU — no GPU required.*
