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

**Kyle sub-tabs:** The English with Kyle tab contains four nested sub-tabs: `st.tabs(["Classes", "🧠 Mind Map", "🦜 Warm-Up Linguo", "📘 Agility Accelerator"])`. The Classes sub-tab renders the class selector and content. The Mind Map sub-tab shows a full-width `st.link_button` that opens `/app/static/mindmap_kyle.html` in a new browser tab. The Warm-Up Linguo sub-tab runs a Duolingo-style quiz (see below). The Agility Accelerator sub-tab renders the standalone `kyle_agility_accelerator` entry (see below).

**Warm-Up Linguo:** `_collect_warmup_questions(kyle_classes)` scans all Kyle classes and collects every question from tests whose title contains `"warm"` (case-insensitive). `_render_warmup_linguo(all_qs)` drives the quiz — screens controlled by `linguo_started` / `linguo_idx` / `linguo_batch` in `st.session_state`. Inner helper `_start_round(batch)` sets up a new round: `batch="all"` shuffles the full pool; `batch=10` draws `random.sample(all_qs, 10)`.
- **Start screen** — question count, horizontal radio ("All questions (N)" / "10 random questions"), Start button. Stores chosen batch in `linguo_batch` and calls `_start_round` on click.
- **Question screen** — progress bar, `linguo_idx`/total counter, live score, question text, option buttons. Clicking an option sets `linguo_selected` and `linguo_answered`; increments `linguo_score` if correct; reruns.
- **After answer** — options replaced by colour-coded HTML divs (`_linguo_option_html`): green = correct, red = wrong selection, grey = unchosen. Feedback message + class source caption + "Continue →" button that increments `linguo_idx` and clears `linguo_answered`/`linguo_selected`.
- **Finish screen** — score, percentage, motivational message, "Play Again" (calls `_start_round(linguo_batch)` — redraws a fresh set of the same size without returning to the start screen) / "Quit" (resets `linguo_started`).

New warm-up questions are picked up automatically — no code change needed, only adding the test to `class_cache.json`.

**Agility Accelerator:** A standalone practice resource (not a dated class) stored as a single special entry in `class_cache.json` with `id: "kyle_agility_accelerator"`. It's excluded from the date-based class selector and the Warm-Up Linguo question pool (both of which only scan classes with `id` starting `kyle_2` — dated Kyle classes). Rendered by `_render_agility_accelerator(cls, header)` and `_render_agility_item(item)`, which use a different section schema than regular classes:
- `sections[].intro` — optional markdown shown at the top of the section's expander.
- `sections[].audio` — optional path (e.g. `"assets/classes/english_with_kyle/Agility_accelarator/3. Common Collocations.mp3"`) to a single pre-generated mp3 covering every sentence in that section; rendered via `st.audio()` under a `"🔊 Click play to hear this section read aloud"` label. Not gitignored — must be committed like images.
- `sections[].groups[]` — each has an optional `name` (rendered as `**bold**` subheading) and a list of `items`.
- `items[].text` — markdown shown to the user (e.g. `"**Be** — I was happy, but I wasn't satisfied."`).
- `items[].secondary` — optional Spanish translation, shown as a smaller grey line above `text`.
- `items[].speak` — plain-text version of the sentence (no markdown/bold). Only used offline when generating the section's audio file — **not** used at runtime; there is no per-sentence TTS or listen button in the app (removed 2026-08).
- `_render_agility_item` renders `secondary` + `text` + a slim custom `<hr>` as a **single** `st.markdown(..., unsafe_allow_html=True)` call (not three separate elements) to keep line spacing tight.

**Generating Agility Accelerator section audio:** There is no live TTS in the app for this feature — each section's `audio` mp3 is pre-generated offline and committed. gTTS (used elsewhere in the app) sounds robotic and low-quality (64kbps/24kHz) for this use case, so use **edge-tts** (Microsoft's free neural TTS, no API key) with the `en-CA-LiamNeural` voice (Canadian male, matches Kyle's own accent) instead. Neither `edge-tts` nor `lameenc` are in `requirements.txt` — they're only needed for this offline generation step, not at runtime, so `pip install edge-tts lameenc` ad hoc (requires `dangerouslyDisableSandbox: true` on Bash for the network calls). Write a one-off script (in the scratchpad dir) that, per section: synthesizes each `items[].speak` sentence individually via `edge_tts.Communicate(text, "en-CA-LiamNeural", rate="-5%").stream()`, measures its duration with `mutagen`, generates a matching silence gap with `lameenc` (duration = speech duration + 0.5s buffer, minimum 1.5s, so the learner has time to repeat the sentence before the next one starts), and concatenates all the raw mp3 clip + silence bytes together into one file per section. Save under `assets/classes/english_with_kyle/Agility_accelarator/` (note: folder name is spelled without the second "e" — `Agility_accelarator`, not `Agility_accelerator`) using the section's exact title as the filename (sanitizing `\/:*?"<>|` if present), then set that section's `audio` field to the relative path.

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

**Adding a new class:** transcribe the MP4 with faster-whisper using `WhisperModel('medium', device='cpu', compute_type='int8')` and `model.transcribe(mp4, language='en', beam_size=5)`. Write a one-off Python script to build the entry dict and `json.load` → `cache.append` → `json.dump` — put it in the Claude Code scratchpad directory (not the project root) so no cleanup is needed. Do not commit MP4 files (`assets/classes/**/*.mp4` is gitignored).

**Transcribing from a Vimeo link:** if no local MP4 exists, download audio only with `yt-dlp -f bestaudio -o scratchpad/filename.%(ext)s <url>` — this produces a single `.m4a` file. (Avoid downloading video: Vimeo streams may not merge without ffmpeg, and audio alone is sufficient for transcription.) Delete the `.m4a` after transcription.

**Tests:** Kyle class entries must include a dedicated **"Test 1 · Warm-Up Translations"** test (covering the vocabulary and grammar from that class's warm-up sentences) as the **first** entry in `tests`, plus tests for each major topic covered in the class. Non-Kyle teachers (julia, juls, natural, brain_buffet) do **not** have a warm-up section — omit that test entirely for them. Do not label any section "Warm-Up" for non-Kyle classes; use "Discussion" or another descriptive title instead.

**After adding a Kyle class:** update `mindmap_kyle.html` (and `mindmap_kyle_network.html` if maintained) with the new content, increment the class count in the header, and sync: `cp mindmap_kyle.html static/mindmap_kyle.html`. Always commit both files together.

**After adding a non-Kyle class** (julia, juls, natural, brain_buffet): no mindmap update needed — just commit `class_cache.json`.

**Mindmap "Go to class" links:** Every `###` and `####` node that carries a `*(date)*` tag must include a `- [→ Go to class](/?class=kyle_YYYYMMDD)` bullet as its **first** child line. Multi-date nodes (e.g. `*(May 21 & 26)*`) get one link per class. The `## Prepositions of Place` branch has no sub-nodes, so its link sits directly as the first bullet under the `##` heading. Always add this link when creating a new node.

**Mindmap branch categorisation:** Place each new `###` node under the correct `##` branch:

| Content type | `##` branch |
|---|---|
| Pronunciation rules, silent letters, phonetics, sound distinctions, J sound | `## Pronunciation Tips` |
| Linking words, connected speech, natural reductions (gonna/wanna, are ya / are you) | `## Pronunciation Tips` |
| Phrasal verbs (including *take over for*, *grow out of*, *get by*, etc.) | `## Phrasal Verbs` |
| Grammar rules, tenses, structures, connectors, verb patterns | `## Grammar Rules` |
| Prepositions of place | `## Prepositions of Place` |
| Time prepositions (in/on/at), time expressions | `## Time Expressions` |
| Interrogative structures, question formation | `## Interrogative Challenge` |
| Describing people, personality adjectives | `## Describing People` |
| Formal/business English, formal vocabulary | `## Formal English & Business` |
| Vocabulary groups, confusable words, idioms, themed word sets | `## Vocabulary Themes` |
| Numbers, numerical expressions, dictation exercises | `## Vocabulary Themes` |
| Warm-up translation exercises | `## Warm-Up Translations` |

If a topic doesn't fit any existing branch, flag it to the user rather than guessing.

**Structural patterns vs. single words:** Fixed *sentence structures* introduced via a single expression — e.g. "to be worth it" (vale la pena), negative transportation (*creo que no* → *I don't think*) — belong in `## Grammar Rules`, not `## Vocabulary Themes`, even though a single phrase triggers them. Reserve `## Vocabulary Themes` for word-level distinctions (confusable word pairs, idioms, themed word sets), not sentence-construction rules.

**Images in class sections:** If a section references an `"image"` field (e.g. `"assets/classes/english_with_kyle/prepositions.png"`), the image file must be committed to git — MP4 files are gitignored but images are not.

**Image placement:** The `image` field always renders *above* the entire `content` block. If the image needs to appear between two content blocks (e.g. grammar rules above the image, practice table below it), split into two sections: one with the first content block and no image, and a second with the `image` field and the remaining content.

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

The pre-generated Agility Accelerator section audio files (`assets/classes/english_with_kyle/Agility_accelarator/*.mp3`) are **not** gitignored and must be committed — unlike class MP4s, these mp3s are the actual served content, not source footage.
