"""Shared opaque-box helpers, fixtures, and media/CLI utilities for E2E tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
GUIONES_DIR = PROJECT_ROOT / "guiones"
AUDIO_DIR = PROJECT_ROOT / "audio"
PIPELINE_DIR = PROJECT_ROOT / "gta6_pipeline"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

EXPECTED_SHORTS = [
    "short_01_barco_puente",
    "short_02_lucia_bajo_mapa",
    "short_03_jason_policia_clipping",
    "short_04_camion_volador",
    "short_05_softlock_banco",
]
EXPECTED_LONG_VIDEO = "video_largo_compilacion_bugs"
EXPECTED_SCRIPT_STEMS = EXPECTED_SHORTS + [EXPECTED_LONG_VIDEO]

REQUIRED_GEMINI_MODELS = [
    "gemini-4-hydrogen",
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-nano-banana-2.1",
    "gemini-omni-1.2-flash",
    "lyria-3.5",
]

DEPRECATED_GEMINI_MODELS = [
    "veo-3.1",
    "imagen-3.0",
]

VALID_LICENSE_TYPES = {
    "standard_youtube",
    "social_media_standard",
    "official_rockstar",
}

VALID_ROCKSTAR_POLICY_RISKS = {
    "low",
    "medium",
    "high_avoid_tutorial",
}

REQUIRED_BUG_FIELDS = {
    "id",
    "title_es",
    "description_es",
    "creator_or_source",
    "url",
    "license_type",
    "raw_reupload_allowed",
    "safe_usage_strategy_es",
    "rockstar_policy_risk",
}


def get_python_executable() -> str:
    """Prefer /home/antigravity/.venv/bin/python when available, else sys.executable."""
    if VENV_PYTHON.exists() and os.access(VENV_PYTHON, os.X_OK):
        return str(VENV_PYTHON)
    return sys.executable


def run_cli(
    module: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Run a gta6_pipeline CLI module via subprocess from PROJECT_ROOT."""
    cmd = [get_python_executable(), "-m", module]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def ffprobe_inspect(media_path: Path) -> dict[str, Any]:
    """Inspect a media file with ffprobe and return parsed JSON metadata."""
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"ffprobe failed for {media_path} (exit {proc.returncode}): {proc.stderr}"
        )
    return json.loads(proc.stdout)


def get_streams(probe_data: dict[str, Any], codec_type: str) -> list[dict[str, Any]]:
    """Return streams matching codec_type ('audio' or 'video') from ffprobe data."""
    return [
        s for s in probe_data.get("streams", []) if s.get("codec_type") == codec_type
    ]


def get_duration_seconds(probe_data: dict[str, Any]) -> float:
    """Extract duration in seconds from ffprobe format or streams."""
    fmt_dur = probe_data.get("format", {}).get("duration")
    if fmt_dur is not None:
        return float(fmt_dur)
    for stream in probe_data.get("streams", []):
        if stream.get("duration") is not None:
            return float(stream["duration"])
    return 0.0


def generate_synthetic_16_9_video(
    out_path: Path,
    duration_sec: int = 5,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Generate a synthetic 16:9 MP4 video with a 440Hz audio track using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration_sec}:size={width}x{height}:rate=30",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_sec}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to generate synthetic test video: {proc.stderr}"
        )
    return out_path


def generate_silent_wav(out_path: Path, duration_sec: int = 4) -> Path:
    """Generate a silent mono 24kHz PCM WAV file using ffmpeg anullsrc."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=24000:cl=mono",
        "-t",
        str(duration_sec),
        "-c:a",
        "pcm_s16le",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to generate silent WAV: {proc.stderr}")
    return out_path


def ffmpeg_detect_max_volume_db(media_path: Path) -> float:
    """Run ffmpeg volumedetect filter and return max_volume in dB."""
    cmd = [
        "ffmpeg",
        "-i",
        str(media_path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise AssertionError(
            f"ffmpeg volumedetect failed for {media_path} (exit {proc.returncode}): {proc.stderr}"
        )
    match = re.search(r"max_volume:\s*([-\d.]+|-inf)\s*dB", proc.stderr)
    if not match:
        raise AssertionError(
            f"Could not parse max_volume from ffmpeg volumedetect output:\n{proc.stderr}"
        )
    raw_val = match.group(1)
    if raw_val == "-inf":
        return -100.0
    return float(raw_val)


def write_sample_srt(out_path: Path) -> Path:
    """Write a minimal valid Spanish SRT subtitle file."""
    srt_content = (
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "Bug viral de GTA VI en el lanzamiento.\n\n"
        "2\n"
        "00:00:02,000 --> 00:00:04,500\n"
        "Análisis y comentario transformativo.\n"
    )
    out_path.write_text(srt_content, encoding="utf-8")
    return out_path


def is_spanish_text(text: str) -> bool:
    """Check that text is genuinely Spanish using word-boundary regex and diacritics."""
    lowered = text.lower()
    has_spanish_chars = bool(re.search(r"[áéíóúñü¿¡]", lowered))

    spanish_function_words = (
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "que",
        "para",
        "con",
        "una",
        "por",
        "como",
        "sin",
        "pero",
        "también",
        "tambien",
        "sobre",
        "entre",
    )
    spanish_domain_words = (
        "derechos",
        "autor",
        "contenido",
        "audio",
        "modelo",
        "modelos",
        "juego",
        "video",
        "guion",
        "narración",
        "narracion",
        "español",
        "espanol",
        "crédito",
        "credito",
        "fuente",
        "análisis",
        "analisis",
    )
    func_hits = sum(
        1
        for w in spanish_function_words
        if re.search(rf"\b{re.escape(w)}\b", lowered)
    )
    domain_hits = sum(
        1
        for w in spanish_domain_words
        if re.search(rf"\b{re.escape(w)}\b", lowered)
    )
    return func_hits >= 3 and (
        has_spanish_chars or (func_hits + domain_hits) >= 6
    )


def load_bugs_json() -> list[dict[str, Any]]:
    """Load and parse docs/BUGS_VERIFICADOS.json."""
    bugs_path = DOCS_DIR / "BUGS_VERIFICADOS.json"
    data = json.loads(bugs_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise AssertionError("BUGS_VERIFICADOS.json must be a JSON array")
    return data


def normalize_metadata_entries(raw: Any) -> dict[str, dict[str, Any]]:
    """Normalize guiones/metadata_youtube.json into a stem -> entry mapping.

    Supports:
    - dict keyed by script stem or filename (e.g. "short_01_barco_puente" or "short_01_barco_puente.txt")
    - list of entry dicts containing an id/script/file/key field
    - dict wrapping a list under keys like "videos", "items", "entries", "metadata"
    """
    entries: dict[str, dict[str, Any]] = {}

    if isinstance(raw, dict):
        # Check if it's a wrapper dict containing a list
        for wrapper_key in ("videos", "items", "entries", "metadata", "scripts"):
            if wrapper_key in raw and isinstance(raw[wrapper_key], list):
                raw = raw[wrapper_key]
                break

    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                stem = Path(k).stem
                entries[stem] = v
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key_val = (
                item.get("script")
                or item.get("script_file")
                or item.get("filename")
                or item.get("id")
                or item.get("slug")
                or item.get("name")
            )
            if isinstance(key_val, str) and key_val.strip():
                entries[Path(key_val.strip()).stem] = item
    return entries
