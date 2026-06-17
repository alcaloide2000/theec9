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
| `assets/profilepictures/` | Circular avatar images shown in tab labels (`kyle.jpg`, `julia.jpg`, `juls.jpg`, `brain_buffet.png`) |
| `mindmap_kyle.html` | Interactive markmap mind map of all Kyle class content — searchable, expandable |
| `mindmap_kyle_network.html` | Alternative vis-network graph view of Kyle class content |
| `static/mindmap_kyle.html` | Copy of `mindmap_kyle.html` served at `/app/static/mindmap_kyle.html` via Streamlit static serving |
| `.streamlit/config.toml` | Enables `enableStaticServing = true` so files in `static/` are publicly accessible |

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

**Page title:** "Reviewing The English Collective" — set in both `st.set_page_config` and `st.title()`.

**Five outer tabs:** `st.tabs(["English with Kyle", "Essential English · Julia", "English Time with Juls", "Natural English", "Brain Buffet"])`. Classes are split by the `teacher` field (`"kyle"` / `"julia"` / `"juls"` / `"natural"` / `"brain_buffet"`). Each tab has its own session state key (`sel_kyle` / `sel_julia` / `sel_juls` / `sel_natural` / `sel_brain_buffet`) for the selected class index.

**Kyle sub-tabs:** The English with Kyle tab contains two nested sub-tabs: `st.tabs(["Classes", "🧠 Mind Map"])`. The Classes sub-tab renders the class selector and content. The Mind Map sub-tab shows a full-width `st.link_button` that opens `/app/static/mindmap_kyle.html` in a new browser tab.

**Tab avatars:** `_inject_tab_avatars(pic_paths)` injects a `<style>` block that uses CSS `::after` pseudo-elements on each `button[data-baseweb="tab"]:nth-child(n)` to render a 26×26 px circular profile photo (base64-embedded) to the right of the tab label text. Avatar images live in `assets/profilepictures/`. The function detects MIME type from the file extension (`.png` → `image/png`, anything else → `image/jpeg`). Pass `None` in the list for a tab that has no profile picture yet — the function skips it silently. An additional CSS rule using `[role="tabpanel"] button[data-baseweb="tab"]::after { content: none }` cancels the avatar bleed onto nested sub-tabs.

**Class selector:** Within each tab, buttons sorted newest → oldest by `date` field. Most recent has a 🆕 badge and is selected by default. Selected button renders as `type="primary"`, others as `type="secondary"`.

**Rendering:** `_render_teacher_tab(classes, sel_key)` handles the selector and delegates to `_render_class(cls)` for sections and tests.

**Test state:** Each test uses session state keys `{key}_sub` (submitted flag), `{key}_q{i}` (radio answer per question), `{key}_reset_pending` (cleared before widget renders to avoid widget-key conflict). Reset handler runs at the top of the script before any widgets render.

## class_cache.json structure

```json
[
  {
    "id": "kyle_20260428",
    "title": "English with Kyle",
    "date": "2026-04-28",
    "topic": "...",
    "teacher": "kyle",
    "sections": [
      {
        "title": "1. ...",
        "expanded": false,
        "content": "...markdown...",
        "image": "assets/foo.jpg",
        "image_hotspots": [
          { "x": 0, "y": 10, "w": 50, "h": 8, "label": "Tooltip text on hover" }
        ]
      }
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

**Section fields:** `image` and `image_hotspots` are optional. If `image` is present without `image_hotspots`, the image is rendered with `st.image()`. If both are present, `_render_hotspot_image()` renders it as an inline HTML component with interactive hover regions. Hotspot coordinates (`x`, `y`, `w`, `h`) are percentages of the image dimensions. `content` (markdown) always renders below the image.

**`teacher` field:** `"kyle"` for English with Kyle classes, `"julia"` for Essential English · Julia classes, `"juls"` for English Time with Juls classes, `"natural"` for Natural English classes, `"brain_buffet"` for Brain Buffet classes. Defaults to `"kyle"` if absent (for backwards compatibility).

**MP4 location:** `assets/classes/english_with_kyle/`, `assets/classes/esential_english_julia/`, `assets/classes/english_time_with_juls/`, `assets/classes/natural_english/`, or `assets/classes/brain_buffet/` depending on teacher.

**Adding a new class:** transcribe the MP4 with faster-whisper, write a one-off Python script to build the entry dict and `json.load` → `cache.append` → `json.dump`, then delete the script. Do not commit MP4 files (`assets/classes/**/*.mp4` is gitignored).

**Transcribing from a Vimeo link:** if no local MP4 exists, download with `yt-dlp` (`pip install yt-dlp`). Vimeo streams may not merge without ffmpeg — if yt-dlp produces a `.fdash-audio-*.m4a` alongside the video file, transcribe directly from the `.m4a` (faster-whisper accepts it). Delete both partial files after transcription.

**Tests:** Kyle class entries must include a dedicated **"Test · Warm-Up Translations"** test (covering the vocabulary and grammar from that class's warm-up sentences), plus tests for each major topic covered in the class. Non-Kyle teachers (julia, juls, natural, brain_buffet) do **not** have a warm-up section — omit that test entirely for them.

**After adding a Kyle class:** update `mindmap_kyle.html` (and `mindmap_kyle_network.html` if maintained) with the new content, increment the class count in the header, and sync: `cp mindmap_kyle.html static/mindmap_kyle.html`. Always commit both files together.

**Mindmap "Go to class" links:** Every `###` and `####` node that carries a `*(date)*` tag must include a `- [→ Go to class](/?class=kyle_YYYYMMDD)` bullet as its **first** child line. Multi-date nodes (e.g. `*(May 21 & 26)*`) get one link per class. The `## Prepositions of Place` branch has no sub-nodes, so its link sits directly as the first bullet under the `##` heading. Always add this link when creating a new node.

**Mindmap branch categorisation:** Place each new `###` node under the correct `##` branch:

| Content type | `##` branch |
|---|---|
| Pronunciation rules, silent letters, phonetics, sound distinctions | `## Pronunciation Tips` |
| Phrasal verbs (including *take over for*, *get by*, etc.) | `## Phrasal Verbs` |
| Grammar rules, tenses, structures, connectors, verb patterns | `## Grammar Rules` |
| Prepositions of place | `## Prepositions of Place` |
| Time prepositions (in/on/at), time expressions | `## Time Expressions` |
| Interrogative structures, question formation | `## Interrogative Challenge` |
| Describing people, personality adjectives | `## Describing People` |
| Formal/business English, formal vocabulary | `## Formal English & Business` |
| Vocabulary groups, confusable words, idioms, themed word sets | `## Vocabulary Themes` |
| Warm-up translation exercises | `## Warm-Up Translations` |

If a topic doesn't fit any existing branch, flag it to the user rather than guessing.

**Images in class sections:** If a section references an `"image"` field (e.g. `"assets/classes/english_with_kyle/prepositions.png"`), the image file must be committed to git — MP4 files are gitignored but images are not.

## mindmap_kyle.html architecture

Standalone markmap interactive mind map. Served as a static file at `/app/static/mindmap_kyle.html`. Opened via `st.link_button` in the 🧠 Mind Map sub-tab.

**Instance capture (PART 1):** Intercepts `window.markmap.Markmap.create` before markmap-autoloader calls it. Handles both sync and async return values (markmap-autoloader@0.14 / markmap-lib@0.17 can return a Promise):
```javascript
M.create = function (...args) {
    const result = orig.apply(this, args);
    if (result && typeof result.then === 'function') result.then(onInstance);
    else onInstance(result);
    return result;
};
```

**Sync requirement:** After every edit to `mindmap_kyle.html`, run `cp mindmap_kyle.html static/mindmap_kyle.html` and commit both files.

## Deployment

Two separate Render web services, both auto-deploy on push to `master` at `github.com/alcaloide2000/theec9`.

| Service | Start command |
|---|---|
| Main app | `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |
| Class test | `streamlit run class_test.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true` |

## Gitignored files

`users.json`, `progress.json`, `history.json`, `classes.json`, `.streamlit/secrets.toml`, `assets/classes/**/*.mp4`

`class_cache.json` is **not** gitignored — commit it so Render can serve class content without the MP4 files.

Images inside `assets/classes/` (e.g. `prepositions.png`) are **not** gitignored and must be committed for Render to serve them.
