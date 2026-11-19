"""Tier 5 E2E Tests: Adversarial Hardening, Edge Cases & Media/Metadata Invariants."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from tests.e2e.helpers import (
    AUDIO_DIR,
    EXPECTED_LONG_VIDEO,
    EXPECTED_SCRIPT_STEMS,
    EXPECTED_SHORTS,
    GUIONES_DIR,
    PROJECT_ROOT,
    ffmpeg_detect_max_volume_db,
    ffprobe_inspect,
    generate_silent_wav,
    generate_synthetic_16_9_video,
    get_duration_seconds,
    get_streams,
    load_bugs_json,
    normalize_metadata_entries,
    run_cli,
)


class TestTier5GeminiWorkflowAdversarial(unittest.TestCase):
    """Adversarial CLI checks for gta6_pipeline.gemini_workflow."""

    def test_per_mode_missing_required_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "out.dat"
            for mode in ("analyze", "tts", "thumbnail", "broll"):
                with self.subTest(mode=mode):
                    proc = run_cli(
                        "gta6_pipeline.gemini_workflow",
                        ["--mode", mode, "--out", str(out_file)],
                        timeout=30,
                    )
                    combined = proc.stdout + "\n" + proc.stderr
                    self.assertNotEqual(
                        proc.returncode,
                        0,
                        f"--mode {mode} without required args should exit non-zero",
                    )
                    self.assertNotIn("Traceback (most recent call last)", combined)

    def test_invalid_mode_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "out.dat"
            proc = run_cli(
                "gta6_pipeline.gemini_workflow",
                ["--mode", "invalid_stage", "--out", str(out_file)],
                timeout=30,
            )
            combined = proc.stdout + "\n" + proc.stderr
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotIn("Traceback (most recent call last)", combined)

    def test_whitespace_only_api_key_rejected_locally(self) -> None:
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = "   \t\n  "
        env.pop("GOOGLE_API_KEY", None)

        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "script.txt"
            proc = run_cli(
                "gta6_pipeline.gemini_workflow",
                [
                    "--mode",
                    "script",
                    "--topic",
                    "bug barco gta 6",
                    "--out",
                    str(out_file),
                ],
                env=env,
                timeout=30,
            )
            combined = proc.stdout + "\n" + proc.stderr
            self.assertEqual(
                proc.returncode,
                2,
                f"Expected exit code 2 for whitespace-only GEMINI_API_KEY, got {proc.returncode}:\n{combined}",
            )
            self.assertIn("GEMINI_API_KEY", combined)
            self.assertNotIn("Traceback (most recent call last)", combined)

    def test_missing_input_files_in_tts_and_analyze(self) -> None:
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = "dummy-local-test-key"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)

            proc_tts = run_cli(
                "gta6_pipeline.gemini_workflow",
                [
                    "--mode",
                    "tts",
                    "--script",
                    str(tmp_dir / "missing_script.txt"),
                    "--out",
                    str(tmp_dir / "out.wav"),
                ],
                env=env,
                timeout=30,
            )
            self.assertNotEqual(proc_tts.returncode, 0)
            self.assertNotIn(
                "Traceback (most recent call last)",
                proc_tts.stdout + "\n" + proc_tts.stderr,
            )

            proc_analyze = run_cli(
                "gta6_pipeline.gemini_workflow",
                [
                    "--mode",
                    "analyze",
                    "--video",
                    str(tmp_dir / "missing_video.mp4"),
                    "--out",
                    str(tmp_dir / "analysis.json"),
                ],
                env=env,
                timeout=30,
            )
            self.assertNotEqual(proc_analyze.returncode, 0)
            self.assertNotIn(
                "Traceback (most recent call last)",
                proc_analyze.stdout + "\n" + proc_analyze.stderr,
            )


class TestTier5TTSOfflineAdversarial(unittest.TestCase):
    """Adversarial CLI checks for gta6_pipeline.tts_offline."""

    def test_cue_only_script_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            script_path = tmp_dir / "cues_only.txt"
            script_path.write_text("[pausa] <laugh> [musica]", encoding="utf-8")
            out_mp3 = tmp_dir / "out.mp3"

            proc = run_cli(
                "gta6_pipeline.tts_offline",
                ["--script", str(script_path), "--out", str(out_mp3)],
                timeout=30,
            )
            combined = proc.stdout + "\n" + proc.stderr
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotIn("Traceback (most recent call last)", combined)
            self.assertFalse(out_mp3.exists())

    def test_missing_script_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            proc = run_cli(
                "gta6_pipeline.tts_offline",
                [
                    "--script",
                    str(tmp_dir / "nonexistent.txt"),
                    "--out",
                    str(tmp_dir / "out.mp3"),
                ],
                timeout=30,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotIn(
                "Traceback (most recent call last)",
                proc.stdout + "\n" + proc.stderr,
            )

    def test_non_mp3_output_extension_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            script_path = tmp_dir / "valid.txt"
            script_path.write_text("Hola mundo en GTA 6.", encoding="utf-8")
            out_wav = tmp_dir / "out.wav"

            proc = run_cli(
                "gta6_pipeline.tts_offline",
                ["--script", str(script_path), "--out", str(out_wav)],
                timeout=30,
            )
            combined = proc.stdout + "\n" + proc.stderr
            self.assertNotEqual(
                proc.returncode,
                0,
                f"tts_offline must reject non-.mp3 extension, got exit 0:\n{combined}",
            )
            self.assertIn(".mp3", combined.lower())
            self.assertNotIn("Traceback (most recent call last)", combined)
            self.assertFalse(out_wav.exists())


class TestTier5AssembleVideoAdversarial(unittest.TestCase):
    """Adversarial CLI checks for gta6_pipeline.assemble_video."""

    def test_missing_video_audio_and_srt_exit_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            valid_vid = generate_synthetic_16_9_video(tmp_dir / "vid.mp4", duration_sec=3)
            valid_aud = generate_silent_wav(tmp_dir / "aud.wav", duration_sec=3)

            cases = [
                (
                    "missing_video",
                    [
                        "--video",
                        str(tmp_dir / "nope.mp4"),
                        "--audio",
                        str(valid_aud),
                        "--out",
                        str(tmp_dir / "out1.mp4"),
                    ],
                ),
                (
                    "missing_audio",
                    [
                        "--video",
                        str(valid_vid),
                        "--audio",
                        str(tmp_dir / "nope.wav"),
                        "--out",
                        str(tmp_dir / "out2.mp4"),
                    ],
                ),
                (
                    "missing_srt",
                    [
                        "--video",
                        str(valid_vid),
                        "--audio",
                        str(valid_aud),
                        "--srt",
                        str(tmp_dir / "nope.srt"),
                        "--out",
                        str(tmp_dir / "out3.mp4"),
                    ],
                ),
            ]
            for label, args in cases:
                with self.subTest(case=label):
                    proc = run_cli("gta6_pipeline.assemble_video", args, timeout=30)
                    combined = proc.stdout + "\n" + proc.stderr
                    self.assertNotEqual(proc.returncode, 0)
                    self.assertNotIn("Traceback (most recent call last)", combined)

    def test_credit_with_special_chars_and_accents_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            raw_vid = generate_synthetic_16_9_video(tmp_dir / "in.mp4", duration_sec=3)
            aud_wav = generate_silent_wav(tmp_dir / "in.wav", duration_sec=3)
            out_mp4 = tmp_dir / "out_special_credit.mp4"

            special_credit = 'Clip: @O\'Connor "Análisis" 100% — camión/acción'
            proc = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(raw_vid),
                    "--audio",
                    str(aud_wav),
                    "--out",
                    str(out_mp4),
                    "--short",
                    "--credit",
                    special_credit,
                ],
                timeout=60,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"assemble_video failed with special credit:\n{proc.stdout}\n{proc.stderr}",
            )
            self.assertTrue(out_mp4.is_file() and out_mp4.stat().st_size > 10_000)

            probe = ffprobe_inspect(out_mp4)
            v_streams = get_streams(probe, "video")
            a_streams = get_streams(probe, "audio")
            self.assertEqual(len(v_streams), 1)
            self.assertEqual(len(a_streams), 1)
            self.assertEqual(int(v_streams[0].get("width", 0)), 1080)
            self.assertEqual(int(v_streams[0].get("height", 0)), 1920)


class TestTier5AudioAndMetadataInvariants(unittest.TestCase):
    """Deep invariants across generated MP3s, BUGS_VERIFICADOS.json, and metadata_youtube.json."""

    def test_all_mp3s_non_silent_stream_properties_and_shorts_cap(self) -> None:
        for stem in EXPECTED_SCRIPT_STEMS:
            mp3_path = AUDIO_DIR / f"{stem}.mp3"
            with self.subTest(stem=stem):
                self.assertTrue(mp3_path.is_file(), f"Missing MP3: {mp3_path}")

                max_db = ffmpeg_detect_max_volume_db(mp3_path)
                self.assertGreater(
                    max_db,
                    -20.0,
                    f"{mp3_path.name} max_volume={max_db:.2f} dB is too quiet (expected > -20.0 dB)",
                )

                probe = ffprobe_inspect(mp3_path)
                a_streams = get_streams(probe, "audio")
                self.assertEqual(len(a_streams), 1)
                stream = a_streams[0]
                self.assertEqual(stream.get("codec_name"), "mp3")
                self.assertEqual(int(stream.get("sample_rate", 0)), 24000)
                self.assertEqual(stream.get("channel_layout"), "mono")

                if stem in EXPECTED_SHORTS:
                    dur = get_duration_seconds(probe)
                    self.assertLessEqual(
                        dur,
                        180.0,
                        f"Short {mp3_path.name} exceeds 180s cap: {dur:.2f}s",
                    )

    def test_bugs_verificados_has_unique_ids_across_all_9_entries(self) -> None:
        bugs = load_bugs_json()
        self.assertEqual(len(bugs), 9, f"Expected 9 bug entries, found {len(bugs)}")
        ids = [b.get("id") for b in bugs]
        self.assertTrue(all(isinstance(i, str) and i.strip() for i in ids))
        self.assertEqual(
            len(ids),
            len(set(ids)),
            f"Duplicate bug IDs found in BUGS_VERIFICADOS.json: {ids}",
        )

    def test_metadata_youtube_files_tags_credits_and_chapter_timestamps(self) -> None:
        meta_raw = json.loads(
            (GUIONES_DIR / "metadata_youtube.json").read_text(encoding="utf-8")
        )
        entries = normalize_metadata_entries(meta_raw)

        for stem in EXPECTED_SCRIPT_STEMS:
            with self.subTest(stem=stem):
                self.assertIn(stem, entries)
                entry = entries[stem]

                script_rel = entry.get("script_file", "")
                audio_rel = entry.get("audio_file", "")
                self.assertTrue(
                    isinstance(script_rel, str)
                    and (PROJECT_ROOT / script_rel).is_file(),
                    f"{stem}: script_file does not exist on disk: {script_rel!r}",
                )
                self.assertTrue(
                    isinstance(audio_rel, str)
                    and (PROJECT_ROOT / audio_rel).is_file(),
                    f"{stem}: audio_file does not exist on disk: {audio_rel!r}",
                )

                tags = entry.get("tags")
                self.assertTrue(
                    isinstance(tags, list) and len(tags) > 0,
                    f"{stem}: tags must be a non-empty list",
                )

                creator_credit = entry.get("creator_credit")
                self.assertTrue(
                    isinstance(creator_credit, str) and bool(creator_credit.strip()),
                    f"{stem}: creator_credit must be a non-empty string",
                )

        # Verify long video chapter timestamps are strictly less than actual MP3 duration
        long_entry = entries[EXPECTED_LONG_VIDEO]
        long_desc = long_entry["description_es"]
        timestamps = re.findall(r"(?m)^(\d{2}):(\d{2})\b", long_desc)
        self.assertGreaterEqual(
            len(timestamps),
            2,
            "Expected chapter timestamps in video_largo_compilacion_bugs description_es",
        )

        long_mp3 = PROJECT_ROOT / long_entry["audio_file"]
        actual_duration = get_duration_seconds(ffprobe_inspect(long_mp3))
        for mm, ss in timestamps:
            chapter_sec = int(mm) * 60 + int(ss)
            self.assertLess(
                chapter_sec,
                actual_duration,
                f"Chapter timestamp {mm}:{ss} ({chapter_sec}s) >= MP3 duration ({actual_duration:.2f}s)",
            )


if __name__ == "__main__":
    unittest.main()
