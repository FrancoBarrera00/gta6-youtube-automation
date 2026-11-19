"""FFmpeg 5.1.9 video/audio assembler for GTA VI YouTube (16:9) & Shorts (9:16)."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path

from gta6_pipeline.config import DEFAULT_FONT_CANDIDATES


def _find_font_file() -> str | None:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "'\\''")
        .replace("%", "\\%")
    )


def _escape_filter_path(path: Path) -> str:
    """Escape a file path for FFmpeg filter arguments (subtitles, fontfile)."""
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def assemble_video(
    video_path: Path,
    audio_path: Path,
    out_path: Path,
    short: bool = False,
    credit: str | None = None,
    srt_path: Path | None = None,
) -> Path:
    """Mute original video audio, mux Spanish voiceover, and apply optional Shorts crop/credit/SRT."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg binary not found in PATH.")
    if not video_path.is_file():
        raise FileNotFoundError(f"Input video not found: {video_path}")
    if not audio_path.is_file():
        raise FileNotFoundError(f"Input audio not found: {audio_path}")
    if srt_path is not None and not srt_path.is_file():
        raise FileNotFoundError(f"Subtitle file not found: {srt_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with (tempfile.TemporaryDirectory() if credit else nullcontext()) as credit_tmp_dir:
        vf_filters: list[str] = []
        if short:
            vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
            vf_filters.append("crop=1080:1920")
            vf_filters.append("setsar=1")

        if credit:
            credit_file = Path(credit_tmp_dir) / "credit.txt"
            credit_file.write_text(credit, encoding="utf-8")
            font_file = _find_font_file()
            font_arg = f":fontfile='{_escape_filter_path(Path(font_file))}'" if font_file else ""
            vf_filters.append(
                f"drawtext=textfile='{_escape_filter_path(credit_file)}':expansion=none{font_arg}"
                ":fontsize=32:fontcolor=white:x=(w-text_w)/2:y=60"
                ":box=1:boxcolor=black@0.65:boxborderw=10"
            )

        if srt_path is not None:
            vf_filters.append(f"subtitles='{_escape_filter_path(srt_path)}'")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
        ]

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(out_path),
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )

    if not out_path.is_file() or out_path.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg produced an empty output file: {out_path}")

    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gta6_pipeline.assemble_video",
        description="Assemble copyright-safe GTA VI YouTube/Shorts MP4 (mutes original audio, adds voiceover, 9:16 crop, credit).",
    )
    parser.add_argument("--video", required=True, type=Path, help="Input video file (.mp4).")
    parser.add_argument("--audio", required=True, type=Path, help="Input voiceover audio (.mp3 or .wav).")
    parser.add_argument("--out", required=True, type=Path, help="Output video file (.mp4).")
    parser.add_argument(
        "--short",
        action="store_true",
        help="Convert output to 9:16 vertical Shorts format (1080x1920).",
    )
    parser.add_argument(
        "--credit",
        default=None,
        help='Optional Fair Use attribution overlay text, e.g. "Clip: @JasonTheWeen".',
    )
    parser.add_argument(
        "--srt",
        type=Path,
        default=None,
        help="Optional subtitle file (.srt) to burn into the video.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        out_file = assemble_video(
            video_path=args.video,
            audio_path=args.audio,
            out_path=args.out,
            short=args.short,
            credit=args.credit,
            srt_path=args.srt,
        )
        size_mb = out_file.stat().st_size / (1024 * 1024)
        print(f"[assemble_video] Created {out_file} ({size_mb:.2f} MB).")
        return 0
    except Exception as exc:
        print(f"[assemble_video] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
