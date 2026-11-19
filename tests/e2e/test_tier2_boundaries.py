"""Tier 2 E2E Tests: Boundary, Corner Cases, Policy Safety & Error Handling."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

from tests.e2e.helpers import (
    AUDIO_DIR,
    DOCS_DIR,
    EXPECTED_LONG_VIDEO,
    EXPECTED_SHORTS,
    ffprobe_inspect,
    get_duration_seconds,
    load_bugs_json,
    run_cli,
)


class TestTier2CLIBoundaries(unittest.TestCase):
    """CLI error handling, missing args, and missing GEMINI_API_KEY."""

    def test_missing_args_return_nonzero_without_traceback(self) -> None:
        for module in (
            "gta6_pipeline.tts_offline",
            "gta6_pipeline.gemini_workflow",
            "gta6_pipeline.assemble_video",
        ):
            with self.subTest(module=module):
                proc = run_cli(module, [], timeout=30)
                self.assertNotEqual(
                    proc.returncode,
                    0,
                    f"{module} with no args should exit non-zero",
                )
                combined = proc.stdout + "\n" + proc.stderr
                self.assertNotIn(
                    "Traceback (most recent call last)",
                    combined,
                    f"{module} raised an unhandled traceback on missing args:\n{combined}",
                )

    def test_invalid_input_paths_return_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_file = Path(tmp) / "does_not_exist.txt"
            out_file = Path(tmp) / "out.mp3"

            proc_tts = run_cli(
                "gta6_pipeline.tts_offline",
                ["--script", str(missing_file), "--out", str(out_file)],
                timeout=30,
            )
            self.assertNotEqual(proc_tts.returncode, 0)
            self.assertNotIn(
                "Traceback (most recent call last)",
                proc_tts.stdout + "\n" + proc_tts.stderr,
            )

            proc_asm = run_cli(
                "gta6_pipeline.assemble_video",
                [
                    "--video",
                    str(Path(tmp) / "missing.mp4"),
                    "--audio",
                    str(Path(tmp) / "missing.mp3"),
                    "--out",
                    str(Path(tmp) / "out.mp4"),
                ],
                timeout=30,
            )
            self.assertNotEqual(proc_asm.returncode, 0)
            self.assertNotIn(
                "Traceback (most recent call last)",
                proc_asm.stdout + "\n" + proc_asm.stderr,
            )

    def test_gemini_workflow_without_api_key_fails_gracefully(self) -> None:
        clean_env = os.environ.copy()
        clean_env.pop("GEMINI_API_KEY", None)
        clean_env.pop("GOOGLE_API_KEY", None)

        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "script.txt"
            proc = run_cli(
                "gta6_pipeline.gemini_workflow",
                [
                    "--mode",
                    "script",
                    "--topic",
                    "bug barco puente gta 6",
                    "--out",
                    str(out_file),
                ],
                env=clean_env,
                timeout=30,
            )
            combined = proc.stdout + "\n" + proc.stderr
            self.assertEqual(
                proc.returncode,
                2,
                f"gemini_workflow must exit with code 2 when GEMINI_API_KEY is unset, got {proc.returncode}:\n{combined}",
            )
            self.assertNotIn(
                "Traceback (most recent call last)",
                combined,
                f"gemini_workflow crashed with unhandled traceback when GEMINI_API_KEY unset:\n{combined}",
            )
            self.assertIn(
                "GEMINI_API_KEY",
                combined,
                f"gemini_workflow should mention GEMINI_API_KEY when unset, got:\n{combined}",
            )


class TestTier2PolicyAndMediaBoundaries(unittest.TestCase):
    """Policy compliance & realistic audio duration boundaries."""

    def test_third_party_bugs_disallow_raw_reupload(self) -> None:
        bugs = load_bugs_json()
        third_party = [
            b for b in bugs if b.get("license_type") != "official_rockstar"
        ]
        self.assertGreater(
            len(third_party),
            0,
            "Expected third-party bug clips in BUGS_VERIFICADOS.json",
        )
        for bug in third_party:
            val = bug.get("raw_reupload_allowed")
            self.assertIs(
                val,
                False,
                f"Third-party bug {bug.get('id')} must have raw_reupload_allowed === false, got {val!r}",
            )

    def test_audio_durations_are_realistic(self) -> None:
        for stem in EXPECTED_SHORTS:
            mp3_path = AUDIO_DIR / f"{stem}.mp3"
            probe = ffprobe_inspect(mp3_path)
            duration = get_duration_seconds(probe)
            self.assertGreater(
                duration,
                10.0,
                f"Short audio {mp3_path.name} too short: {duration:.2f}s (expected > 10.0s)",
            )

        long_mp3 = AUDIO_DIR / f"{EXPECTED_LONG_VIDEO}.mp3"
        long_probe = ffprobe_inspect(long_mp3)
        long_duration = get_duration_seconds(long_probe)
        self.assertGreater(
            long_duration,
            45.0,
            f"Long video audio {long_mp3.name} too short: {long_duration:.2f}s (expected > 45.0s)",
        )

    def test_guide_warns_against_raw_pov_reupload_without_facecam(self) -> None:
        guia_path = DOCS_DIR / "GUIA_COMPLETA_GTA6.md"
        content = guia_path.read_text(encoding="utf-8")
        lowered = content.lower()

        # Must explicitly address POV / facecam / reused content risk
        self.assertIn("pov", lowered, "Guide must address the user's POV question")
        self.assertTrue(
            "facecam" in lowered or "cámara" in lowered or "voz" in lowered,
            "Guide must discuss facecam/voice transformation",
        )
        self.assertTrue(
            "reutilizado" in lowered or "reused content" in lowered,
            "Guide must warn about YouTube Reused Content policy",
        )

        # Must NOT contain misleading claims encouraging raw POV re-upload as safe
        forbidden_claims = (
            r"pov\s+sin\s+facecam\s+es\s+seguro",
            r"puedes\s+subir\s+el\s+pov\s+sin\s+editar",
            r"no\s+hay\s+riesgo\s+de\s+copyright\s+si\s+solo\s+subes\s+el\s+gameplay",
        )
        for pattern in forbidden_claims:
            self.assertIsNone(
                re.search(pattern, lowered),
                f"Guide contains unsafe misinformation matching /{pattern}/",
            )


if __name__ == "__main__":
    unittest.main()
