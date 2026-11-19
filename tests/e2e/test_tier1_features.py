"""Tier 1 E2E Tests: Feature Coverage across Features 1-6 from PROJECT.md."""

from __future__ import annotations

import json
import re
import unittest

from tests.e2e.helpers import (
    AUDIO_DIR,
    DEPRECATED_GEMINI_MODELS,
    DOCS_DIR,
    EXPECTED_SCRIPT_STEMS,
    GUIONES_DIR,
    PIPELINE_DIR,
    REQUIRED_BUG_FIELDS,
    REQUIRED_GEMINI_MODELS,
    VALID_LICENSE_TYPES,
    VALID_ROCKSTAR_POLICY_RISKS,
    ffprobe_inspect,
    get_streams,
    is_spanish_text,
    load_bugs_json,
    run_cli,
)

PLACEHOLDER_URL_PATTERNS = (
    "example.com",
    "example.org",
    "placeholder",
    "todo",
    "tbd",
    "changeme",
    "your-url",
)

DEPRECATION_CONTEXT_MARKERS = (
    "deprecad",
    "deprecated",
    "obsolet",
    "evitar",
    "avoid",
    "no usar",
    "do not use",
    "reemplaz",
    "sustitu",
    "anterior",
    "antigu",
    "legacy",
    "descontinuad",
    "apagad",
    "cierre",
    "migrar",
)


class TestTier1Feature1BugsCatalog(unittest.TestCase):
    """Feature 1: Verified Launch-Day GTA VI Bugs Catalog."""

    def test_bugs_json_exists_and_valid_schema(self) -> None:
        bugs_path = DOCS_DIR / "BUGS_VERIFICADOS.json"
        self.assertTrue(bugs_path.is_file(), f"Missing {bugs_path}")

        bugs = load_bugs_json()
        self.assertGreaterEqual(
            len(bugs), 5, "Expected at least 5 verified launch-day bugs"
        )

        seen_ids: set[str] = set()
        for idx, bug in enumerate(bugs):
            self.assertIsInstance(bug, dict, f"Bug #{idx} must be a JSON object")
            missing = REQUIRED_BUG_FIELDS - set(bug.keys())
            self.assertFalse(
                missing, f"Bug #{idx} missing required fields: {missing}"
            )

            bug_id = bug["id"]
            self.assertIsInstance(bug_id, str)
            self.assertTrue(bug_id.strip(), f"Bug #{idx} has empty id")
            self.assertNotIn(bug_id, seen_ids, f"Duplicate bug id: {bug_id}")
            seen_ids.add(bug_id)

            for str_field in (
                "title_es",
                "description_es",
                "creator_or_source",
                "safe_usage_strategy_es",
            ):
                self.assertIsInstance(
                    bug[str_field], str, f"{bug_id}.{str_field} must be string"
                )
                self.assertGreater(
                    len(bug[str_field].strip()),
                    5,
                    f"{bug_id}.{str_field} is too short/empty",
                )

            self.assertIn(
                bug["license_type"],
                VALID_LICENSE_TYPES,
                f"{bug_id} invalid license_type: {bug['license_type']}",
            )
            self.assertIn(
                bug["rockstar_policy_risk"],
                VALID_ROCKSTAR_POLICY_RISKS,
                f"{bug_id} invalid rockstar_policy_risk: {bug['rockstar_policy_risk']}",
            )
            self.assertIsInstance(
                bug["raw_reupload_allowed"],
                bool,
                f"{bug_id}.raw_reupload_allowed must be boolean",
            )

            url = bug["url"]
            self.assertIsInstance(url, str)
            self.assertTrue(
                url.startswith("https://"),
                f"{bug_id}.url must start with https://, got {url!r}",
            )
            lowered_url = url.lower()
            for bad in PLACEHOLDER_URL_PATTERNS:
                self.assertNotIn(
                    bad,
                    lowered_url,
                    f"{bug_id}.url contains placeholder pattern {bad!r}: {url}",
                )


class TestTier1Feature2CopyrightGuide(unittest.TestCase):
    """Feature 2: Copyright, Reused Content & Rockstar Policy Guide."""

    def test_guia_completa_exists_spanish_and_substantive(self) -> None:
        guia_path = DOCS_DIR / "GUIA_COMPLETA_GTA6.md"
        self.assertTrue(guia_path.is_file(), f"Missing {guia_path}")

        content = guia_path.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            len(content.strip()),
            1500,
            "GUIA_COMPLETA_GTA6.md is too short to be a complete guide",
        )
        self.assertTrue(
            is_spanish_text(content),
            "GUIA_COMPLETA_GTA6.md must be written in Spanish",
        )

        lowered = content.lower()
        for topic_kw in ("fair use", "rockstar", "shorts", "copyright"):
            self.assertIn(
                topic_kw,
                lowered,
                f"GUIA_COMPLETA_GTA6.md must cover '{topic_kw}'",
            )


class TestTier1Feature3GeminiModels(unittest.TestCase):
    """Feature 3: Exact Gemini 2026 Model Stack Guide & config.py."""

    def test_modelos_gemini_doc_exists_spanish_and_accurate(self) -> None:
        doc_path = DOCS_DIR / "MODELOS_GEMINI_2026.md"
        self.assertTrue(doc_path.is_file(), f"Missing {doc_path}")

        content = doc_path.read_text(encoding="utf-8")
        self.assertGreaterEqual(len(content.strip()), 500)
        self.assertTrue(
            is_spanish_text(content),
            "MODELOS_GEMINI_2026.md must be written in Spanish",
        )

        for model_id in REQUIRED_GEMINI_MODELS:
            self.assertIn(
                model_id,
                content,
                f"MODELOS_GEMINI_2026.md missing required model {model_id}",
            )

        # If deprecated models are mentioned, they must appear on a line or under a section/table header
        # that explicitly marks them as deprecated/obsolete/avoid (not recommended).
        lines = content.splitlines()
        current_heading = ""
        current_table_header = ""
        for idx, line in enumerate(lines):
            stripped = line.strip()
            lowered_line = stripped.lower()
            if stripped.startswith("#"):
                current_heading = lowered_line
                current_table_header = ""
            elif stripped.startswith("|") and idx + 1 < len(lines) and "---" in lines[idx + 1]:
                current_table_header = lowered_line
            elif not stripped.startswith("|"):
                current_table_header = ""

            for dep in DEPRECATED_GEMINI_MODELS:
                if dep in lowered_line:
                    context_blob = f"{current_heading}\n{current_table_header}\n{lowered_line}"
                    has_dep_marker = any(
                        m in context_blob for m in DEPRECATION_CONTEXT_MARKERS
                    )
                    self.assertTrue(
                        has_dep_marker,
                        f"Deprecated model '{dep}' mentioned on line {idx + 1} "
                        f"without explicit deprecated/avoid context (heading={current_heading!r}): {line!r}",
                    )

    def test_pipeline_config_uses_verified_models_only(self) -> None:
        config_path = PIPELINE_DIR / "config.py"
        self.assertTrue(config_path.is_file(), f"Missing {config_path}")

        content = config_path.read_text(encoding="utf-8")
        for model_id in REQUIRED_GEMINI_MODELS:
            self.assertIn(
                model_id,
                content,
                f"gta6_pipeline/config.py missing required model {model_id}",
            )

        # Strip comments to ensure deprecated models aren't configured as active values
        non_comment_lines = [
            line.split("#", 1)[0] for line in content.splitlines()
        ]
        active_code = "\n".join(non_comment_lines).lower()
        for dep in DEPRECATED_GEMINI_MODELS:
            self.assertNotIn(
                dep,
                active_code,
                f"gta6_pipeline/config.py must not configure deprecated model {dep}",
            )


class TestTier1Feature4ScriptsAndMetadata(unittest.TestCase):
    """Feature 4: Spanish Voiceover Scripts & Metadata."""

    def test_all_scripts_exist_non_empty_and_spanish(self) -> None:
        self.assertTrue(GUIONES_DIR.is_dir(), f"Missing {GUIONES_DIR}")
        for stem in EXPECTED_SCRIPT_STEMS:
            script_path = GUIONES_DIR / f"{stem}.txt"
            self.assertTrue(script_path.is_file(), f"Missing script {script_path}")
            text = script_path.read_text(encoding="utf-8").strip()
            self.assertGreater(
                len(text), 80, f"Script {script_path} is unexpectedly short"
            )
            self.assertTrue(
                is_spanish_text(text),
                f"Script {script_path} does not appear to be in Spanish",
            )

    def test_metadata_youtube_json_valid(self) -> None:
        meta_path = GUIONES_DIR / "metadata_youtube.json"
        self.assertTrue(meta_path.is_file(), f"Missing {meta_path}")
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertTrue(
            isinstance(data, (dict, list)) and len(data) > 0,
            "metadata_youtube.json must be a non-empty JSON object or array",
        )


class TestTier1Feature5GeneratedAudio(unittest.TestCase):
    """Feature 5: Generated Playable Spanish Audio Files."""

    def test_all_audio_files_exist_and_pass_ffprobe(self) -> None:
        self.assertTrue(AUDIO_DIR.is_dir(), f"Missing {AUDIO_DIR}")
        for stem in EXPECTED_SCRIPT_STEMS:
            mp3_path = AUDIO_DIR / f"{stem}.mp3"
            self.assertTrue(mp3_path.is_file(), f"Missing audio file {mp3_path}")
            self.assertGreater(
                mp3_path.stat().st_size,
                1024,
                f"Audio file {mp3_path} is too small ({mp3_path.stat().st_size} bytes)",
            )
            probe = ffprobe_inspect(mp3_path)
            audio_streams = get_streams(probe, "audio")
            self.assertGreaterEqual(
                len(audio_streams),
                1,
                f"Audio file {mp3_path} has no valid audio stream in ffprobe",
            )


class TestTier1Feature6PipelineCLIs(unittest.TestCase):
    """Feature 6: Automated Gemini + FFmpeg Video/Audio Pipeline CLIs."""

    def test_cli_help_commands_exit_zero(self) -> None:
        for module in (
            "gta6_pipeline.tts_offline",
            "gta6_pipeline.gemini_workflow",
            "gta6_pipeline.assemble_video",
        ):
            with self.subTest(module=module):
                proc = run_cli(module, ["--help"], timeout=30)
                self.assertEqual(
                    proc.returncode,
                    0,
                    f"{module} --help exited {proc.returncode}.\n"
                    f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
                )
                combined = (proc.stdout + "\n" + proc.stderr).lower()
                self.assertTrue(
                    "usage" in combined or "uso" in combined or "--" in combined,
                    f"{module} --help did not print usage information",
                )


if __name__ == "__main__":
    unittest.main()
