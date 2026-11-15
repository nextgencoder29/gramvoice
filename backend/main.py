from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile, os, httpx, json
from rag import query_schemes
from tts import speak

app = FastAPI(title="GramVoice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "YOUR_SARVAM_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY",   "YOUR_GROQ_KEY")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query/voice")
async def voice_query(audio: UploadFile = File(...), lang: str = "hi-IN"):
    """
    Full pipeline:
      1. Save uploaded audio
      2. Transcribe via Sarvam STT
      3. RAG lookup
      4. LLM simplification via Groq
      5. TTS via Sarvam
      6. Return audio file
    """
    # -- 1. Save audio to temp file --
    suffix = os.path.splitext(audio.filename)[-1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        audio_path = tmp.name

    try:
        # -- 2. Speech-to-Text (Sarvam) --
        transcript = await transcribe(audio_path, lang)

        # -- 3. RAG: retrieve relevant scheme info --
        context = query_schemes(transcript)

        # -- 4. LLM simplification (Groq / Llama-3) --
        answer = await simplify(transcript, context, lang)

        # -- 5. Text-to-Speech (Sarvam) --
        tts_path = await speak(answer, lang)

        return FileResponse(tts_path, media_type="audio/wav",
                            headers={"X-Transcript": transcript,
                                     "X-Answer": answer})
    finally:
        os.unlink(audio_path)


@app.post("/query/text")
async def text_query(body: dict):
    """Handy for testing without audio."""
    question = body.get("question", "")
    lang     = body.get("lang", "hi-IN")
    context  = query_schemes(question)
    answer   = await simplify(question, context, lang)
    return {"question": question, "answer": answer, "context_used": context[:300]}


# ── helpers ────────────────────────────────────────────────────────────────────

async def transcribe(audio_path: str, lang: str) -> str:
    """Sarvam AI speech-to-text."""
    url = "https://api.sarvam.ai/speech-to-text"
    with open(audio_path, "rb") as f:
        files  = {"file": ("audio.wav", f, "audio/wav")}
        data   = {"language_code": lang, "model": "saarika:v2"}
        headers = {"api-subscription-key": SARVAM_API_KEY}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, data=data, files=files)
    if r.status_code != 200:
        raise HTTPException(502, f"Sarvam STT error: {r.text}")
    return r.json().get("transcript", "")


async def simplify(question: str, context: str, lang: str) -> str:
    """Groq Llama-3 for a simple, rural-friendly answer."""
    system = (
        "You are a helpful government scheme advisor for rural Indian citizens. "
        "Answer in simple, short sentences (2-3 max). "
        "Use the provided context only. "
        f"Reply in the same language as the question (language code: {lang}). "
        "If unsure, say 'Please visit your nearest Panchayat office.'"
    )
    user_msg = f"Context:\n{context}\n\nQuestion: {question}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_msg},
        ],
        "max_tokens": 200,
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.groq.com/openai/v1/chat/completions",
                              headers=headers, json=payload)
    if r.status_code != 200:
        raise HTTPException(502, f"Groq error: {r.text}")
    return r.json()["choices"][0]["message"]["content"].strip()
