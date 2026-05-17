# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run main app
streamlit run app.py

# Run standalone class app
streamlit run class_test.py

# Run on a specific port
streamlit run app.py --server.port=8501
```

## Repository structure

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit app — 7 tabs, auth gate, Excel-backed practice modules |
| `class_test.py` | Standalone Streamlit app — Class tab only, no auth, reads from `class_cache.json` |
| `class_cache.json` | All class content: sections (markdown) + multiple-choice tests, one entry per class |
| `the.xlsx` | Multi-sheet Excel workbook — source data for all practice modules |
| `Procfile` | Render start command for `app.py` |
| `requirements.txt` | `streamlit`, `pandas`, `gTTS`, `openpyxl` |

## app.py architecture

Single-file Streamlit app backed by `the.xlsx`.

**Data flow:** Excel sheets loaded once at startup via `@st.cache_data`. Each tab filters its DataFrame and picks random rows on button clicks.

**State:** All inter-widget state lives in `st.session_state`. Each module uses prefixed keys (e.g. `warm_*`, `rep_*`, `pic_*`). Filter/dropdown changes reset that module's keys so count and score start fresh.

**Modules and their Excel sheets:**

| Tab | Sheet | Key columns |
|---|---|---|
| Warm-Up | `warm` | `structure`, `esp`, `eng` |
| Reported Speech | `reportedsp` | `story`, `direct`, `reported` |
| Interrogative | `question` | `word`, `answer`, `question` |
| Pictures | `pictures` | `name` (filename in `/assets/`), `eng` |
| Question Tags | `tags` | `sentence`, `tag` |
| Never Done | `never` | `question`, `answer` |
| Class | — | reads from `class_cache.json` via `_load_class_cache()` |

**Audio:** `generate_audio(text)` calls gTTS and returns raw MP3 bytes, played via `st.audio()`. Canadian accent (`lang='en', tld='ca'`).

**Auth:** Login/register gate backed by `users.json` (gitignored). Progress persisted to `progress.json` and `history.json` (both gitignored).

## class_test.py architecture

Lightweight standalone app — no auth, no Excel, no other tabs. Reads entirely from `class_cache.json`.

**Class selector:** Buttons sorted newest → oldest by `date` field. Most recent has a 🆕 badge and is selected by default. Selected button renders as `type="primary"`, others as `type="secondary"`.

**Test state:** Each test uses session state keys `{key}_sub` (submitted flag), `{key}_q{i}` (radio answer per question), `{key}_reset_pending` (cleared before widget renders to avoid widget-key conflict). Reset handler runs at the top of the script before any widgets render.

## class_cache.json structure

```json
[
  {
    "id": "kyle_20260428",
    "title": "English with Kyle",
    "date": "2026-04-28",
    "topic": "...",
    "sections": [
      { "title": "1. ...", "expanded": false, "content": "...markdown..." }
    ],
    "tests": [
      {
        "title": "Test 1 · ...",
        "key": "unique_key",
        "qs": [
          { "q": "question text", "opts": ["A", "B", "C"], "ans": "A" }
        ]
      }
    ]
  }
]
```

**Adding a new class:** transcribe the MP4 with faster-whisper, write a one-off Python script to build the entry dict and `json.load` → `cache.append` → `json.dump`, then delete the script. Do not commit MP4 files (`assets/classes/*.mp4` is gitignored).

## Deployment

Two separate Render web services, both auto-deploy on push to `master` at `github.com/alcaloide2000/theec9`.

| Service | Start command |
|---|---|
| Main app | `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |
| Class test | `streamlit run class_test.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |

## Gitignored files

`users.json`, `progress.json`, `history.json`, `classes.json`, `.streamlit/secrets.toml`, `assets/classes/*.mp4`

`class_cache.json` is **not** gitignored — commit it so Render can serve class content without the MP4 files.
