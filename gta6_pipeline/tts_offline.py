"""Offline/free Spanish TTS generator using edge-tts with gTTS fallback."""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from gta6_pipeline.config import DEFAULT_OFFLINE_VOICE, DEFAULT_TTS_RATE


def clean_script_for_tts(raw_text: str) -> str:
    """Remove bracketed stage/vocal cues like [pausa corta] or <short pause>."""
    # Remove [ ... ] stage cues and < ... > Gemini inline vocal tags
    cleaned = re.sub(r"\[[^\]]*\]", " ", raw_text)
    cleaned = re.sub(r"<[^>]*>", " ", cleaned)
    # Collapse multiple spaces/blank lines into clean sentences
    lines = [re.sub(r"\s+", " ", line).strip() for line in cleaned.splitlines()]
    return "\n".join(line for line in lines if line)


async def _generate_edge_tts(text: str, out_path: Path, voice: str, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(out_path))


def _generate_gtts(text: str, out_path: Path) -> None:
    from gtts import gTTS

    tts = gTTS(text=text, lang="es", slow=False)
    tts.save(str(out_path))


def synthesize_script(
    script_path: Path,
    out_path: Path,
    voice: str = DEFAULT_OFFLINE_VOICE,
    rate: str = DEFAULT_TTS_RATE,
) -> str:
    """Read a Spanish script file, clean cues, and synthesize an MP3 file.

    Returns the engine name used ('edge-tts' or 'gTTS').
    """
    if out_path.suffix.lower() != ".mp3":
        raise ValueError(
            f"Output file must have a .mp3 extension, got: {out_path.name!r}"
        )
    if not script_path.is_file():
        raise FileNotFoundError(f"Script file not found: {script_path}")

    raw_text = script_path.read_text(encoding="utf-8")
    cleaned_text = clean_script_for_tts(raw_text)
    if not cleaned_text.strip():
        raise ValueError(f"Script file is empty after cleaning cues: {script_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(_generate_edge_tts(cleaned_text, out_path, voice=voice, rate=rate))
        if out_path.is_file() and out_path.stat().st_size > 0:
            return "edge-tts"
        raise RuntimeError("edge-tts produced an empty file")
    except Exception as edge_err:
        print(
            f"[tts_offline] edge-tts unavailable ({edge_err}); falling back to gTTS...",
            file=sys.stderr,
        )
        _generate_gtts(cleaned_text, out_path)
        if not out_path.is_file() or out_path.stat().st_size == 0:
            raise RuntimeError("gTTS failed to produce a non-empty MP3 file")
        return "gTTS"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gta6_pipeline.tts_offline",
        description="Generate natural Spanish voiceover MP3 from a script (edge-tts + gTTS fallback).",
    )
    parser.add_argument(
        "--script",
        required=True,
        type=Path,
        help="Path to the input Spanish script (.txt).",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Path to the output audio file (.mp3).",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_OFFLINE_VOICE,
        help=f"edge-tts voice name (default: {DEFAULT_OFFLINE_VOICE}).",
    )
    parser.add_argument(
        "--rate",
        default=DEFAULT_TTS_RATE,
        help=f"Speech rate adjustment for edge-tts (default: {DEFAULT_TTS_RATE.replace('%', '%%')}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        engine = synthesize_script(
            script_path=args.script,
            out_path=args.out,
            voice=args.voice,
            rate=args.rate,
        )
        size_kb = args.out.stat().st_size / 1024
        print(f"[tts_offline] Generated {args.out} ({size_kb:.1f} KB) using {engine}.")
        return 0
    except Exception as exc:
        print(f"[tts_offline] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
