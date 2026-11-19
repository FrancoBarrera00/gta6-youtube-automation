"""Full Gemini API workflow CLI (google-genai >= 2.25.0) for GTA VI Spanish content."""

import argparse
import base64
import os
import sys
from pathlib import Path

from gta6_pipeline.config import (
    DEFAULT_GEMINI_TTS_STYLE,
    GEMINI_IMAGE_MODEL,
    GEMINI_SCRIPT_MODEL,
    GEMINI_TTS_MODEL,
    GEMINI_VIDEO_GEN_MODEL,
)


def _require_api_key() -> str:
    api_key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    if not api_key:
        print(
            "Error: GEMINI_API_KEY no esta configurada.\n"
            "Obtene tu clave gratuita en Google AI Studio (https://aistudio.google.com) "
            "y ejecutala asi:\n"
            '  export GEMINI_API_KEY="tu_clave_aqui"\n'
            "(Si queres generar audio gratis sin API key, usa: "
            "python -m gta6_pipeline.tts_offline --script ... --out ...)",
            file=sys.stderr,
        )
        sys.exit(2)
    return api_key


def _get_client():
    from google import genai

    api_key = _require_api_key()
    return genai.Client(api_key=api_key)


def run_script_mode(topic: str, duration: int, out_path: Path) -> None:
    """Generate a transformative Spanish YouTube/Shorts script using gemini-4-hydrogen."""
    client = _get_client()
    prompt = (
        f"Sos un guionista experto en YouTube Gaming en español.\n"
        f"Escribi un guion de aproximadamente {duration} segundos sobre el tema:\n"
        f'"{topic}"\n\n'
        f"REGLAS OBLIGATORIAS:\n"
        f"1. Tono informativo/periodistico/entretenimiento (Fair Use transformativo): "
        f"NO finjas que jugaste el juego si el clip es de otro creador; menciona al creador.\n"
        f"2. Hook impactante en los primeros 3 segundos.\n"
        f"3. Espanol natural y dinamico, sin relleno.\n"
        f"4. Devuelve solo el guion listo para locutar."
    )
    response = client.models.generate_content(
        model=GEMINI_SCRIPT_MODEL,
        contents=prompt,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(response.text or "", encoding="utf-8")
    print(f"[gemini_workflow:script] Guion guardado en {out_path} ({GEMINI_SCRIPT_MODEL}).")


def run_analyze_mode(video: str, processing: str, out_path: Path) -> None:
    """Analyze a local video or YouTube URL for GTA VI bugs/timestamps using gemini-4-hydrogen."""
    from google.genai import types

    client = _get_client()
    prompt = (
        "Analiza este video de GTA VI en espanol. "
        "Identifica todos los bugs, glitches o momentos destacados con timestamps exactos (MM:SS), "
        "describe que ocurre en pantalla, y sugiere un hook corto en espanol para YouTube Shorts. "
        "Responde en JSON valido con la lista 'events': [{timestamp, title_es, description_es, hook_es}]."
    )

    if video.startswith("http://") or video.startswith("https://"):
        video_part = types.Part.from_uri(file_uri=video, mime_type="video/*")
    else:
        video_path = Path(video)
        if not video_path.is_file():
            raise FileNotFoundError(f"Video file not found: {video}")
        uploaded = client.files.upload(file=str(video_path))
        video_part = uploaded

    config_kwargs = {"response_mime_type": "application/json"}
    if processing == "agentic":
        # Agentic video understanding mode for long-form VODs
        config_kwargs["media_resolution"] = "MEDIA_RESOLUTION_LOW"

    response = client.models.generate_content(
        model=GEMINI_SCRIPT_MODEL,
        contents=[video_part, prompt],
        config=types.GenerateContentConfig(**config_kwargs),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(response.text or "{}", encoding="utf-8")
    print(
        f"[gemini_workflow:analyze] Analisis ({processing}) guardado en {out_path} ({GEMINI_SCRIPT_MODEL})."
    )


def run_tts_mode(script_path: Path, style: str, out_path: Path) -> None:
    """Generate native Spanish WAV voiceover using gemini-3.8-flash-tts."""
    from google.genai import types

    if not script_path.is_file():
        raise FileNotFoundError(f"Script file not found: {script_path}")

    script_text = script_path.read_text(encoding="utf-8").strip()
    if not script_text:
        raise ValueError(f"Script file is empty: {script_path}")

    client = _get_client()
    prompt = f"[Voice style: {style}]\n\n{script_text}"
    response = client.models.generate_content(
        model=GEMINI_TTS_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
        ),
    )

    audio_bytes = None
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                data = inline.data
                audio_bytes = base64.b64decode(data) if isinstance(data, str) else data
                break
        if audio_bytes:
            break

    if not audio_bytes:
        raise RuntimeError("No audio data returned by Gemini TTS model.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio_bytes)
    print(f"[gemini_workflow:tts] Audio WAV guardado en {out_path} ({GEMINI_TTS_MODEL}).")


def run_thumbnail_mode(prompt: str, out_path: Path) -> None:
    """Generate a YouTube thumbnail image using gemini-nano-banana-2.1."""
    from google.genai import types

    client = _get_client()
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    img_bytes = None
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                data = inline.data
                img_bytes = base64.b64decode(data) if isinstance(data, str) else data
                break
        if img_bytes:
            break

    if not img_bytes:
        raise RuntimeError("No image data returned by Gemini image model.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_bytes)
    print(f"[gemini_workflow:thumbnail] Miniatura guardada en {out_path} ({GEMINI_IMAGE_MODEL}).")


def run_broll_mode(prompt: str, duration: int, out_path: Path) -> None:
    """Generate B-roll video using gemini-omni-1.2-flash."""
    from google.genai import types

    client = _get_client()
    full_prompt = f"{prompt} (Duration: {duration} seconds, 1080p cinematic gaming B-roll)"
    response = client.models.generate_content(
        model=GEMINI_VIDEO_GEN_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["VIDEO"],
        ),
    )

    video_bytes = None
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                data = inline.data
                video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                break
        if video_bytes:
            break

    if not video_bytes:
        raise RuntimeError("No video data returned by Gemini Omni model.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(video_bytes)
    print(f"[gemini_workflow:broll] B-roll guardado en {out_path} ({GEMINI_VIDEO_GEN_MODEL}).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gta6_pipeline.gemini_workflow",
        description="End-to-end Gemini 2026 API workflow for GTA VI Spanish YouTube & Shorts.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["script", "analyze", "tts", "thumbnail", "broll"],
        help="Workflow stage to run.",
    )
    parser.add_argument("--topic", help="Topic for --mode script.")
    parser.add_argument("--duration", type=int, default=50, help="Target duration in seconds (script/broll).")
    parser.add_argument("--video", help="Local video path or YouTube URL for --mode analyze.")
    parser.add_argument(
        "--processing",
        choices=["static", "agentic"],
        default="static",
        help="Video processing mode for --mode analyze (default: static).",
    )
    parser.add_argument("--script", type=Path, help="Input script path for --mode tts.")
    parser.add_argument(
        "--style",
        default=DEFAULT_GEMINI_TTS_STYLE,
        help="Voice style prompt for --mode tts.",
    )
    parser.add_argument("--prompt", help="Prompt for --mode thumbnail or --mode broll.")
    parser.add_argument("--out", required=True, type=Path, help="Output file path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == "script":
            if not args.topic:
                parser.error("--topic is required for --mode script")
            run_script_mode(args.topic, args.duration, args.out)
        elif args.mode == "analyze":
            if not args.video:
                parser.error("--video is required for --mode analyze")
            run_analyze_mode(args.video, args.processing, args.out)
        elif args.mode == "tts":
            if not args.script:
                parser.error("--script is required for --mode tts")
            run_tts_mode(args.script, args.style, args.out)
        elif args.mode == "thumbnail":
            if not args.prompt:
                parser.error("--prompt is required for --mode thumbnail")
            run_thumbnail_mode(args.prompt, args.out)
        elif args.mode == "broll":
            if not args.prompt:
                parser.error("--prompt is required for --mode broll")
            run_broll_mode(args.prompt, args.duration, args.out)
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[gemini_workflow] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
