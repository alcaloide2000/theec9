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

**Kyle sub-tabs:** The English with Kyle tab contains five nested sub-tabs: `st.tabs(["Classes", "🧠 Mind Map", "🦜 Warm-Up Linguo", "📘 Agility Accelerator", "❓ The Interrogative Challenge"])`. The Classes sub-tab renders the class selector and content. The Mind Map sub-tab shows a full-width `st.link_button` that opens `/app/static/mindmap_kyle.html` in a new browser tab. The Warm-Up Linguo sub-tab runs a Duolingo-style quiz (see below). The Agility Accelerator sub-tab renders the standalone `kyle_agility_accelerator` entry (see below). The Interrogative Challenge sub-tab renders statement/question pairs collected from all dated Kyle classes, grouped by class then section, each with click-to-hear synced audio (see below).

**Warm-Up Linguo:** `_collect_warmup_questions(kyle_classes)` scans all Kyle classes and collects every question from tests whose title contains `"warm"` (case-insensitive). `_render_warmup_linguo(all_qs)` drives the quiz — screens controlled by `linguo_started` / `linguo_idx` / `linguo_batch` in `st.session_state`. Inner helper `_start_round(batch)` sets up a new round: `batch="all"` shuffles the full pool; `batch=10` draws `random.sample(all_qs, 10)`.
- **Start screen** — question count, horizontal radio ("All questions (N)" / "10 random questions"), Start button. Stores chosen batch in `linguo_batch` and calls `_start_round` on click.
- **Question screen** — progress bar, `linguo_idx`/total counter, live score, question text, option buttons. Clicking an option sets `linguo_selected` and `linguo_answered`; increments `linguo_score` if correct; reruns.
- **After answer** — options replaced by colour-coded HTML divs (`_linguo_option_html`): green = correct, red = wrong selection, grey = unchosen. Feedback message + class source caption + "Continue →" button that increments `linguo_idx` and clears `linguo_answered`/`linguo_selected`.
- **Finish screen** — score, percentage, motivational message, "Play Again" (calls `_start_round(linguo_batch)` — redraws a fresh set of the same size without returning to the start screen) / "Quit" (resets `linguo_started`).

New warm-up questions are picked up automatically — no code change needed, only adding the test to `class_cache.json`.

**The Interrogative Challenge:** `_collect_interrogative_pairs(kyle_classes)` scans every dated Kyle class's section `content` markdown for two-column tables headed `| Statement | Question |` or `| Answer | Question |` (case-insensitive), extracts every data row as a `{left_label, left, question, from_date, from_topic, from_section}` pair, and separately returns a `section_audio` dict keyed by `(date, topic, section_title)` of any section that carries pre-generated `interrogative_audio` / `interrogative_timings` fields (see below). `_render_interrogative_challenge(pairs, section_audio)` groups the pairs by class (newest first) then by section, same as before. Only sections that actually use the pipe-table format are picked up; free-text bullet/blockquote drills (e.g. `"6. Interrogative Challenge: Which vs. Where & Whose"`, which uses `- *statement* → **question**` prose instead of a table) are intentionally skipped rather than parsed with a fragile regex.
- **With pre-generated audio** (the common case — every section as of this writing has it): the group's pairs are flattened into an alternating Statement/Question (or Answer/Question) item list and rendered through the same `_render_agility_section_synced(sec)` karaoke-sync player used by the Agility Accelerator's "Mastering the Interrogative" sections — click play, current sentence highlights as it plays.
- **Without audio** (fallback for a section whose table was just added to `class_cache.json` and hasn't been regenerated yet): renders as a plain markdown table, same as the original static behavior.

Unlike Warm-Up Linguo, new tables are **not** picked up with synced audio automatically — the table renders as a plain fallback table until its class's section gets `interrogative_audio` / `interrogative_timings` fields via the regeneration step below.

**Generating Interrogative Challenge section audio + timings:** Same offline pipeline as the Agility Accelerator's "Mastering the Interrogative" sections (edge-tts, `en-CA-LiamNeural`, rate `-5%`, PCM decode-concat-reencode via PyAV + `lameenc`; see that section's rationale for why raw mp3-byte splicing is avoided). Per dated class, per section that contains a `| Statement/Answer | Question |` table: flatten every row into two items — `{text: left, secondary: left_label}` then `{text: question, secondary: "Question"}` — in table order (a section with more than one such table in its `content`, e.g. an Answer block followed by a Statement block, gets one merged audio file covering all its tables in document order). Gap rule (identical to the Agility Accelerator's Section 6 exception): **5000ms** after a Statement/Answer item (thinking time before the question plays), **2500ms** after a Question item. No comma-splitting (none of the source pairs contain commas — re-check before reusing this rule if new content does). Save the mp3 under `assets/classes/english_with_kyle/Interrogative_challenge/` named after the section's exact title (same sanitization as Agility Accelerator: `\/:*?"<>|` stripped, `:` → ` -`). Write the resulting `audio` relative path and `timings` list directly onto that section's object in `class_cache.json` as `interrogative_audio` / `interrogative_timings` — sibling fields to the existing `content`, not a replacement for it (the same section's markdown table still renders normally in the Classes sub-tab via `_render_class`, and doubles as the fallback if audio generation is skipped). If a table's content changes, regenerate that section's audio and `timings` together — they're positionally indexed with no id to re-match against.

**Agility Accelerator:** A standalone practice resource (not a dated class) stored as a single special entry in `class_cache.json` with `id: "kyle_agility_accelerator"`. It's excluded from the date-based class selector and the Warm-Up Linguo question pool (both of which only scan classes with `id` starting `kyle_2` — dated Kyle classes). Rendered by `_render_agility_accelerator(cls, header)` and `_render_agility_item(item)`, which use a different section schema than regular classes:
- `sections[].intro` — optional markdown shown at the top of the section's expander.
- `sections[].audio` — path (e.g. `"assets/classes/english_with_kyle/Agility_accelarator/3. Common Collocations.mp3"`) to a single pre-generated mp3 covering every sentence in that section. Not gitignored — must be committed like images.
- `sections[].timings` — list of `[start, end]` second offsets (floats, one pair per item in flattened group→item order) into `sections[].audio`. Every section has this. `_render_agility_accelerator` calls `_render_agility_section_synced(sec)`, which base64-embeds the mp3 into a `components.html` block alongside all the section's sentences, and JS on the `<audio>` element's `timeupdate` event highlights (`.active` class) whichever `.sentence` div's `[start, end)` range contains the current playback time — karaoke-style sync. `items[].text` markdown (only `**bold**` is used anywhere in the data) is converted to `<strong>` with a regex since this path renders raw HTML, not `st.markdown`.
- `sections[].groups[]` — each has an optional `name` (rendered as a bold subheading) and a list of `items`.
- `items[].text` — markdown shown to the user (e.g. `"**Be** — I was happy, but I wasn't satisfied."`); only `**bold**` spans are supported.
- `items[].secondary` — optional Spanish translation/note, shown as a smaller grey line above `text`. May contain raw HTML (e.g. `<b>`/`<i>`) — rendered unescaped.
- `items[].speak` — plain-text version of the sentence (no markdown/bold). Only used offline when generating the section's audio file and its `timings` — **not** used at runtime for TTS; there is no per-sentence TTS or listen button in the app (removed 2026-08).
- `_render_agility_item(item)` (legacy path, kept for any future section added without `timings`) renders `secondary` + `text` + a slim custom `<hr>` as a **single** `st.markdown(..., unsafe_allow_html=True)` call to keep line spacing tight.

**Generating Agility Accelerator section audio + timings:** There is no live TTS in the app for this feature — each section's `audio` mp3 and `timings` array are pre-generated offline and committed together. gTTS (used elsewhere in the app) sounds robotic and low-quality (64kbps/24kHz) for this use case, so use **edge-tts** (Microsoft's free neural TTS, no API key) with the `en-CA-LiamNeural` voice (Canadian male, matches Kyle's own accent) instead. Neither `edge-tts`, `lameenc`, `mutagen`, nor `av` (PyAV) are in `requirements.txt` — they're only needed for this offline generation step, not at runtime, so `pip install edge-tts lameenc mutagen av` ad hoc (requires `dangerouslyDisableSandbox: true` on Bash for the network calls). Write a one-off script (in the scratchpad dir) that, per section, per item (in flattened group→item order):
1. If `items[].speak` contains a comma **and** the section uses comma-split pauses (see the per-section table below — not all do), split on the **first** comma into two clauses, synthesize each separately via `edge_tts.Communicate(text, "en-CA-LiamNeural", rate="-5%").stream()`, decode each clip to PCM with PyAV (`av.open` + `av.AudioResampler(format="s16", layout="mono", rate=24000)`), and join the two PCM arrays with a block of zero-samples sized to that section's comma-gap duration. If there's no comma, or the section doesn't use comma-splitting, decode the whole synthesized sentence to PCM as one clip.
2. Track a running sample-count cursor (at 24000 Hz) and record `[cursor/24000, (cursor+len(item_pcm))/24000]` as that item's timing entry; advance the cursor by `len(item_pcm) + len(gap_pcm)` where the gap length is that section's between-item gap (see table below; section 6 additionally depends on the item's `secondary` field).
3. Append every item's PCM + trailing gap PCM into one big in-memory array for the whole section, then encode it **once** with `lameenc` (`set_bit_rate(48)`, `set_in_sample_rate(24000)`, mono) into a single mp3, saved under `assets/classes/english_with_kyle/Agility_accelarator/` (note: folder name is spelled without the second "e" — `Agility_accelarator`, not `Agility_accelerator`) using the section's exact title as the filename (sanitizing `\/:*?"<>|` if present, `:` → ` -`), then set that section's `audio` field to the relative path and its `timings` field to the recorded list.

**Why decode-concat-reencode instead of splicing raw mp3 bytes:** an earlier version of this script synthesized each clause/gap as its own independently-LAME-encoded mp3 and concatenated the raw bytes. That mostly plays back fine, but every independent encode carries its own small encoder priming/padding overhead, and those overheads compound across the ~2-3 splices per item — on a 64-item, ~465s section this produced roughly 5s (~1%) of drift between the computed `timings` and the actual decoded playback length, enough to visibly desync the karaoke highlight by the end of the section. Decoding every clip to raw PCM up front, concatenating the *samples*, and running a single `lameenc` pass over the whole section eliminates the internal splice points entirely, so the file's real duration matches the arithmetic `timings` to within a few tens of milliseconds. Always use the PCM pipeline, not raw byte concatenation, when (re)generating a section's audio.

**PyAV plane-buffer gotcha (must slice to `frame.samples`):** when pulling PCM out of `resampler.resample(frame)`, do **not** append `bytes(rframe.planes[0])` directly — the plane's `buffer_size` is padded/aligned and can be noticeably larger than the frame's actual valid data (observed: 1216-byte buffer for a 576-sample s16 mono frame, i.e. 1152 valid bytes — 64 bytes of leftover/uninitialized buffer content per frame). Appending the raw plane pulls that padding in as audio *in the middle of* the concatenated stream (not just at the end), which decodes as a faint periodic buzz/static across the entire clip — easy to miss on a quick listen but audible as "poor quality/noise" on a full playthrough. Always slice explicitly: `bytes(rframe.planes[0])[:rframe.samples * bytes_per_sample]` (2 bytes/sample for s16), for every frame from both the main `resampler.resample(frame)` loop and the final `resampler.resample(None)` flush call. If a section's audio ever sounds noisy/staticky, this is the first thing to check before re-suspecting the TTS voice or encoder settings.

**Per-section comma-split pause / between-item gap values** (not a single global default — check this table before regenerating a section):

| Section | Comma-split pause | Between-item gap |
|---|---|---|
| 1. Common Irregular Verb Practice | 450ms | 500ms |
| 2. Irregular Verbs: Simple Past vs. Present Perfect | 900ms | 900ms |
| 3. Common Collocations | 900ms | 900ms |
| 4. Comparatives and Superlatives | none (see exception) | 2500ms |
| 5. Such + Irregular Verbs | 450ms | 500ms |
| 6. Mastering the Interrogative | none (no commas in content) | see exception |
| 7. Focused Pronoun Practice | 450ms | 900ms |

**Section 4 exception:** `"4. Comparatives and Superlatives"` does **not** get the comma-split pause, even though about half its items contain a comma (the `"No, ..."` answer sentences) — every item is synthesized as a single uninterrupted clip regardless of commas. It still gets the flat between-item gap from the table above. If this section's content changes, regenerate it without the comma-split step; don't reuse the general per-section script as-is.

**Section 6 exception:** `"6. Mastering the Interrogative"` items strictly alternate `secondary: "Statement"` / `secondary: "Question"` pairs (a fact stated aloud, then the question that elicits it — no commas in any item). The gap **after a Statement item** (before its paired Question plays) is **5000ms**, giving the learner time to formulate the question themselves before hearing it. The gap after a Question item (before the next Statement) is **2500ms**. If this section's content changes, regenerate preserving this alternation-aware gap, keyed off each item's `secondary` field.

If a section's content or delay values are changed again, regenerate both the mp3 and `timings` together — they must stay in lockstep, since `timings` indexes are positional (flattened group→item order) with no id to re-match against.

**Tab avatars:** `_inject_tab_avatars(pic_paths)` injects a `<style>` block that uses CSS `::after` pseudo-elements on each `button[data-baseweb="tab"]:nth-child(n)` to render a 26×26 px circular profile photo (base64-embedded) to the right of the tab label text. Avatar images live in `assets/profilepictures/`. The function detects MIME type from the file extension (`.png` → `image/png`, anything else → `image/jpeg`). Pass `None` in the list for a tab that has no profile picture yet — the function skips it silently. An additional CSS rule using `[role="tabpanel"] button[data-baseweb="tab"]::after { content: none }` cancels the avatar bleed onto nested sub-tabs.

**Class selector:** Within each tab, buttons sorted newest → oldest by `date` field. Most recent has a 🆕 badge and is selected by default. Selected button renders as `type="primary"`, others as `type="secondary"`. Laid out two-per-row via a fresh `st.columns(2)` for every pair (row-major: item 0 & 1 share a row, 2 & 3 share the next, etc.) rather than one `st.columns(2)` reused for the whole list — this keeps chronological order correct when Streamlit's built-in responsive breakpoint collapses each row to a single column on narrow (phone) screens. Don't revert to a single `st.columns(2)` filled via `cols[i % 2]` — that reads column-major (all even indices, then all odd) and shows out-of-order dates once collapsed to one column on mobile.

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

**Inline synced audio inside a regular class section (`audio_blocks`):** A regular (non-Agility-Accelerator) section can embed one or more Agility-Accelerator-style karaoke-sync players partway through its own markdown, e.g. to make specific drills (not the whole section) listen-along, without duplicating that content as plain bullets too. `_render_class` in `class_test.py` renders, in order: `content` (markdown, the part before the first drill), then for each entry in `audio_blocks` (in list order) — `_render_agility_section_synced(block)` (using that block's own `audio`/`timings`/`groups`, exact same schema as an Agility Accelerator section) followed by that block's `content_after` (markdown, everything up to the next drill or the end of the section). A section with no drills simply has no `audio_blocks` key. To add a drill: split the section's `content` string at the point where the player should appear, move everything from that point onward into a new block's `content_after`, remove the corresponding bullet list from that markdown (it would otherwise be shown twice — once as plain bullets, once as the synced player's own sentence list), and generate `audio`/`timings`/`groups` via the same edge-tts → PCM → lameenc pipeline used for the Agility Accelerator (see below) — one flat `groups: [{"items": [...]}]`, no alternating `secondary` unless the drill itself alternates. Save the mp3 next to the class's other assets, e.g. `assets/classes/english_with_kyle/kyle_YYYYMMDD/<drill_name>.mp3`. Adding a second drill to an already-drilled section: append a new block to the existing `audio_blocks` list and move the trailing chunk of the *previous* block's `content_after` (everything from the new drill's heading onward) into the new block's own `content_after`. If the table/list being converted has no `###` heading directly above it (some sections just flow straight from the intro paragraph into a table), insert a short new heading there before splitting — the deep-link anchor scroll (see below) needs a real heading to target, and a bare table/bullet list isn't one.

Gap convention for these drills: default to a flat 900ms between-item gap (same as the Agility Accelerator's simpler sections), with no comma-splitting, unless every item in the source content already came without commas — re-check before reusing this default if new content has commas. For a drill that's genuinely a question/answer pair (not just a flat list of examples), use the alternating 5000ms-after-Question / 2500ms-after-Answer gap instead (same rationale as the Agility Accelerator's Section 6: thinking time before the answer plays), keyed off each item's `secondary` field. This alternating pattern isn't limited to literal Q&A — a cue → transformed-answer drill (e.g. *accustomed to* → *used to*) uses the same 5000/2500 split with `secondary: "Cue"` / `"Answer"` instead of `"Question"`/`"Answer"`.

If the source material is a markdown table whose "Example" column *is* the practice content (rather than a separate bullet list below the table), pull those example sentences out into the drill items and drop the Example column from the table (keep the other reference columns — e.g. verb forms — since those aren't duplicated elsewhere); leave a short new heading in their place, same as the bullet-list case. Don't leave the full sentences sitting in both the table and the audio block.

Retrofitting a drill into an **already-committed, older** class works the same way as adding one to a brand-new class — this isn't limited to classes being added for the first time. Most drills added so far have been retrofits onto classes committed weeks earlier.

First used for the "Not quite as … as" and "Not nearly as … as" drills inside `kyle_20260428`'s "4. Comparatives with as…as" section (two blocks in one section's `audio_blocks`), then extended to: `kyle_20260428`'s "just about as…as" (a third block in the same section); all three subsections of `kyle_20260526`'s "Way" as Amplifier section (comparative adjective / more-fewer-less / too + adjective, one block each, flat 900ms); the "Quantity Comparisons" grammar across three separate classes — `kyle_20260505`'s "Not As Many / Not As Much" table, `kyle_20260602`'s "Examples from Class" list, and `kyle_20260716`'s "Not As Many / Not As Much Examples" table plus its "From the Agility Accelerator (superlative comparisons)" list (two blocks in one section) — all flat 900ms; `kyle_20260709`'s "Comparative + Superlative Drill" (one block, alternating 5000ms/2500ms gap, since it's a real Question → Answer drill with a bonus non-alternating "Example" item tacked on the end using the 2500ms gap); `kyle_20260512`'s "By the time" examples (one block, flat 900ms, retrofit onto the "1. Warm-Up: Past Continuous" section); `kyle_20260521`'s "Let vs. Allow Examples" (one block, flat 900ms — heading renamed from a generic "Examples" to avoid an anchor collision with that class's Negative Shift section, which already used that heading); the "Used to Structures" grammar across three classes — `kyle_20260521`'s "Examples of Each" (flat 900ms), `kyle_20260526`'s "Recap Examples" (table's Example column converted, flat 900ms), and `kyle_20260716`'s pre-existing "Drills (accustomed to → used to)" list (alternating 5000ms/2500ms, `secondary: "Cue"`/`"Answer"`); `kyle_20260505`'s "Raise vs. Rise Examples" (table's Example column converted, flat 900ms); and — the first time this was done for a class's own sections in the same session the class was created, rather than as a retrofit onto an older one — three blocks added to `kyle_20260901` (Sep 1): its "2. It Depends On" section's repeat-drill bullet list (heading added: "It Depends On — Drill", flat 900ms), its "3. Phrasal Verbs with 'Put' (Review)" section (table's Example column converted, heading "Put — Drill", flat 900ms), and its "4. To Have Trouble + -ing" section (the whole Spanish/English table replaced by the drill, since both columns duplicated it — heading "To Have Trouble — Drill", flat 900ms, expanded with two extra transcript examples beyond the original table's four rows). That class's "1. Warm-Up Translations" section was deliberately left without a drill, matching the standing rule that the generic top-level Warm-Up Translations table never gets retrofitted — only its named grammar-topic sections do.

**`teacher` field:** `"kyle"` for English with Kyle classes, `"julia"` for Essential English · Julia classes, `"juls"` for English Time with Juls classes, `"natural"` for Natural English classes, `"brain_buffet"` for Brain Buffet classes. Defaults to `"kyle"` if absent (for backwards compatibility).

**MP4 location:** `assets/classes/english_with_kyle/`, `assets/classes/esential_english_julia/`, `assets/classes/english_time_with_juls/`, `assets/classes/natural_english/`, or `assets/classes/brain_buffet/` depending on teacher.

**Adding a new class:** transcribe the MP4 with faster-whisper using `WhisperModel('medium', device='cpu', compute_type='int8')` and `model.transcribe(mp4, language='en', beam_size=5)`. Write a one-off Python script to build the entry dict and `json.load` → `cache.append` → `json.dump` — put it in the Claude Code scratchpad directory (not the project root) so no cleanup is needed. Do not commit MP4 files (`assets/classes/**/*.mp4` is gitignored).

**Transcribing from a Vimeo link:** if no local MP4 exists, download audio only with `yt-dlp -f bestaudio -o scratchpad/filename.%(ext)s <url>` — this produces a single `.m4a` file. (Avoid downloading video: Vimeo streams may not merge without ffmpeg, and audio alone is sufficient for transcription.) Delete the `.m4a` after transcription.

**Tests:** Kyle class entries must include a dedicated **"Test 1 · Warm-Up Translations"** test (covering the vocabulary and grammar from that class's warm-up sentences) as the **first** entry in `tests`, plus tests for each major topic covered in the class. Non-Kyle teachers (julia, juls, natural, brain_buffet) do **not** have a warm-up section — omit that test entirely for them. Do not label any section "Warm-Up" for non-Kyle classes; use "Discussion" or another descriptive title instead.

**After adding a Kyle class:** update `mindmap_kyle.html` (and `mindmap_kyle_network.html` if maintained) with the new content, increment the class count in the header, and sync: `cp mindmap_kyle.html static/mindmap_kyle.html`. Always commit both files together.

**After adding a non-Kyle class** (julia, juls, natural, brain_buffet): no mindmap update needed — just commit `class_cache.json`.

**Mindmap "Go to class" links:** Every `###` and `####` node that carries a `*(date)*` tag must include a `- [→ Go to class](/?class=kyle_YYYYMMDD)` bullet as its **first** child line. Multi-date nodes (e.g. `*(May 21 & 26)*`) get one link per class. The `## Prepositions of Place` branch has no sub-nodes, so its link sits directly as the first bullet under the `##` heading. Always add this link when creating a new node.

**Mindmap deep-link to a subsection:** The `/?class=` query param supports two optional extras, handled in `class_test.py` just above the `_cache`/tab-building code: `&section=N` (0-based index into that class's `sections` list — force-opens that section's `st.expander` regardless of its `expanded` field) and `&anchor=text` (URL-encoded substring — after the section renders, `_scroll_to_anchor()` injects a zero-height `components.html` script that searches `window.parent.document` for the first `h1`–`h6` heading containing that substring, scrolls it into view, and briefly flashes a yellow highlight). Use this instead of a plain "Go to class" link when a mindmap node should jump straight to one specific subheading inside a section's markdown `content` rather than just opening the class — e.g. `- [→ Jump to "..." drill](/?class=kyle_YYYYMMDD&section=3&anchor=some%20unique%20text)`. Pick the `anchor` text as a substring that appears **only** in the target `###`/`####` markdown heading itself (not in surrounding bullets), since the search matches any heading containing it. This scheme only exists in `class_test.py` (the mind map is only ever opened from there) — `app.py` has no equivalent.

**Anchor-collision gotcha:** the anchor search scans the whole rendered page, not just the section named by `&section=`, so a generic heading text (e.g. plain `"Examples"`) can collide with the same heading in a *different, `expanded: true`* section of the same class that renders earlier in the DOM — the scroll then jumps to the wrong (first-matching) heading. Before reusing a generic heading like `"### Examples"`, check the other section titles/headings in that same class for a duplicate; if one exists, rename the new heading to something more specific (e.g. `"### Let vs. Allow Examples"` instead of `"### Examples"`) rather than relying on section order.

**Linking a mindmap bullet to an `audio_blocks` drill:** When a mindmap bullet's text is drawn from (or closely paraphrases) a sentence that now lives inside an `audio_blocks` karaoke-sync drill, add a nested `- [→ Jump to "..." Agility accelerator](...)` bullet directly under it, one level deeper, pointing at that drill's heading via the `&section=`/`&anchor=` deep link above. Several bullets can point at the same drill anchor if they all draw from the same block. Skip this for bullets that are generic grammar-rule statements with no single matching sentence/heading (e.g. "**fewer** → countable · **less** → uncountable") — only add the link where there's a real anchor to jump to. When a mindmap branch aggregates content from multiple classes (e.g. "Quantity Comparisons" pulling from three different dated classes), each bullet's jump link points at whichever class/drill it actually came from, not a single shared one.

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
