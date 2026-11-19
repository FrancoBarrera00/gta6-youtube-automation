"""Configuration and verified late-2026 Gemini model IDs for gta6_pipeline."""

# Verified Late-2026 Gemini API Model Stack
GEMINI_SCRIPT_MODEL = "gemini-4-hydrogen"
GEMINI_FAST_MODEL = "gemini-3.5-flash-lite"
GEMINI_TTS_MODEL = "gemini-3.8-flash-tts"
GEMINI_TTS_LITE_MODEL = "gemini-3.8-flash-lite-tts"
GEMINI_IMAGE_MODEL = "gemini-nano-banana-2.1"
GEMINI_VIDEO_GEN_MODEL = "gemini-omni-1.2-flash"
GEMINI_BGM_MODEL = "lyria-3.5"

# Spanish TTS Voice & Pacing Defaults (edge-tts / gTTS)
DEFAULT_OFFLINE_VOICE = "es-MX-DaliaNeural"
ALTERNATIVE_OFFLINE_VOICES = (
    "es-MX-DaliaNeural",
    "es-MX-JorgeNeural",
    "es-ES-AlvaroNeural",
    "es-ES-ElviraNeural",
    "es-AR-ElenaNeural",
    "es-CO-SalomeNeural",
)
DEFAULT_TTS_RATE = "+0%"

# Gemini 3.8 Flash TTS Defaults
DEFAULT_GEMINI_TTS_STYLE = (
    "Enthusiastic, engaging Spanish gaming news YouTube narrator, "
    "clear Latin-American/neutral Spanish pronunciation, dynamic pacing"
)

# Font candidates for FFmpeg drawtext on Debian 12+
DEFAULT_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf",
    "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf",
    "/usr/share/fonts/opentype/urw-base35/URWGothic-Demi.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
