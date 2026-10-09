import base64
import html
import random
import re
import streamlit as st
import json
import pathlib

st.set_page_config(page_title="Reviewing The English Collective", layout="wide")

st.title("Reviewing The English Collective")

BASE_PATH = pathlib.Path(__file__).parent
CACHE_PATH = BASE_PATH / "class_cache.json"
WALL_PATH = BASE_PATH / "wall_phrasal_verbs.json"


def _render_hotspot_image(img_path, hotspots):
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    html = f"""<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;font-family:sans-serif;overflow:hidden;}}
#wrap{{position:relative;max-width:700px;margin:0 auto;}}
#wrap img{{width:100%;display:block;border-radius:8px;}}
.hs{{position:absolute;border-radius:4px;cursor:help;transition:background .12s;}}
.hs:hover{{background:rgba(255,215,0,0.25);box-shadow:inset 0 0 0 2px rgba(255,185,0,0.85);}}
.tt{{
  visibility:hidden;opacity:0;transition:opacity .15s;
  position:absolute;z-index:99;
  background:rgba(12,12,12,0.93);color:#fff;
  padding:8px 13px;border-radius:8px;
  white-space:normal;max-width:280px;
  font-size:13px;line-height:1.5;font-weight:600;
  pointer-events:none;box-shadow:0 4px 16px rgba(0,0,0,0.55);
}}
.hs:hover .tt{{visibility:visible;opacity:1;}}
</style>
<div id="wrap"><img id="img" src="data:image/jpeg;base64,{b64}"></div>
<script>
var HS={json.dumps(hotspots)};
var img=document.getElementById('img');
var wrap=document.getElementById('wrap');
function build(){{
  HS.forEach(function(h){{
    var el=document.createElement('div');
    el.className='hs';
    el.style.cssText='left:'+h.x+'%;top:'+h.y+'%;width:'+h.w+'%;height:'+h.h+'%';
    var tt=document.createElement('div');
    tt.className='tt';
    tt.textContent=h.label;
    var mid=h.y+h.h/2;
    if(mid>=50){{tt.style.bottom='calc(100% + 6px)';tt.style.top='auto';}}
    else{{tt.style.top='calc(100% + 6px)';tt.style.bottom='auto';}}
    if(h.x+h.w/2>55){{tt.style.right='0';tt.style.left='auto';}}
    else{{tt.style.left='0';tt.style.right='auto';}}
    el.appendChild(tt);wrap.appendChild(el);
  }});
  window.parent.postMessage({{isStreamlitMessage:true,type:'streamlit:setFrameHeight',height:wrap.offsetHeight+10}},'*');
}}
img.complete?build():img.onload=build;
</script>"""
    st.iframe(html, height="content")


def _inject_tab_avatars(pic_paths):
    css_rules = []
    for i, pic in enumerate(pic_paths, start=1):
        if pic is None:
            continue
        mime = "image/png" if str(pic).lower().endswith(".png") else "image/jpeg"
        with open(pic, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        css_rules.append(f"""
[data-testid="stTab"]:nth-child({i})::after {{
    content: '';
    display: inline-block;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background-image: url('data:{mime};base64,{b64}');
    background-size: cover;
    background-position: center;
    margin-left: 8px;
    vertical-align: middle;
    align-self: center;
    flex-shrink: 0;
    border: 2px solid #d0d0d0;
}}""")
    css_rules.append("""
[role="tabpanel"] [data-testid="stTab"]::after,
[data-testid="stTabPanel"] [data-testid="stTab"]::after {
    content: none !important;
    background-image: none !important;
    display: none !important;
}""")
    st.markdown(f"<style>{''.join(css_rules)}</style>", unsafe_allow_html=True)


def _load_class_cache():
    if not CACHE_PATH.exists():
        return []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _scroll_to_anchor(text):
    script = f"""<script>
(function() {{
  var target = {json.dumps(text)};
  function tryScroll(attempts) {{
    var doc = window.parent.document;
    var headings = doc.querySelectorAll('h1,h2,h3,h4,h5,h6');
    for (var i = 0; i < headings.length; i++) {{
      if (headings[i].textContent.indexOf(target) !== -1) {{
        headings[i].scrollIntoView({{behavior: 'smooth', block: 'center'}});
        headings[i].style.transition = 'background-color 0.3s';
        headings[i].style.backgroundColor = 'rgba(255,205,0,0.55)';
        setTimeout(function() {{ headings[i].style.backgroundColor = 'transparent'; }}, 2200);
        return;
      }}
    }}
    if (attempts > 0) setTimeout(function() {{ tryScroll(attempts - 1); }}, 200);
  }}
  tryScroll(20);
}})();
</script>"""
    st.html(script, unsafe_allow_javascript=True)


def _render_class(cls, header=None):
    st.subheader(header or f"CLASS — {cls['title']}")
    st.markdown(f"**{cls['date']}** · {cls['topic']}")
    st.divider()

    deep_link = st.session_state.pop("_deep_link", None)
    if deep_link and deep_link.get("class") != cls.get("id"):
        deep_link = None

    for i, sec in enumerate(cls.get("sections", [])):
        force_open = deep_link is not None and deep_link.get("section") == i
        with st.expander(sec["title"], expanded=(force_open or sec.get("expanded", False))):
            if "image" in sec:
                if "image_hotspots" in sec:
                    _render_hotspot_image(BASE_PATH / sec["image"], sec["image_hotspots"])
                else:
                    st.image(str(BASE_PATH / sec["image"]))
            st.markdown(sec["content"])
            for block in sec.get("audio_blocks", []):
                _render_agility_section_synced(block)
                if block.get("content_after"):
                    st.markdown(block["content_after"])
            if force_open and deep_link.get("anchor"):
                _scroll_to_anchor(deep_link["anchor"])

    _render_tests(cls)


def _render_agility_item(item):
    content = ""
    if item.get("secondary"):
        content += f"<span style='color:#888'>{item['secondary']}</span>  \n"
    content += item["text"]
    content += "\n<hr style='margin:4px 0 10px 0;border:none;border-top:1px solid rgba(128,128,128,0.25);'>"
    st.markdown(content, unsafe_allow_html=True)


def _render_agility_section_synced(sec, title="Agility Accelerator", blur_labels=()):
    """Karaoke-sync player. Items whose `secondary` is in `blur_labels` stay blurred
    until they start playing or are clicked (used by Reported Speech practice mode)."""
    with open(BASE_PATH / sec["audio"], "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    timings = sec["timings"]
    rows_html = []
    idx = 0
    for group in sec.get("groups", []):
        if group.get("name"):
            rows_html.append(f'<div class="group-name">{html.escape(group["name"])}</div>')
        for item in group["items"]:
            start, end = timings[idx]
            idx += 1
            secondary_html = f'<span class="secondary">{item["secondary"]}</span>' if item.get("secondary") else ""
            text_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(item["text"]))
            if item.get("secondary") in blur_labels:
                text_html = f'<span class="blur">{text_html}</span>'
            rows_html.append(
                f'<div class="sentence" data-start="{start}" data-end="{end}">'
                f'{secondary_html}{text_html}</div>'
            )

    component_html = f"""<style>
body{{font-family:"Source Sans Pro",sans-serif;margin:0;padding:0;}}
.group-name{{font-weight:700;margin:14px 0 6px 0;}}
.sentence{{padding:6px 8px;border-bottom:1px solid rgba(128,128,128,0.25);margin-bottom:2px;border-radius:6px;transition:background .15s;}}
.sentence.active{{background:rgba(255,205,0,0.32);}}
.secondary{{color:#888;font-size:0.85em;display:block;margin-bottom:2px;}}
#sentences{{max-height:440px;overflow-y:auto;margin-top:10px;}}
audio{{width:100%;}}
.blur{{filter:blur(6px);cursor:pointer;transition:filter .3s;user-select:none;}}
.blur.shown{{filter:none;user-select:auto;}}
</style>
<p>🔊 <b>{html.escape(title)}.</b> Click Play</p>
<audio id="aud" controls>
  <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
</audio>
<div id="sentences">{"".join(rows_html)}</div>
<script>
var aud = document.getElementById('aud');
var els = Array.prototype.slice.call(document.querySelectorAll('.sentence'));
var active = null;
aud.addEventListener('timeupdate', function() {{
  var t = aud.currentTime;
  var found = null;
  for (var i = 0; i < els.length; i++) {{
    var s = parseFloat(els[i].dataset.start), e = parseFloat(els[i].dataset.end);
    if (t >= s && t < e) {{ found = els[i]; break; }}
  }}
  if (found !== active) {{
    if (active) active.classList.remove('active');
    if (found) {{
      found.classList.add('active');
      var b = found.querySelector('.blur');
      if (b) b.classList.add('shown');
      found.scrollIntoView({{block: 'nearest', behavior: 'smooth'}});
    }}
    active = found;
  }}
}});
document.querySelectorAll('.blur').forEach(function(b) {{
  b.addEventListener('click', function() {{ b.classList.toggle('shown'); }});
}});
aud.addEventListener('ended', function() {{
  if (active) {{ active.classList.remove('active'); active = null; }}
}});
</script>"""
    st.iframe(component_html, height=580)


def _render_agility_accelerator(cls, header=None):
    st.subheader(header or cls["title"])
    st.markdown(f"*{cls['date']} edition* · {cls['topic']}")
    st.divider()

    for sec in cls.get("sections", []):
        with st.expander(sec["title"], expanded=sec.get("expanded", False)):
            if sec.get("intro"):
                st.markdown(sec["intro"])
            if sec.get("timings"):
                _render_agility_section_synced(sec)
            else:
                if sec.get("audio"):
                    st.markdown("🔊 **Click play to hear this section read aloud**")
                    st.audio(str(BASE_PATH / sec["audio"]))
                for group in sec.get("groups", []):
                    if group.get("name"):
                        st.markdown(f"**{group['name']}**")
                    for item in group["items"]:
                        _render_agility_item(item)

    _render_tests(cls)


def _render_tests(cls):
    st.divider()
    st.markdown("### Tests")

    for test in cls.get("tests", []):
        key = test["key"]
        sub_key = f"{key}_sub"
        if sub_key not in st.session_state:
            st.session_state[sub_key] = False

        with st.expander(test["title"], expanded=False):
            for i, q in enumerate(test["qs"]):
                qk = f"{key}_q{i}"
                st.radio(q["q"], q["opts"], key=qk, index=None)
                if st.session_state[sub_key]:
                    sel = st.session_state.get(qk)
                    if sel == q["ans"]:
                        st.success("✓ Correct")
                    elif sel:
                        st.error(f'✗ Correct answer: **{q["ans"]}**')
                    else:
                        st.warning(f'Not answered · Correct answer: **{q["ans"]}**')

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Check answers", key=f"{key}_check", use_container_width=True):
                    st.session_state[sub_key] = True
                    st.rerun()
            with c2:
                if st.button("Reset", key=f"{key}_reset_btn", use_container_width=True):
                    st.session_state[f"{key}_reset_pending"] = True
                    st.rerun()

            if st.session_state[sub_key]:
                score = sum(
                    1 for i2, q2 in enumerate(test["qs"])
                    if st.session_state.get(f"{key}_q{i2}") == q2["ans"]
                )
                total = len(test["qs"])
                color = "green" if score >= total * 0.6 else "red"
                st.markdown(
                    f"<b style='color:{color}'>Score: {score} / {total}</b>",
                    unsafe_allow_html=True,
                )


def _render_teacher_tab(classes, sel_key):
    if not classes:
        st.info("No classes available yet.")
        return

    sorted_cls = sorted(classes, key=lambda c: c["date"], reverse=True)

    if sel_key not in st.session_state:
        st.session_state[sel_key] = 0

    if st.session_state[sel_key] >= len(sorted_cls):
        st.session_state[sel_key] = 0

    # Keep the selectbox's own widget state in sync with sel_key, which the
    # ?class= deep link can set before this widget renders.
    widget_key = f"{sel_key}_select"
    if st.session_state.get(widget_key) != st.session_state[sel_key]:
        st.session_state[widget_key] = st.session_state[sel_key]

    def _on_select():
        st.session_state[sel_key] = st.session_state[widget_key]

    st.selectbox(
        "Select a class",
        options=range(len(sorted_cls)),
        format_func=lambda i: f"{'🆕 ' if i == 0 else ''}{sorted_cls[i]['date']} · {sorted_cls[i]['topic']}",
        key=widget_key,
        on_change=_on_select,
    )

    st.divider()
    _render_class(sorted_cls[st.session_state[sel_key]])



def _collect_warmup_questions(kyle_classes):
    qs = []
    for cls in kyle_classes:
        for test in cls.get("tests", []):
            if "warm" in test["title"].lower():
                for q in test["qs"]:
                    qs.append({
                        "q": q["q"],
                        "opts": q["opts"],
                        "ans": q["ans"],
                        "from_date": cls["date"],
                        "from_topic": cls["topic"],
                        "from_id": cls["id"],
                    })
    return qs


def _collect_interrogative_pairs(kyle_classes):
    header_re = re.compile(r"^\|\s*(Statement|Answer)\s*\|\s*Question\s*\|\s*$", re.IGNORECASE)
    sep_re = re.compile(r"^\|[\s:|-]+\|$")
    pairs = []
    section_audio = {}
    for cls in kyle_classes:
        for sec in cls.get("sections", []):
            content = sec.get("content", "")
            if not content:
                continue
            lines = content.split("\n")
            i = 0
            while i < len(lines):
                m = header_re.match(lines[i].strip())
                if m and i + 1 < len(lines) and sep_re.match(lines[i + 1].strip()):
                    left_label = m.group(1)
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        cols = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                        if len(cols) == 2 and cols[0] and cols[1]:
                            pairs.append({
                                "left_label": left_label,
                                "left": cols[0],
                                "question": cols[1],
                                "from_date": cls["date"],
                                "from_topic": cls["topic"],
                                "from_section": sec["title"],
                            })
                        j += 1
                    i = j
                else:
                    i += 1
            if sec.get("interrogative_audio"):
                section_audio[(cls["date"], cls["topic"], sec["title"])] = {
                    "audio": sec["interrogative_audio"],
                    "timings": sec["interrogative_timings"],
                }
    return pairs, section_audio


def _collect_reported_speech(kyle_classes):
    """Collect every `| Direct speech | Reported speech |` table row from dated Kyle classes.

    Rows whose direct cell starts with a bold speaker tag (`**Name:**`) are dialogue lines;
    the rest (tense backshift, time & place words) are grammar-rule rows.
    """
    header_re = re.compile(r"^\|\s*Direct speech\s*\|\s*Reported speech\s*\|\s*$", re.IGNORECASE)
    sep_re = re.compile(r"^\|[\s:|-]+\|$")
    speaker_re = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")
    lines_out, rules, dialogue_audio, class_audio = [], [], {}, {}
    for cls in kyle_classes:
        for sec in cls.get("sections", []):
            for entry in sec.get("reported_audio", []):
                dialogue_audio[(cls["date"], entry["dialogue"])] = entry
            if sec.get("reported_audio_full"):
                class_audio[cls["date"]] = sec["reported_audio_full"]
            content = sec.get("content", "")
            lines = content.split("\n")
            heading = None
            i = 0
            while i < len(lines):
                stripped = lines[i].strip()
                if stripped.startswith("#"):
                    heading = stripped.lstrip("#").strip()
                if header_re.match(stripped) and i + 1 < len(lines) and sep_re.match(lines[i + 1].strip()):
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        cols = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                        if len(cols) == 2 and cols[0] and cols[1]:
                            m = speaker_re.match(cols[0])
                            if m:
                                lines_out.append({
                                    "speaker": m.group(1),
                                    "direct": m.group(2),
                                    "reported": cols[1],
                                    "dialogue": heading or sec["title"],
                                    "from_date": cls["date"],
                                    "from_topic": cls["topic"],
                                    "from_section": sec["title"],
                                })
                            else:
                                rules.append({"direct": cols[0], "reported": cols[1], "group": heading or sec["title"]})
                        j += 1
                    i = j
                else:
                    i += 1
    return lines_out, rules, dialogue_audio, class_audio


def _render_reported_speech(lines, rules, dialogue_audio, class_audio):
    st.markdown("## 📰 Reported Speech")
    if not lines and not rules:
        st.info("No reported speech content found yet.")
        return

    if rules:
        with st.expander("📏 The rules — tense backshift & time/place words", expanded=False):
            by_group, seen = {}, set()
            for r in rules:
                key = (r["direct"], r["reported"])
                if key in seen:
                    continue
                seen.add(key)
                by_group.setdefault(r["group"], []).append(r)
            for group, rows in by_group.items():
                st.markdown(f"**{group}**")
                body = "\n".join(f"| {r['direct']} | {r['reported']} |" for r in rows)
                st.markdown(f"| Direct speech | Reported speech |\n|---|---|\n{body}")

    if not lines:
        return

    n_dialogues = len({(l["from_date"], l["dialogue"]) for l in lines})
    st.markdown(f"**{len(lines)} lines** from **{n_dialogues} dialogues** collected from all Kyle classes.")
    practice = st.toggle(
        "Practice mode — hide the reported version until it plays or I click it",
        value=True,
        key="reported_practice",
    )
    st.divider()

    grouped = {}
    for l in lines:
        grouped.setdefault((l["from_date"], l["from_topic"]), []).append(l)

    for (date, topic), items in sorted(grouped.items(), key=lambda kv: kv[0][0], reverse=True):
        with st.expander(f"{date} — {topic}", expanded=False):
            by_dialogue = {}
            for l in items:
                by_dialogue.setdefault(l["dialogue"], []).append(l)
            full = class_audio.get(date)
            if full and len(full["timings"]) == 2 * len(items):
                mode = st.radio(
                    "Audio", ["Whole class (one track)", "By conversation"],
                    horizontal=True, key=f"reported_mode_{date}",
                )
                if mode == "Whole class (one track)":
                    groups = []
                    for dialogue, d_items in by_dialogue.items():
                        synth_items = []
                        for l in d_items:
                            synth_items.append({"text": l["direct"], "secondary": l["speaker"]})
                            synth_items.append({"text": l["reported"], "secondary": "Reported speech"})
                        groups.append({"name": dialogue, "items": synth_items})
                    _render_agility_section_synced(
                        {"audio": full["audio"], "timings": full["timings"], "groups": groups},
                        title="The whole class in one track — report each line before the answer plays",
                        blur_labels={"Reported speech"} if practice else (),
                    )
                    continue
            for dialogue, d_items in by_dialogue.items():
                st.markdown(f"#### {dialogue}")
                audio = dialogue_audio.get((date, dialogue))
                if audio and len(audio["timings"]) == 2 * len(d_items):
                    synth_items = []
                    for l in d_items:
                        synth_items.append({"text": l["direct"], "secondary": l["speaker"]})
                        synth_items.append({"text": l["reported"], "secondary": "Reported speech"})
                    _render_agility_section_synced(
                        {"audio": audio["audio"], "timings": audio["timings"],
                         "groups": [{"items": synth_items}]},
                        title="Listen and report it yourself before the answer plays",
                        blur_labels={"Reported speech"} if practice else (),
                    )
                elif practice:
                    parts = []
                    for l in d_items:
                        parts.append(
                            f"<div style='margin:0.6rem 0'>"
                            f"<div><b>{l['speaker']}:</b> {_md_bold_to_html(l['direct'])}</div>"
                            f"<details style='margin-left:1rem;color:#555'>"
                            f"<summary style='cursor:pointer;font-size:0.9em'>Show reported speech</summary>"
                            f"<div style='color:#1a7f37;font-weight:600;margin-top:0.2rem'>{_md_bold_to_html(l['reported'])}</div>"
                            f"</details></div>"
                        )
                    st.markdown("".join(parts), unsafe_allow_html=True)
                else:
                    body = "\n".join(
                        f"| **{l['speaker']}:** {l['direct']} | {l['reported']} |" for l in d_items
                    )
                    st.markdown(f"| Direct speech | Reported speech |\n|---|---|\n{body}")


def _md_bold_to_html(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)


def _load_phrasal_wall():
    if not WALL_PATH.exists():
        return []
    with open(WALL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_WALL_COLORS = {"in": "#2e86de", "into": "#8e44ad", "out": "#e67e22", "up": "#27ae60"}


def _render_phrasal_wall(wall):
    """Particle → concept bricks → verbs. Each verb is a <details> that reveals
    its meaning, an example and a link to the class it came from."""
    if not wall:
        st.info("Wall of Phrasal Verbs content not available yet.")
        return

    st.markdown(
        "Learn phrasal verbs by **particle + concept**, not one by one: one concept unlocks "
        "many verbs. Click a verb to see its meaning and an example."
    )
    particles = [p["particle"] for p in wall]
    col_p, col_q = st.columns([3, 2])
    choice = col_p.radio("Particle", ["All"] + particles, horizontal=True, key="wall_particle")
    query = col_q.text_input("Search a verb", key="wall_search").strip().lower()

    css = """<style>
.pw-row{margin:0 0 22px 0;}
.pw-particle{display:inline-block;font-size:1.5em;font-weight:800;color:#fff;padding:2px 18px;
  border-radius:8px;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;}
.pw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;}
.pw-brick{border:2px solid var(--pw-c);border-radius:10px;padding:10px 12px;
  background:color-mix(in srgb,var(--pw-c) 8%,transparent);}
.pw-icon{font-size:1.8em;text-align:center;}
.pw-eq{text-align:center;font-size:1.15em;margin:4px 0 2px 0;}
.pw-eq b{color:var(--pw-c);}
.pw-concept{text-align:center;color:#888;font-size:.85em;}
.pw-note{text-align:center;font-size:.8em;color:#888;margin:4px 0 6px 0;}
.pw-brick details{border-top:1px solid rgba(128,128,128,.25);padding:4px 2px;}
.pw-brick summary{cursor:pointer;font-weight:600;}
.pw-brick details p{margin:4px 0 2px 14px;font-size:.9em;}
.pw-ex{font-style:italic;}
.pw-brick a{font-size:.8em;}
</style>"""
    rows = []
    for p in wall:
        if choice != "All" and p["particle"] != choice:
            continue
        color = _WALL_COLORS.get(p["particle"], "#16a085")
        bricks = []
        for c in p["concepts"]:
            verbs = [v for v in c["verbs"] if query in v["verb"].lower()]
            if not verbs:
                continue
            verb_html = []
            for v in verbs:
                link = (f'<br><a href="/?class={v["cls"]}" target="_blank">→ Go to class</a>'
                        if v.get("cls") else "")
                verb_html.append(
                    f'<details><summary>{html.escape(v["verb"])}</summary>'
                    f'<p>{html.escape(v["meaning"])}<br>'
                    f'<span class="pw-ex">“{html.escape(v["example"])}”</span>{link}</p></details>'
                )
            note = f'<div class="pw-note">{c["note"]}</div>' if c.get("note") else ""
            bricks.append(
                f'<div class="pw-brick" style="--pw-c:{color}">'
                f'<div class="pw-icon">{c.get("icon", "")}</div>'
                f'<div class="pw-eq"><b>{html.escape(p["particle"])}</b> = {html.escape(c["es"])}</div>'
                f'<div class="pw-concept">{html.escape(c["concept"])}</div>'
                f'{note}{"".join(verb_html)}</div>'
            )
        if bricks:
            rows.append(
                f'<div class="pw-row"><span class="pw-particle" style="background:{color}">'
                f'{html.escape(p["particle"])}</span><div class="pw-grid">{"".join(bricks)}</div></div>'
            )
    if not rows:
        st.info("No phrasal verb matches your search.")
        return
    st.html(css + "".join(rows))


def _render_interrogative_challenge(pairs, section_audio):
    st.markdown("## ❓ The Interrogative Challenge")
    if not pairs:
        st.info("No interrogative statement/question pairs found yet.")
        return

    st.markdown(f"**{len(pairs)} statement → question pairs** collected from all Kyle classes.")
    st.divider()

    grouped = {}
    for p in pairs:
        grouped.setdefault((p["from_date"], p["from_topic"]), []).append(p)

    for (date, topic), items in sorted(grouped.items(), key=lambda kv: kv[0][0], reverse=True):
        with st.expander(f"{date} — {topic}", expanded=False):
            by_section = {}
            for p in items:
                by_section.setdefault(p["from_section"], []).append(p)
            for section_title, sec_items in by_section.items():
                st.markdown(f"**{section_title}**")
                meta = section_audio.get((date, topic, section_title))
                if meta:
                    synth_items = []
                    for p in sec_items:
                        synth_items.append({"text": p["left"], "secondary": p["left_label"]})
                        synth_items.append({"text": p["question"], "secondary": "Question"})
                    synth_sec = {
                        "audio": meta["audio"],
                        "timings": meta["timings"],
                        "groups": [{"items": synth_items}],
                    }
                    _render_agility_section_synced(synth_sec)
                else:
                    header_label = sec_items[0]["left_label"]
                    rows = "\n".join(f"| {p['left']} | {p['question']} |" for p in sec_items)
                    st.markdown(f"| {header_label} | Question |\n|---|---|\n{rows}")
                st.markdown("")


def _linguo_option_html(label, state):
    cfg = {
        "correct":    ("#45a100", "#d7f5b1", "#2d7a00", "600", "✓ "),
        "wrong":      ("#cc0000", "#ffd3d3", "#aa0000", "600", "✗ "),
        "neutral":    ("#d0d0d0", "#f5f5f5", "#666",    "400", ""),
    }
    border, bg, color, fw, icon = cfg.get(state, cfg["neutral"])
    st.markdown(
        f'<div style="padding:13px 18px;margin:5px 0;border-radius:12px;'
        f'border:2px solid {border};background:{bg};color:{color};'
        f'font-size:15px;font-weight:{fw};">{icon}{label}</div>',
        unsafe_allow_html=True,
    )


def _render_warmup_linguo(all_qs):
    if not all_qs:
        st.info("No warm-up translation questions found yet.")
        return

    # ── init state ──────────────────────────────────────────────────────────
    for key, val in [
        ("linguo_started", False),
        ("linguo_qs", []),
        ("linguo_idx", 0),
        ("linguo_score", 0),
        ("linguo_answered", False),
        ("linguo_selected", None),
        ("linguo_batch", "all"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    def _start_round(batch):
        st.session_state.linguo_batch = batch
        if batch == 10:
            pool = random.sample(all_qs, min(10, len(all_qs)))
        else:
            pool = all_qs.copy()
            random.shuffle(pool)
        st.session_state.linguo_qs = pool
        st.session_state.linguo_idx = 0
        st.session_state.linguo_score = 0
        st.session_state.linguo_answered = False
        st.session_state.linguo_selected = None
        st.session_state.linguo_started = True

    # ── start screen ────────────────────────────────────────────────────────
    if not st.session_state.linguo_started:
        st.markdown("## 🦜 Warm-Up Linguo")
        st.markdown(
            f"**{len(all_qs)} questions** collected from all Kyle classes — "
            "shuffled fresh every round."
        )
        st.markdown(
            "Each question shows the Spanish sentence from class; pick the correct English translation."
        )
        st.markdown("")
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            batch_choice = st.radio(
                "Round size",
                [f"All questions ({len(all_qs)})", "10 random questions"],
                index=0,
                horizontal=True,
                label_visibility="visible",
            )
            st.markdown("")
            if st.button("▶  Start", use_container_width=True, type="primary"):
                batch = 10 if batch_choice.startswith("10") else "all"
                _start_round(batch)
                st.rerun()
        return

    qs       = st.session_state.linguo_qs
    idx      = st.session_state.linguo_idx
    score    = st.session_state.linguo_score
    answered = st.session_state.linguo_answered
    selected = st.session_state.linguo_selected
    total    = len(qs)

    # ── finish screen ────────────────────────────────────────────────────────
    if idx >= total:
        pct = int(score / total * 100) if total else 0
        color = "green" if pct >= 70 else ("orange" if pct >= 40 else "red")
        msg = (
            "Outstanding! 🏆" if pct >= 90 else
            "Excellent! 🎉"   if pct >= 75 else
            "Good job! 👍"    if pct >= 60 else
            "Keep practising! 💪" if pct >= 40 else
            "Don't give up! 🔄"
        )
        st.markdown(f"## {msg}")
        st.markdown(
            f"<h2 style='color:{color};text-align:center'>{score} / {total} correct ({pct}%)</h2>",
            unsafe_allow_html=True,
        )
        st.progress(score / total)
        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶  Play Again", use_container_width=True, type="primary"):
                _start_round(st.session_state.linguo_batch)
                st.rerun()
        with c2:
            if st.button("✕  Quit", use_container_width=True):
                st.session_state.linguo_started = False
                st.rerun()
        return

    # ── question screen ──────────────────────────────────────────────────────
    q = qs[idx]

    st.progress((idx) / total)
    prog_col, score_col = st.columns([3, 1])
    with prog_col:
        st.caption(f"Question {idx + 1} of {total}")
    with score_col:
        if idx > 0:
            st.caption(f"✅ {score} / {idx}")

    st.markdown("")
    st.markdown(f"### {q['q']}")
    st.markdown("")

    opts = q["opts"]

    if not answered:
        for i, opt in enumerate(opts):
            if st.button(opt, key=f"linguo_opt_{idx}_{i}", use_container_width=True):
                st.session_state.linguo_selected = opt
                st.session_state.linguo_answered = True
                if opt == q["ans"]:
                    st.session_state.linguo_score += 1
                st.rerun()
    else:
        for opt in opts:
            if opt == q["ans"]:
                state = "correct"
            elif opt == selected:
                state = "wrong"
            else:
                state = "neutral"
            _linguo_option_html(opt, state)

        st.markdown("")
        if selected == q["ans"]:
            st.success("🎉 Correct!")
        else:
            st.error(f"The correct answer was: **{q['ans']}**")
        st.caption(f"From: {q['from_date']} — {q['from_topic']}")
        st.markdown("")
        if st.button("Continue →", key=f"linguo_continue_{idx}", use_container_width=True, type="primary"):
            st.session_state.linguo_idx += 1
            st.session_state.linguo_answered = False
            st.session_state.linguo_selected = None
            st.rerun()


_cache = _load_class_cache()

for _cls in _cache:
    for _t in _cls.get("tests", []):
        _tk = _t.get("key", "")
        if _tk and st.session_state.pop(f"{_tk}_reset_pending", False):
            st.session_state[f"{_tk}_sub"] = False
            for _qi in range(len(_t.get("qs", []))):
                st.session_state.pop(f"{_tk}_q{_qi}", None)
            st.rerun()

# Deep-link: /?class=kyle_XXXXXXXX jumps straight to that class in the Kyle tab.
# Optional &section=N (0-based index into that class's sections list) also force-opens
# that section's expander; optional &anchor=text additionally scrolls to and briefly
# highlights the first heading inside it containing that text.
_qp_class = st.query_params.get("class")
if _qp_class:
    _kyle_sorted = sorted(
        [c for c in _cache if c.get("teacher", "kyle") == "kyle"],
        key=lambda c: c["date"], reverse=True,
    )
    for _i, _c in enumerate(_kyle_sorted):
        if _c["id"] == _qp_class:
            st.session_state["sel_kyle"] = _i
            break
    _qp_section = st.query_params.get("section")
    if _qp_section is not None:
        try:
            st.session_state["_deep_link"] = {
                "class": _qp_class,
                "section": int(_qp_section),
                "anchor": st.query_params.get("anchor"),
            }
        except ValueError:
            pass
    st.query_params.clear()

if not _cache:
    st.info("No class content available.")
else:
    kyle_classes = [c for c in _cache if c.get("teacher", "kyle") == "kyle"]
    agility_accelerator = next((c for c in _cache if c.get("id") == "kyle_agility_accelerator"), None)
    julia_classes = [c for c in _cache if c.get("teacher") == "julia"]
    juls_classes = [c for c in _cache if c.get("teacher") == "juls"]
    natural_classes = [c for c in _cache if c.get("teacher") == "natural"]
    brain_buffet_classes = [c for c in _cache if c.get("teacher") == "brain_buffet"]

    _inject_tab_avatars([
        BASE_PATH / "assets/profilepictures/kyle.jpg",
        BASE_PATH / "assets/profilepictures/julia.jpg",
        BASE_PATH / "assets/profilepictures/juls.jpg",
        BASE_PATH / "assets/profilepictures/julia.jpg",
        BASE_PATH / "assets/profilepictures/brain_buffet.png",
    ])
    tab_kyle, tab_julia, tab_juls, tab_natural, tab_brain_buffet = st.tabs([
        "English with Kyle",
        "Essential English · Julia",
        "English Time with Juls",
        "Natural English",
        "Brain Buffet",
    ])

    with tab_kyle:
        (kyle_tab_classes, kyle_tab_mindmap, kyle_tab_linguo, kyle_tab_agility,
         kyle_tab_interrogative, kyle_tab_reported, kyle_tab_wall) = st.tabs(
            ["Classes", "🧠 Mind Map", "🦜 Warm-Up Linguo", "📘 Agility Accelerator",
             "❓ The Interrogative Challenge", "📰 Reported Speech", "🧱 Wall of Phrasal Verbs"]
        )
        with kyle_tab_classes:
            _render_teacher_tab(kyle_classes, "sel_kyle")
        with kyle_tab_mindmap:
            st.link_button("Open full mind map ↗", url="/app/static/mindmap_kyle.html", use_container_width=True)
        with kyle_tab_linguo:
            _render_warmup_linguo(_collect_warmup_questions(kyle_classes))
        with kyle_tab_agility:
            if agility_accelerator:
                _render_agility_accelerator(agility_accelerator, header="📘 Agility Accelerator")
            else:
                st.info("Agility Accelerator content not available yet.")
        with kyle_tab_interrogative:
            _render_interrogative_challenge(*_collect_interrogative_pairs(kyle_classes))
        with kyle_tab_reported:
            _render_reported_speech(*_collect_reported_speech(kyle_classes))
        with kyle_tab_wall:
            _render_phrasal_wall(_load_phrasal_wall())

    with tab_julia:
        _render_teacher_tab(julia_classes, "sel_julia")

    with tab_juls:
        _render_teacher_tab(juls_classes, "sel_juls")

    with tab_natural:
        _render_teacher_tab(natural_classes, "sel_natural")

    with tab_brain_buffet:
        _render_teacher_tab(brain_buffet_classes, "sel_brain_buffet")
