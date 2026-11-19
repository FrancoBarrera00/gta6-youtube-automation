"""Tier 3 E2E Tests: Cross-Feature Combinations & FFmpeg Assembly Integration."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.e2e.helpers import (
    AUDIO_DIR,
    DOCS_DIR,
    EXPECTED_SCRIPT_STEMS,
    EXPECTED_SHORTS,
    GUIONES_DIR,
    ffmpeg_detect_max_volume_db,
    ffprobe_inspect,
    generate_silent_wav,
    generate_synthetic_16_9_video,
    get_duration_seconds,
    get_streams,
    load_bugs_json,
    normalize_metadata_entries,
    run_cli,
    write_sample_srt,
)


class TestTier3CrossAssetConsistency(unittest.TestCase):
    """Cross-feature consistency between docs/, guiones/, metadata, and audio/."""

    def test_every_script_has_matching_audio_and_metadata(self) -> None:
        meta_raw = json.loads(
            (GUIONES_DIR / "metadata_youtube.json").read_text(encoding="utf-8")
        )
        entries = normalize_metadata_entries(meta_raw)

        for stem in EXPECTED_SCRIPT_STEMS:
            script_path = GUIONES_DIR / f"{stem}.txt"
            audio_path = AUDIO_DIR / f"{stem}.mp3"
            self.assertTrue(script_path.is_file(), f"Missing script {script_path}")
            self.assertTrue(audio_path.is_file(), f"Missing audio {audio_path}")
            self.assertIn(
                stem,
                entries,
                f"metadata_youtube.json missing entry for '{stem}' "
                f"(found keys: {sorted(entries.keys())})",
            )

    def test_bugs_catalog_aligns_with_scripts_and_metadata(self) -> None:
        bugs = load_bugs_json()
        self.assertGreaterEqual(len(bugs), 5)

        meta_raw = json.loads(
            (GUIONES_DIR / "metadata_youtube.json").read_text(encoding="utf-8")
        )
        entries = normalize_metadata_entries(meta_raw)
        self.assertEqual(
            set(entries.keys()),
            set(EXPECTED_SCRIPT_STEMS),
            "metadata_youtube.json must map 1:1 to all 6 expected scripts",
        )

        # Verify each metadata entry points to the matching script/audio and aligns with bug catalog
        scripts_by_stem = {
            stem: (GUIONES_DIR / f"{stem}.txt").read_text(encoding="utf-8").lower()
            for stem in EXPECTED_SCRIPT_STEMS
        }
        all_scripts_text = "\n".join(scripts_by_stem.values())
        all_metadata_text = json.dumps(entries, ensure_ascii=False).lower()

        # First 5 launch-day bugs must align across BUGS_VERIFICADOS.json, guiones/, and metadata_youtube.json
        expected_bug_alignments = [
            ("bug_01_boat_bridge", "short_01_barco_puente", ("jasontheween", "barco", "puente")),
            ("bug_02_lucia_falling_ground", "short_02_lucia_bajo_mapa", ("lucia", "suelo", "mapa")),
            ("bug_03_jason_cop_clipping", "short_03_jason_policia_clipping", ("michaeldoeslife", "jason", "clipping")),
            ("bug_04_flying_truck_cars", "short_04_camion_volador", ("synaptic_uk", "autos", "camion")),
            ("bug_05_bank_mission_softlock", "short_05_softlock_banco", ("softlock", "banco", "gamewatcher")),
        ]
        bugs_by_id = {b["id"]: b for b in bugs}
        for bug_id, stem, keywords in expected_bug_alignments:
            self.assertIn(bug_id, bugs_by_id, f"Missing expected bug {bug_id}")
            bug_blob = json.dumps(bugs_by_id[bug_id], ensure_ascii=False).lower()
            meta_blob = json.dumps(entries[stem], ensure_ascii=False).lower()
            script_blob = scripts_by_stem[stem]
            for kw in keywords:
                # Normalize accents for 'camion'/'camión'
                norm_bug = bug_blob.replace("ó", "o")
                norm_meta = meta_blob.replace("ó", "o")
                norm_script = script_blob.replace("ó", "o")
                self.assertIn(kw, norm_bug, f"Keyword {kw!r} missing from bug {bug_id}")
                self.assertTrue(
                    kw in norm_script or kw in norm_meta,
                    f"Keyword {kw!r} from {bug_id} missing from {stem} script and metadata",
                )

        # Verify creator attribution / topic alignment in overall scripts + metadata
        self.assertIn("jasontheween", all_metadata_text)
        self.assertIn("rockstar", all_scripts_text + "\n" + all_metadata_text)

    def test_high_risk_bugs_warn_against_step_by_step_tutorials(self) -> None:
        bugs = load_bugs_json()
        high_risk_bugs = [
            b for b in bugs if b.get("rockstar_policy_risk") == "high_avoid_tutorial"
        ]
        self.assertGreater(
            len(high_risk_bugs),
            0,
            "Expected at least one high_avoid_tutorial bug in BUGS_VERIFICADOS.json",
        )
        for bug in high_risk_bugs:
            strategy = bug["safe_usage_strategy_es"].lower()
            self.assertTrue(
                bool(re.search(r"\bno\b.*tutorial", strategy))
                or "paso a paso" in strategy,
                f"high_avoid_tutorial bug {bug['id']} must warn against step-by-step tutorials: {strategy!r}",
            )

        guia_text = (DOCS_DIR / "GUIA_COMPLETA_GTA6.md").read_text(encoding="utf-8").lower()
        self.assertIn("high_avoid_tutorial", guia_text)
        self.assertTrue(
            "no hacer tutorial" in guia_text
            or "no subir tutoriales de exploits" in guia_text
            or "paso a paso" in guia_text,
            "GUIA_COMPLETA_GTA6.md must warn against publishing step-by-step exploit tutorials",
        )


class TestTier3AssembleVideoIntegration(unittest.TestCase):
    """Cross-feature integration: FFmpeg 9:16 Shorts, 16:9 landscape, and audio muting."""

    def test_assemble_short_9_16_with_credit_and_srt(self) -> None:
        real_audio = AUDIO_DIR / f"{EXPECTED_SHORTS[0]}.mp3"
        self.assertTrue(real_audio.is_file(), f"Missing real audio {real_audio}")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            raw_video = generate_synthetic_16_9_video(
                tmp_dir / "raw_16_9.mp4", duration_sec=6
            )
            srt_file = write_sample_srt(tmp_dir / "subs.srt")
            out_video = tmp_dir / "final_short_9_16.mp4"

            proc = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(raw_video),
                    "--audio",
                    str(real_audio),
                    "--out",
                    str(out_video),
                    "--short",
                    "--credit",
                    "Clip: @testcreator",
                    "--srt",
                    str(srt_file),
                ],
                timeout=120,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"assemble_video failed (exit {proc.returncode}):\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            self.assertTrue(
                out_video.is_file() and out_video.stat().st_size > 10_000,
                f"Output video {out_video} missing or too small",
            )

            probe = ffprobe_inspect(out_video)
            video_streams = get_streams(probe, "video")
            audio_streams = get_streams(probe, "audio")
            self.assertEqual(len(video_streams), 1, "Expected exactly 1 video stream")
            self.assertEqual(len(audio_streams), 1, "Expected exactly 1 audio stream")

            v0 = video_streams[0]
            self.assertEqual(
                int(v0.get("width", 0)),
                1080,
                f"Expected 9:16 width 1080, got {v0.get('width')}",
            )
            self.assertEqual(
                int(v0.get("height", 0)),
                1920,
                f"Expected 9:16 height 1920, got {v0.get('height')}",
            )
            duration = get_duration_seconds(probe)
            self.assertGreater(duration, 1.0, f"Output duration too short: {duration}")

    def test_assemble_long_16_9_without_short_flag(self) -> None:
        real_audio = AUDIO_DIR / f"{EXPECTED_SHORTS[0]}.mp3"
        self.assertTrue(real_audio.is_file(), f"Missing real audio {real_audio}")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            raw_video = generate_synthetic_16_9_video(
                tmp_dir / "raw_16_9.mp4", duration_sec=4
            )
            out_video = tmp_dir / "final_landscape_16_9.mp4"

            proc = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(raw_video),
                    "--audio",
                    str(real_audio),
                    "--out",
                    str(out_video),
                    "--credit",
                    "Clip: @testcreator",
                ],
                timeout=120,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"assemble_video 16:9 failed (exit {proc.returncode}):\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            probe = ffprobe_inspect(out_video)
            video_streams = get_streams(probe, "video")
            audio_streams = get_streams(probe, "audio")
            self.assertEqual(len(video_streams), 1, "Expected exactly 1 video stream")
            self.assertEqual(len(audio_streams), 1, "Expected exactly 1 audio stream")

            width = int(video_streams[0].get("width", 0))
            height = int(video_streams[0].get("height", 0))
            self.assertGreater(
                width,
                height,
                f"Expected 16:9 landscape (width > height), got {width}x{height}",
            )
            self.assertEqual((width, height), (1920, 1080))
            self.assertGreater(get_duration_seconds(probe), 1.0)

    def test_assemble_video_mutes_original_game_audio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            # Synthetic 16:9 video contains a loud ~0 dB 440 Hz sine wave
            loud_game_video = generate_synthetic_16_9_video(
                tmp_dir / "loud_440hz_game.mp4", duration_sec=4
            )
            silent_vo = generate_silent_wav(tmp_dir / "silent_vo.wav", duration_sec=4)
            out_video = tmp_dir / "muted_output.mp4"

            proc = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(loud_game_video),
                    "--audio",
                    str(silent_vo),
                    "--out",
                    str(out_video),
                    "--short",
                ],
                timeout=120,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"assemble_video failed (exit {proc.returncode}):\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )

            probe = ffprobe_inspect(out_video)
            audio_streams = get_streams(probe, "audio")
            self.assertEqual(
                len(audio_streams),
                1,
                "Expected exactly 1 audio stream (original game audio must not remain)",
            )

            max_vol_db = ffmpeg_detect_max_volume_db(out_video)
            self.assertLess(
                max_vol_db,
                -40.0,
                f"Original 440Hz game audio leaked into output! max_volume={max_vol_db:.1f} dB",
            )


if __name__ == "__main__":
    unittest.main()
