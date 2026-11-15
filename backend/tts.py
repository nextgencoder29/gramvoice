"""
TTS via Sarvam AI — returns path to a temporary WAV file.
Falls back to gTTS if Sarvam key is missing (for testing).
"""

import os, tempfile, httpx

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Map language codes to Sarvam speaker voices
VOICE_MAP = {
    "hi-IN": "meera",
    "ta-IN": "pavithra",
    "te-IN": "arvind",
    "kn-IN": "vijay",
    "ml-IN": "anu",
    "bn-IN": "aditi",
    "mr-IN": "meera",
    "gu-IN": "meera",
    "pa-IN": "meera",
    "en-IN": "meera",
}


async def speak(text: str, lang: str = "hi-IN") -> str:
    """Convert text to speech. Returns path to temp WAV file."""
    if SARVAM_API_KEY and SARVAM_API_KEY != "YOUR_SARVAM_KEY":
        return await _sarvam_tts(text, lang)
    else:
        return await _gtts_fallback(text, lang)


async def _sarvam_tts(text: str, lang: str) -> str:
    speaker = VOICE_MAP.get(lang, "meera")
    url     = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "inputs":        [text],
        "target_language_code": lang,
        "speaker":       speaker,
        "model":         "bulbul:v1",
        "pitch":         0,
        "pace":          1.0,
        "loudness":      1.5,
        "enable_preprocessing": True,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
    r.raise_for_status()

    # Sarvam returns base64-encoded WAV
    import base64
    audio_b64 = r.json()["audios"][0]
    audio_bytes = base64.b64decode(audio_b64)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name


async def _gtts_fallback(text: str, lang: str) -> str:
    """gTTS fallback — works without API key, English only."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="hi" if "hi" in lang else "en", slow=False)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name
