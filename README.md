# GramVoice — 1-Hour Build Guide

> Voice-first government scheme assistant for rural India

---

## ⏱ The 1-Hour Plan

| Time | Task | Done? |
|------|------|-------|
| 0:00 – 0:10 | Get API keys (Groq + Sarvam) | ☐ |
| 0:10 – 0:25 | Set up backend + ingest data | ☐ |
| 0:25 – 0:35 | Test RAG + LLM via `/query/text` | ☐ |
| 0:35 – 0:50 | Open frontend, test voice in browser | ☐ |
| 0:50 – 1:00 | Demo run with 3 scripted questions | ☐ |

---

## Step 1 — Get Keys (0:00 – 0:10)

### Groq (required — free, instant)
1. Go to https://console.groq.com
2. Sign up → API Keys → Create key
3. Copy key starting with `gsk_...`

### Sarvam AI (recommended — free tier)
1. Go to https://www.sarvam.ai
2. Sign up → Dashboard → API Key
3. Copy the subscription key

---

## Step 2 — Configure & Install (0:10 – 0:20)

```bash
cd gramvoice

# Set your keys
cp .env.example .env
nano .env          # paste your keys

source .env        # load them into shell

# Install deps
cd backend
pip install -r requirements.txt
```

---

## Step 3 — Build the Knowledge Base (0:20 – 0:25)

The `data/schemes/` folder already has 3 schemes (PM-KISAN, Ayushman Bharat, PMAY-G).

**Optional — add more PDFs:**
Download any from https://india.gov.in/topics/government-schemes and drop into `data/schemes/`.

```bash
# From backend/ folder:
python rag.py --ingest

# Test a query:
python rag.py --query "PM KISAN ke liye documents kya chahiye?"
```

---

## Step 4 — Start the Backend (0:25 – 0:35)

```bash
# From backend/ folder:
bash start.sh

# Server will be live at http://localhost:8000
# Test in browser: http://localhost:8000/health
```

**Test the text API:**
```bash
curl -X POST http://localhost:8000/query/text \
  -H "Content-Type: application/json" \
  -d '{"question": "PM KISAN ke liye kaise apply karein?", "lang": "hi-IN"}'
```

---

## Step 5 — Open the Frontend (0:35 – 0:50)

Simply open `frontend/index.html` in Chrome.

```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# Windows
start frontend/index.html
```

Allow microphone access when prompted.

---

## Step 6 — Demo Run (0:50 – 1:00)

Use the **pill buttons** to test without voice first, then test voice.

### 3 Scripted Demo Questions:

| Hindi | English |
|-------|---------|
| PM KISAN ke liye kaise apply karein? | How to apply for PM-KISAN? |
| Ayushman Bharat mein kya kya cover hota hai? | What's covered under Ayushman Bharat? |
| Pradhan Mantri Awas Yojana ke liye kaun eligible hai? | Who is eligible for PMAY? |

### Demo the offline feature (impresses judges!):
1. Turn off WiFi
2. Record a query → it shows in the orange queue
3. Turn WiFi back on → it auto-syncs and responds

---

## Project Structure

```
gramvoice/
├── backend/
│   ├── main.py          ← FastAPI app (full pipeline)
│   ├── rag.py           ← ChromaDB + LangChain RAG
│   ├── tts.py           ← Sarvam TTS (with gTTS fallback)
│   ├── requirements.txt
│   └── start.sh         ← One-command setup
├── frontend/
│   └── index.html       ← Voice UI (open directly in browser)
├── data/
│   ├── schemes/         ← Add PDFs/TXTs here
│   └── chroma_db/       ← Auto-created after ingestion
└── .env.example
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Sarvam STT returns error | Check API key; gTTS fallback activates for TTS automatically |
| CORS error in browser | Make sure backend is running on port 8000 |
| No schemes returned | Re-run `python rag.py --ingest` |
| Mic not working | Use Chrome; allow mic permissions |

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Backend | FastAPI + Python |
| Speech-to-Text | Sarvam AI (IndicWav2Vec-v2) |
| Vector DB | ChromaDB (local) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| LLM | Groq + Llama-3-8B |
| Text-to-Speech | Sarvam AI Bulbul-v1 |
| Frontend | Vanilla HTML/CSS/JS |
