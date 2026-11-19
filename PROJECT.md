# Project: GTA VI Automated YouTube & Shorts Production Kit (Spanish)

## Architecture
A complete, copyright-safe, Spanish-language YouTube & Shorts content creation kit and automated production pipeline for *Grand Theft Auto VI* (launched Nov 19, 2026), built around:
1. **Verified Knowledge & Policy Layer (`docs/`)**: Evidence-backed Spanish guides covering real launch-day GTA VI bugs/glitches, YouTube & Rockstar copyright/monetization compliance (why raw POV re-uploads fail and how transformative Fair Use / CC-BY / official media works), and the exact late-2026 Gemini API model stack.
2. **Content & Audio Assets Layer (`guiones/`, `audio/`)**: Ready-to-use Spanish voiceover scripts (Shorts + long-form compilation) with inline vocal/pacing cues, paired with real generated playable audio files (`.mp3` / `.wav`) and subtitle files (`.srt`).
3. **Automated Production Pipeline (`gta6_pipeline/`)**: Python 3.11 + FFmpeg 5.1.9 CLI toolkit integrating `google-genai >= 2.25.0` (`gemini-4-hydrogen`, `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-nano-banana-2.1`, `gemini-omni-1.2-flash`, `lyria-3.5`) for video bug detection, Spanish TTS generation, thumbnail generation, B-roll, and 9:16 / 16:9 FFmpeg assembly (with copyrighted in-game audio muting & Fair Use attribution overlays).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Verified Launch-Day GTA VI Bugs Catalog | Documented Nov 18–19, 2026 bugs (Bridge Boat Glitch, Lucia Falling Through Ground, Jason/Cop Clipping, Flying Truck/Cars, Bank Softlock, Store-Robbery Glitch) with verified URLs & license status | M1 | Survey 1 |
| 2 | Copyright, Reused Content & Rockstar Policy Guide | Clear Spanish explanation of why POV-without-facecam violates Copyright/Reused Content, CC-BY absence, Fair Use transformative rules, Shorts 1–3 min claim blocking, GenAI disclosure, and Rockstar policy | M1 | Survey 1 & 2 |
| 3 | Exact Gemini 2026 Model Stack Guide | Exact model IDs (`gemini-4-hydrogen`, `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-nano-banana-2.1`, `gemini-omni-1.2-flash`, `lyria-3.5`), pricing, and deprecated models to avoid | M1 | Survey 3 |
| 4 | Spanish Voiceover Scripts & Metadata | Ready-to-record/generate Spanish scripts (5 Shorts + 1 Long-Form Compilation) with hooks, Fair Use commentary, titles, descriptions, and tags | M2 | ORIGINAL_REQUEST |
| 5 | Generated Playable Spanish Audio Files | Real, locally generated Spanish voiceover audio files (`.mp3` / `.wav`) for all scripts, verified with `ffprobe` | M2 | ORIGINAL_REQUEST |
| 6 | Automated Gemini + FFmpeg Video/Audio Pipeline | Python CLI (`gta6_pipeline`) for Gemini bug/timestamp analysis, `gemini-3.8-flash-tts` WAV generation, `gemini-nano-banana-2.1` thumbnails, and FFmpeg Shorts/video muxing (audio mute + attribution overlay + subtitles) | M2 | ORIGINAL_REQUEST & Survey 3 |
| 7 | E2E Test Suite & Adversarial Hardening | Opaque-box E2E verification (Tiers 1–4) + Tier 5 adversarial hardening of all docs, scripts, audio files, and pipeline CLI | M3 (Final) | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Knowledge, Policy & Gemini Stack Docs | `docs/GUIA_COMPLETA_GTA6.md`, `docs/BUGS_VERIFICADOS.json`, `docs/MODELOS_GEMINI_2026.md` | none | DONE |
| M2 | Spanish Scripts, Generated Audio & Pipeline | `guiones/`, `audio/`, `gta6_pipeline/`, `.venv/` | none (uses PROJECT.md contracts) | DONE |
| E2E | E2E Testing Track | `TEST_INFRA.md`, `tests/e2e/`, `TEST_READY.md` | none (requirement-driven) | DONE |
| M3 | Final Milestone: E2E Pass & Tier 5 Hardening | Pass 100% `TEST_READY.md` Tiers 1–4, then Tier 5 adversarial hardening | M1, M2, E2E | DONE |

## Interface Contracts
### `docs/BUGS_VERIFICADOS.json` Schema
Array of bug objects:
- `id` (string, e.g. `"bug_01_boat_bridge"`)
- `title_es` (string)
- `description_es` (string)
- `creator_or_source` (string)
- `url` (string, verified URL)
- `license_type` (enum: `"standard_youtube"`, `"social_media_standard"`, `"official_rockstar"`)
- `raw_reupload_allowed` (boolean, `false` for all third-party clips)
- `safe_usage_strategy_es` (string)
- `rockstar_policy_risk` (enum: `"low"`, `"medium"`, `"high_avoid_tutorial"`)

### `gta6_pipeline` CLI Contract
- Virtualenv: `/home/antigravity/.venv`
- Package / Entrypoints:
  - `python -m gta6_pipeline.tts_offline --script <path.txt> --out <path.mp3>` (generates real Spanish TTS audio offline/free without API key)
  - `python -m gta6_pipeline.gemini_workflow --mode <script|analyze|tts|thumbnail|broll> ...` (full Gemini API integration using `google-genai >= 2.25.0`; validates arguments and fails gracefully with clear message if `GEMINI_API_KEY` is unset)
  - `python -m gta6_pipeline.assemble_video --video <in.mp4> --audio <vo.mp3|wav> --out <out.mp4> [--short] [--credit "Clip: @creator"] [--srt <subs.srt>]` (uses `ffmpeg` to mute original copyrighted game audio, mix voiceover, optional 9:16 crop, attribution text overlay, and subtitles)

## Code Layout
```
/home/antigravity/
├── PROJECT.md
├── TEST_INFRA.md                 # E2E Testing Track
├── TEST_READY.md                 # E2E Testing Track completion signal
├── docs/                         # M1 exclusive ownership
│   ├── GUIA_COMPLETA_GTA6.md     # Main Spanish guide for the user
│   ├── BUGS_VERIFICADOS.json     # Structured catalog of verified bugs & URLs
│   └── MODELOS_GEMINI_2026.md    # Exact Gemini 2026 model recommendations & code
├── guiones/                      # M2 exclusive ownership
│   ├── short_01_barco_puente.txt
│   ├── short_02_lucia_bajo_mapa.txt
│   ├── short_03_jason_policia_clipping.txt
│   ├── short_04_camion_volador.txt
│   ├── short_05_softlock_banco.txt
│   ├── video_largo_compilacion_bugs.txt
│   └── metadata_youtube.json     # Titles, descriptions, tags, Fair Use attributions
├── audio/                        # M2 exclusive ownership
│   ├── short_01_barco_puente.mp3
│   ├── short_02_lucia_bajo_mapa.mp3
│   ├── short_03_jason_policia_clipping.mp3
│   ├── short_04_camion_volador.mp3
│   ├── short_05_softlock_banco.mp3
│   └── video_largo_compilacion_bugs.mp3
├── gta6_pipeline/                # M2 exclusive ownership
│   ├── __init__.py
│   ├── config.py                 # Verified late-2026 Gemini model IDs
│   ├── tts_offline.py            # Free/local Spanish TTS generator
│   ├── gemini_workflow.py        # google-genai >= 2.25.0 full workflow
│   ├── assemble_video.py         # FFmpeg 9:16/16:9 assembler + audio mute + attribution
│   └── requirements.txt
└── tests/                        # E2E Testing Track exclusive ownership
    └── e2e/
        └── ...
```
