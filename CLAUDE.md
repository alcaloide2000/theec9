# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Run on a specific port
streamlit run app.py --server.port=8501
```

## Architecture

Single-file Streamlit app (`app.py`) backed by `the.xlsx` (multi-sheet Excel workbook).

**Data flow:** Excel sheets are loaded once at startup via `@st.cache_data` into module-level DataFrames. Each tab filters its DataFrame and picks random rows on button clicks.

**State:** All inter-widget state lives in `st.session_state`. Each module has its own prefixed keys (e.g. `warm_*`, `rep_*`, `pic_*`). Filter/dropdown changes reset the module's state keys so count and score start fresh.

**Modules and their Excel sheets:**

| Tab | Sheet | Key columns |
|---|---|---|
| Warm-Up | `warm` | `structure`, `esp`, `eng` |
| Reported Speech | `reportedsp` | `story`, `direct`, `reported` |
| Interrogative | `question` | `word`, `answer`, `question` |
| Pictures | `pictures` | `name` (filename in `/assets/`), `eng` |
| Question Tags | `tags` | `sentence`, `tag` |
| Never Done | `never` | `question`, `answer` |

**Audio:** `generate_audio(text)` calls gTTS and returns raw MP3 bytes, played via `st.audio()`. Voice is English with Canadian accent (`lang='en', tld='ca'`).

**Warm-Up scoring:** Correct/incorrect buttons are capped at the selected bunch size (`warm_limit`). The score display color flips red when incorrect ≥ correct.

## Deployment

Deployed on Render. Auto-deploys on push to `master` at `github.com/alcaloide2000/theec9`. The `Procfile` contains the start command — no build step needed.
