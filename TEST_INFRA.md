# E2E Testing Infrastructure (`TEST_INFRA.md`)

## 1. Architecture Overview
The E2E test suite in `/home/antigravity/tests/e2e/` is a **strictly opaque-box** verification suite of **22 tests** (with 6 subtests) built on Python's standard-library `unittest` (`unittest.TestCase`). [`conftest.py`](file:///home/antigravity/tests/e2e/conftest.py) ensures `/home/antigravity` is on `sys.path` so the suite executes cleanly under both:
- Standard library: `python3 -m unittest discover -s tests/e2e -v`
- Virtualenv pytest: `/home/antigravity/.venv/bin/pytest tests/e2e/ -v`

All CLI invocations use [`get_python_executable()`](file:///home/antigravity/tests/e2e/helpers.py), which prefers `/home/antigravity/.venv/bin/python` when present and falls back to `sys.executable`.

## 2. Environment Dependencies & Fixtures
- **`ffmpeg` & `ffprobe` (5.1.9 on PATH)**:
  - [`generate_synthetic_16_9_video()`](file:///home/antigravity/tests/e2e/helpers.py) creates a genuine 1920x1080 30fps H.264 `.mp4` with a loud 0 dB 440Hz AAC audio track inside a `tempfile.TemporaryDirectory()` so `assemble_video` can be tested end-to-end without external footage.
  - [`generate_silent_wav()`](file:///home/antigravity/tests/e2e/helpers.py) creates a silent 24kHz mono PCM `.wav` (`anullsrc`) and [`ffmpeg_detect_max_volume_db()`](file:///home/antigravity/tests/e2e/helpers.py) runs `ffmpeg -af volumedetect` to verify original game audio is genuinely muted (`max_volume < -40.0 dB`).
  - [`ffprobe_inspect()`](file:///home/antigravity/tests/e2e/helpers.py) validates exact stream counts (`1` video, `1` audio), resolutions (`1080x1920` for 9:16 Shorts; `1920x1080` for 16:9 landscape), and media duration.
  - [`write_sample_srt()`](file:///home/antigravity/tests/e2e/helpers.py) generates a temporary Spanish `.srt` subtitle file for `--srt` integration testing.
- **`GEMINI_API_KEY` isolation**:
  - Tier 2 explicitly copies `os.environ` and removes `GEMINI_API_KEY` and `GOOGLE_API_KEY` before invoking `gta6_pipeline.gemini_workflow` to verify graceful non-zero exit without unhandled Python tracebacks.

## 3. Feature-to-Test Mapping (Features 1–6 × Tiers 1–4)

| Feature (`PROJECT.md`) | Tier 1 (Features) | Tier 2 (Boundaries) | Tier 3 (Integration) | Tier 4 (Workflows) |
|---|---|---|---|---|
| **1. Verified Launch-Day GTA VI Bugs Catalog** | [`TestTier1Feature1BugsCatalog.test_bugs_json_exists_and_valid_schema`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | [`TestTier2PolicyAndMediaBoundaries.test_third_party_bugs_disallow_raw_reupload`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py) | [`TestTier3CrossAssetConsistency.test_bugs_catalog_aligns_with_scripts_and_metadata`](file:///home/antigravity/tests/e2e/test_tier3_integration.py), [`test_high_risk_bugs_warn_against_step_by_step_tutorials`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | — |
| **2. Copyright, Reused Content & Rockstar Policy Guide** | [`TestTier1Feature2CopyrightGuide.test_guia_completa_exists_spanish_and_substantive`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | [`TestTier2PolicyAndMediaBoundaries.test_guide_warns_against_raw_pov_reupload_without_facecam`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py) | [`TestTier3CrossAssetConsistency.test_high_risk_bugs_warn_against_step_by_step_tutorials`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | [`TestTier4EndToEndWorkflows.test_youtube_upload_readiness_metadata_and_fair_use`](file:///home/antigravity/tests/e2e/test_tier4_workflows.py) |
| **3. Exact Gemini 2026 Model Stack Guide** | [`TestTier1Feature3GeminiModels.test_modelos_gemini_doc_exists_spanish_and_accurate`](file:///home/antigravity/tests/e2e/test_tier1_features.py), [`test_pipeline_config_uses_verified_models_only`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | — | — | — |
| **4. Spanish Voiceover Scripts & Metadata** | [`TestTier1Feature4ScriptsAndMetadata.test_all_scripts_exist_non_empty_and_spanish`](file:///home/antigravity/tests/e2e/test_tier1_features.py), [`test_metadata_youtube_json_valid`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | — | [`TestTier3CrossAssetConsistency.test_every_script_has_matching_audio_and_metadata`](file:///home/antigravity/tests/e2e/test_tier3_integration.py), [`test_bugs_catalog_aligns_with_scripts_and_metadata`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | [`TestTier4EndToEndWorkflows.test_youtube_upload_readiness_metadata_and_fair_use`](file:///home/antigravity/tests/e2e/test_tier4_workflows.py) |
| **5. Generated Playable Spanish Audio Files** | [`TestTier1Feature5GeneratedAudio.test_all_audio_files_exist_and_pass_ffprobe`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | [`TestTier2PolicyAndMediaBoundaries.test_audio_durations_are_realistic`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py) | [`TestTier3CrossAssetConsistency.test_every_script_has_matching_audio_and_metadata`](file:///home/antigravity/tests/e2e/test_tier3_integration.py), [`TestTier3AssembleVideoIntegration`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | — |
| **6. Automated Gemini + FFmpeg Video/Audio Pipeline** | [`TestTier1Feature6PipelineCLIs.test_cli_help_commands_exit_zero`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | [`TestTier2CLIBoundaries.test_missing_args_return_nonzero_without_traceback`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py), [`test_invalid_input_paths_return_nonzero_without_traceback`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py), [`test_gemini_workflow_without_api_key_fails_gracefully`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py) | [`test_assemble_short_9_16_with_credit_and_srt`](file:///home/antigravity/tests/e2e/test_tier3_integration.py), [`test_assemble_long_16_9_without_short_flag`](file:///home/antigravity/tests/e2e/test_tier3_integration.py), [`test_assemble_video_mutes_original_game_audio`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | [`TestTier4EndToEndWorkflows.test_full_script_to_tts_to_short_video_workflow`](file:///home/antigravity/tests/e2e/test_tier4_workflows.py) |

## 4. Test Runner Commands
```bash
# Run with Python stdlib unittest (22 tests)
python3 -m unittest discover -s tests/e2e -v

# Run with pytest in .venv (22 passed, 6 subtests passed)
/home/antigravity/.venv/bin/pytest tests/e2e/ -v
```
