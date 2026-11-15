#!/bin/bash
# GramVoice — one-shot setup & run script
# Usage: bash start.sh

set -e

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║        GramVoice — Setup & Run        ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# ── 0. Check env vars ──────────────────────────────────────────────────────────
if [ -z "$SARVAM_API_KEY" ] || [ "$SARVAM_API_KEY" = "YOUR_SARVAM_KEY" ]; then
  echo "⚠️  SARVAM_API_KEY not set — will use gTTS fallback for TTS."
  echo "   Get a free key at: https://www.sarvam.ai"
fi
if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "YOUR_GROQ_KEY" ]; then
  echo "❌ GROQ_API_KEY is required!"
  echo "   Get a free key at: https://console.groq.com"
  echo "   Then run: export GROQ_API_KEY=your_key"
  exit 1
fi

# ── 1. Install dependencies ────────────────────────────────────────────────────
echo ""
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

# ── 2. Build vector DB ─────────────────────────────────────────────────────────
echo ""
echo "📚 Building scheme knowledge base..."
python rag.py --ingest

# ── 3. Start server ────────────────────────────────────────────────────────────
echo ""
echo "🚀 Starting GramVoice server on http://localhost:8000"
echo "   Open frontend/index.html in your browser"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
