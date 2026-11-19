# Stack de Modelos Gemini (Noviembre 2026) para Automatización de GTA VI

Guía técnica con los IDs oficiales vigentes de la **Gemini API** (`google-genai >= 2.25.0`) para automatizar detección de bugs en video, guiones en español, locución TTS expresiva, miniaturas, B-roll y música libre de copyright.

---

## 1. Tabla Resumen de Modelos Recomendados

| Etapa del flujo | Modelo recomendado | Alternativa / Escala | Nivel gratuito (Free Tier) | Modelos obsoletos a EVITAR |
|---|---|---|---|---|
| **Guiones, hooks, títulos y JSON (ES)** | `gemini-4-hydrogen` | `gemini-3.5-flash-lite` (alto volumen / bajo costo) | **Sí** (ambos) | `gemini-2.5-*`, `gemini-3.8-flash` |
| **Análisis multimodal de video y bugs** | `gemini-4-hydrogen` (Static `<5m`, Agentic `>10m`) | `gemini-4-argon` / `gemini-4-carbon` | **Sí** (`hydrogen`) | — |
| **Voz en off en español (TTS)** | `gemini-3.8-flash-tts` | `gemini-3.8-flash-lite-tts` (Shorts masivos) | Consultar cuota AI Studio | `gemini-3.1-flash-tts-preview`, `gemini-2.5-*-tts` |
| **Miniaturas / Imágenes (1K–4K)** | `gemini-nano-banana-2.1` | `gemini-3-pro-image` (tipografía de estudio) | Consultar cuota AI Studio | `imagen-3.0-generate-002`, `gemini-3.1-flash-image` |
| **Video B-roll con audio nativo (3–15s)** | `gemini-omni-1.2-flash` | — | **Sí** | `veo-3.1-*-preview` (apagado el 22 oct 2026) |
| **Música de fondo libre de copyright** | `lyria-3.5` | — | Consultar cuota AI Studio | `lyria-3-clip-preview` |

---

## 2. Detalle y Precios por Modelo

### A. Texto, Guiones y Análisis Multimodal de Video
- **`gemini-4-hydrogen`** *(Modelo general por defecto)*
  - **Ventana:** 1M de tokens de entrada (texto, imagen, audio, video, PDF) y hasta 64K/1M de salida.
  - **Precio:** `$1.50` / 1M tokens de entrada · `$7.50` / 1M tokens de salida (**Free Tier disponible**).
  - **Modos de análisis de video:**
    - **Static (por defecto):** extrae 1 FPS (configurable a mayor FPS para bugs rápidos). Ideal para clips cortos `< 5 min`.
    - **Agentic (`processing="agentic"`):** inspecciona transcripciones primero y carga dinámicamente solo los segmentos visuales relevantes. Ideal para VODs largos `> 5–10 min`; reduce hasta un **88% los tokens de video** y mejora ~7% la calidad.
- **`gemini-3.5-flash-lite`** *(Alto volumen y bajo costo)*
  - **Precio:** `$0.30` / 1M tokens de entrada · `$2.50` / 1M tokens de salida (**Free Tier disponible**).
  - Ideal para generar metadatos JSON, traducciones, etiquetas y variaciones masivas de títulos/descripciones para Shorts.

### B. Voz en Off en Español (TTS) y Música
- **`gemini-3.8-flash-tts`** *(TTS insignia creativo, lanzado sept 2026)*
  - Soporta **130 idiomas** (incluyendo español natural).
  - Permite control de estilo por turno (`speech_metadata.style`, ej. `"entusiasta y dinámico"`), etiquetas vocales en línea (`<short pause>`, `<laugh>`, `<sigh>`), diseño/replicación de voz y diálogos multi-hablante.
  - **Formato de salida:** peticiones unarias (`stream=False`) devuelven `audio/wav` completo con cabecera RIFF (24 kHz, mono, PCM 16-bit); en streaming (`stream=True`) devuelve `audio/l16` sin cabecera.
- **`gemini-3.8-flash-lite-tts`** *(TTS de alto rendimiento)*
  - Soporta **101 idiomas** con esquema 100% compatible (*drop-in*) con `gemini-3.8-flash-tts`, ideal para producción masiva de Shorts.
- **`lyria-3.5`** *(Música de fondo libre de copyright)*
  - Acepta texto o imagen y genera `Audio (MP3)` + letras opcionales. Perfecto para evitar reclamos de Content ID en Shorts de 1–3 minutos.

### C. Miniaturas e Imágenes
- **`gemini-nano-banana-2.1`** *(Octubre 2026)*
  - Generación y edición conversacional en **1K, 2K y 4K**.
  - Renderizado mejorado de texto en español para miniaturas, fusión de hasta **14 imágenes de referencia** (4 personajes + 10 objetos) y *grounding* con Google Search.
- **`gemini-3-pro-image`** *(Nano Banana Pro)*
  - Motor con razonamiento para diseño gráfico de estudio y tipografía de alta precisión.

### D. Generación de Video B-Roll
- **`gemini-omni-1.2-flash`** *(GA desde el 5 de noviembre de 2026)*
  - Reemplazo oficial tras el cierre de `veo-3.1-*-preview`.
  - Genera clips de **3 a 15 segundos con audio nativo** a partir de texto, hasta 6 imágenes de referencia o video, y permite extensión multi-turno.
  - **Precio estándar:** `$12.00 / 1M tokens` (~`$0.07/s` promedio; `$0.023/s` en 360p, `$0.104/s` en 1080p, `$0.209/s` en 4K; **Free Tier disponible**).

---

## 3. Modelos Obsoletos o Apagados (NO USAR)

Usar cualquiera de estos IDs provocará errores `404` o fallos de API en noviembre de 2026:
- `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview` *(apagados el **22 de octubre de 2026** → migrar a `gemini-omni-1.2-flash`)*.
- `imagen-3.0-generate-002` *(apagado el **10 de noviembre de 2025** → migrar a `gemini-nano-banana-2.1`)*.
- `gemini-3.1-flash-image` y `gemini-3.1-flash-image-preview` *(deprecados / apagados el **25 de junio de 2026** → migrar a `gemini-nano-banana-2.1`)*.
- `gemini-3.1-flash-tts-preview`, `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts` *(reemplazados por `gemini-3.8-flash-tts` y `gemini-3.8-flash-lite-tts`)*.

---

## 4. Ejemplos en Python (`google-genai >= 2.25.0`)

Instalación previa:
```bash
pip install "google-genai>=2.25.0"
export GEMINI_API_KEY="TU_API_KEY_DE_AI_STUDIO"
```

### 4.1. Generar guion en español y metadatos JSON (`gemini-4-hydrogen`)
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-4-hydrogen",
    contents=(
        "Escribe un guion de YouTube Short (45 segundos) en español latino sobre "
        "el bug del barco atascado en el puente en GTA VI. Incluye gancho inicial, "
        "explicación técnica del fallo de colisión y cierre sin prometer hacks."
    ),
)
print(response.text)
```

### 4.2. Detectar bugs y timestamps en un video (`Static` vs `Agentic`)
```python
from google import genai
from google.genai import types

client = genai.Client()

# Para VODs largos (>10 min), usa processing="agentic" para ahorrar hasta 88% de tokens.
# Para clips cortos (<5 min), omite processing (usa Static 1 FPS por defecto).
video_part = types.Part.from_uri(
    file_uri="https://www.youtube.com/watch?v=Ek1xjfuS-U8",
    mime_type="video/mp4",
)

response = client.models.generate_content(
    model="gemini-4-hydrogen",
    contents=[
        video_part,
        "Lista cada bug visible con su timestamp exacto (MM:SS) y descripción breve en español.",
    ],
    config=types.GenerateContentConfig(
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
    ),
)
print(response.text)
```

> **Nota sobre modo Agentic:** en la Gemini API / Interactions API, al analizar VODs largos (>10 min) puedes habilitar `processing="agentic"` en la configuración de entrada de video según la documentación de `aistudio.google.com/docs/video-understanding`.

### 4.3. Generar locución en español WAV 24 kHz (`gemini-3.8-flash-tts`)
```python
import base64
from google import genai

client = genai.Client()

# Requiere google-genai >= 2.25.0 para Interactions API / output_audio
interaction = client.interactions.create(
    model="gemini-3.8-flash-tts",
    input=(
        "¡No vas a creer este bug del día uno en GTA 6! <short pause> "
        "Un barco gigante quedó atrapado vibrando en medio de un puente."
    ),
    generation_config={
        "speech_config": {
            "speech_metadata": {"style": "entusiasta y dinámico, español neutro"}
        }
    },
)

audio_bytes = base64.b64decode(interaction.output_audio.data)
with open("locucion_gta6.wav", "wb") as f:
    f.write(audio_bytes)
```

### 4.4. Generar miniatura 16:9 con texto en español (`gemini-nano-banana-2.1`)
```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-nano-banana-2.1",
    contents=(
        "Miniatura llamativa de YouTube Gaming estilo Vice City neón al atardecer, "
        "un barco gigante atascado en un puente de autopista, texto grande y legible "
        "en español: '¡BUG DÍA 1!' en amarillo y blanco con borde negro."
    ),
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K"),
    ),
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        with open("miniatura_gta6.png", "wb") as f:
            f.write(part.inline_data.data)
```
