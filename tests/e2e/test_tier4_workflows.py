"""Tier 4 E2E Tests: Real-World End-to-End Production Workflows."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.e2e.helpers import (
    EXPECTED_SCRIPT_STEMS,
    EXPECTED_SHORTS,
    GUIONES_DIR,
    ffprobe_inspect,
    generate_synthetic_16_9_video,
    get_duration_seconds,
    get_streams,
    is_spanish_text,
    normalize_metadata_entries,
    run_cli,
)


def _extract_str_field(entry: dict, candidates: tuple[str, ...]) -> str:
    for key in candidates:
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


class TestTier4EndToEndWorkflows(unittest.TestCase):
    """Real-world end-to-end production & YouTube upload readiness workflows."""

    def test_full_script_to_tts_to_short_video_workflow(self) -> None:
        script_path = GUIONES_DIR / f"{EXPECTED_SHORTS[1]}.txt"
        self.assertTrue(script_path.is_file(), f"Missing script {script_path}")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            generated_mp3 = tmp_dir / "voiceover.mp3"
            raw_16_9 = generate_synthetic_16_9_video(
                tmp_dir / "gameplay_16_9.mp4", duration_sec=6
            )
            final_mp4 = tmp_dir / "youtube_short_ready.mp4"

            # Step 1: Generate Spanish TTS audio offline from real script
            proc_tts = run_cli(
                "gta6_pipeline.tts_offline",
                ["--script", str(script_path), "--out", str(generated_mp3)],
                timeout=120,
            )
            self.assertEqual(
                proc_tts.returncode,
                0,
                f"tts_offline failed (exit {proc_tts.returncode}):\n"
                f"STDOUT:\n{proc_tts.stdout}\nSTDERR:\n{proc_tts.stderr}",
            )
            self.assertTrue(
                generated_mp3.is_file() and generated_mp3.stat().st_size > 1024,
                "tts_offline did not produce a valid non-empty MP3",
            )
            mp3_probe = ffprobe_inspect(generated_mp3)
            self.assertGreaterEqual(
                len(get_streams(mp3_probe, "audio")),
                1,
                "Generated TTS MP3 has no audio stream",
            )
            self.assertGreater(
                get_duration_seconds(mp3_probe),
                5.0,
                "Generated TTS MP3 duration is unexpectedly short",
            )

            # Step 2: Assemble 9:16 Short with muted game audio & Fair Use credit
            proc_asm = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(raw_16_9),
                    "--audio",
                    str(generated_mp3),
                    "--out",
                    str(final_mp4),
                    "--short",
                    "--credit",
                    "Clip: @gta6_creator_e2e",
                ],
                timeout=120,
            )
            self.assertEqual(
                proc_asm.returncode,
                0,
                f"assemble_video failed (exit {proc_asm.returncode}):\n"
                f"STDOUT:\n{proc_asm.stdout}\nSTDERR:\n{proc_asm.stderr}",
            )
            self.assertTrue(
                final_mp4.is_file() and final_mp4.stat().st_size > 10_000,
                "Final assembled Short MP4 missing or too small",
            )

            final_probe = ffprobe_inspect(final_mp4)
            v_streams = get_streams(final_probe, "video")
            a_streams = get_streams(final_probe, "audio")
            self.assertEqual(len(v_streams), 1)
            self.assertEqual(len(a_streams), 1)
            self.assertEqual(int(v_streams[0].get("width", 0)), 1080)
            self.assertEqual(int(v_streams[0].get("height", 0)), 1920)
            self.assertGreater(get_duration_seconds(final_probe), 1.0)

    def test_youtube_upload_readiness_metadata_and_fair_use(self) -> None:
        meta_raw = json.loads(
            (GUIONES_DIR / "metadata_youtube.json").read_text(encoding="utf-8")
        )
        entries = normalize_metadata_entries(meta_raw)

        for stem in EXPECTED_SCRIPT_STEMS:
            self.assertIn(stem, entries, f"Missing metadata for {stem}")
            entry = entries[stem]

            title = _extract_str_field(entry, ("title", "titulo", "title_es"))
            desc = _extract_str_field(
                entry, ("description", "descripcion", "description_es")
            )
            credit = _extract_str_field(
                entry,
                (
                    "creator_credit",
                    "credit",
                    "attribution",
                    "fair_use_attribution",
                    "atribucion",
                    "fuente",
                ),
            )
            tags = entry.get("tags") or entry.get("etiquetas") or []

            self.assertTrue(title, f"{stem}: missing YouTube title")
            self.assertLessEqual(
                len(title),
                100,
                f"{stem}: YouTube title exceeds 100 chars ({len(title)})",
            )
            self.assertTrue(desc, f"{stem}: missing YouTube description")
            self.assertTrue(
                is_spanish_text(f"{title}\n{desc}"),
                f"{stem}: metadata title/description must be in Spanish",
            )

            # Fair Use attribution / credit must appear in description or dedicated credit field
            combined_attr = f"{desc}\n{credit}".lower()
            self.assertTrue(
                any(
                    kw in combined_attr
                    for kw in (
                        "clip",
                        "crédito",
                        "credito",
                        "credit",
                        "fair use",
                        "fuente",
                        "autor",
                        "creador",
                        "@",
                    )
                ),
                f"{stem}: missing Fair Use attribution/credit in metadata",
            )

            if isinstance(tags, list):
                tags_joined = " ".join(str(t) for t in tags).lower()
            else:
                tags_joined = str(tags).lower()

            if stem in EXPECTED_SHORTS:
                shorts_blob = f"{title}\n{desc}\n{tags_joined}".lower()
                self.assertIn(
                    "#shorts",
                    shorts_blob,
                    f"{stem}: Shorts metadata must include #Shorts marker",
                )


if __name__ == "__main__":
    unittest.main()
