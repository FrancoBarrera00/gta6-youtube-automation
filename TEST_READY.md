# E2E Test Suite Ready (`TEST_READY.md`)

The opaque-box E2E test suite in `/home/antigravity/tests/e2e/` (**22 tests, 6 subtests**) is complete, hardened, and verified passing under both `pytest` and `unittest`.

## Verified Test Runs
- **`/home/antigravity/.venv/bin/pytest tests/e2e/ -v`**: `22 passed, 6 subtests passed in 55.68s` (exit code `0`)
- **`python3 -m unittest discover -s tests/e2e -v`**: `Ran 22 tests in 53.546s — OK` (exit code `0`)

## Test Runner Commands
```bash
# Virtualenv pytest runner (uses tests/e2e/conftest.py for sys.path)
/home/antigravity/.venv/bin/pytest tests/e2e/ -v

# Standard-library unittest runner
python3 -m unittest discover -s tests/e2e -v
```

## Coverage Summary (Features 1–6 × Tiers 1–4)

| Tier | Test File | Scope Covered |
|---|---|---|
| **Tier 1 (Feature Coverage — 8 tests)** | [`test_tier1_features.py`](file:///home/antigravity/tests/e2e/test_tier1_features.py) | Spanish docs (word-boundary regex + diacritics), `BUGS_VERIFICADOS.json` schema & real `https://` URLs, all 6 Gemini 2026 stack models (`gemini-4-hydrogen`, `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-nano-banana-2.1`, `gemini-omni-1.2-flash`, `lyria-3.5`) & section/line-verified deprecation markers for `veo-3.1`/`imagen-3.0`, 6 scripts + `metadata_youtube.json`, 6 `ffprobe`-verified `.mp3` files, 3 CLI `--help` checks |
| **Tier 2 (Boundary & Corner Cases — 6 tests)** | [`test_tier2_boundaries.py`](file:///home/antigravity/tests/e2e/test_tier2_boundaries.py) | Missing/invalid CLI args (non-zero, no traceback), `GEMINI_API_KEY` unset graceful handling, `raw_reupload_allowed === false` for third-party clips, realistic audio durations (`>10s` Shorts, `>45s` long video), explicit warning against raw POV without facecam |
| **Tier 3 (Cross-Feature Integration — 6 tests)** | [`test_tier3_integration.py`](file:///home/antigravity/tests/e2e/test_tier3_integration.py) | 1:1 alignment across `guiones/`, `audio/`, `metadata_youtube.json`, and `BUGS_VERIFICADOS.json`; `high_avoid_tutorial` exploit-tutorial warning check in both catalog & guide; `assemble_video` 9:16 Short (`1080x1920`, `--credit`, `--srt`), 16:9 landscape (`1920x1080` without `--short`), and `ffmpeg -af volumedetect` (`max_volume < -40.0 dB`) proving loud 440Hz game audio is genuinely muted |
| **Tier 4 (Real-World E2E Workflows — 2 tests)** | [`test_tier4_workflows.py`](file:///home/antigravity/tests/e2e/test_tier4_workflows.py) | Full `script -> tts_offline -> assemble_video --short --credit -> ffprobe` pipeline (exact 1 video + 1 audio stream); YouTube upload readiness (`<=100` char titles, `#Shorts`, Fair Use attribution, Spanish metadata) |
