import base64
import io
import random
import streamlit as st
import streamlit.components.v1 as components
import json
import pathlib
from gtts import gTTS

st.set_page_config(page_title="Reviewing The English Collective", layout="wide")

st.title("Reviewing The English Collective")

BASE_PATH = pathlib.Path(__file__).parent
CACHE_PATH = BASE_PATH / "class_cache.json"


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
    components.html(html, height=500, scrolling=False)


def _inject_tab_avatars(pic_paths):
    css_rules = []
    for i, pic in enumerate(pic_paths, start=1):
        if pic is None:
            continue
        mime = "image/png" if str(pic).lower().endswith(".png") else "image/jpeg"
        with open(pic, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        css_rules.append(f"""
button[data-baseweb="tab"]:nth-child({i})::after {{
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
[role="tabpanel"] button[data-baseweb="tab"]::after {
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


@st.cache_data
def _generate_audio(text):
    if not text:
        return None
    tts = gTTS(text=str(text), lang="en", tld="ca")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.getvalue()


def _render_class(cls, header=None):
    st.subheader(header or f"CLASS — {cls['title']}")
    st.markdown(f"**{cls['date']}** · {cls['topic']}")
    st.divider()

    for sec in cls.get("sections", []):
        with st.expander(sec["title"], expanded=sec.get("expanded", False)):
            if "image" in sec:
                if "image_hotspots" in sec:
                    _render_hotspot_image(BASE_PATH / sec["image"], sec["image_hotspots"])
                else:
                    st.image(str(BASE_PATH / sec["image"]))
            st.markdown(sec["content"])

    _render_tests(cls)


def _render_agility_item(item, item_key):
    audio_cache = st.session_state.setdefault("agility_audio", {})
    c1, c2 = st.columns([8, 1])
    with c1:
        if item.get("secondary"):
            st.markdown(f"<span style='color:#888'>{item['secondary']}</span>", unsafe_allow_html=True)
        st.markdown(item["text"])
    with c2:
        if st.button("🔊", key=f"{item_key}_btn", help="Listen"):
            audio_cache.setdefault(item_key, _generate_audio(item["speak"]))
            st.session_state["agility_last_played"] = item_key
    if item_key in audio_cache:
        st.audio(
            audio_cache[item_key],
            format="audio/mp3",
            autoplay=item_key == st.session_state.get("agility_last_played"),
        )
    st.markdown("---")


def _render_agility_accelerator(cls, header=None):
    st.subheader(header or cls["title"])
    st.markdown(f"*{cls['date']} edition* · {cls['topic']}")
    st.divider()

    for sec in cls.get("sections", []):
        with st.expander(sec["title"], expanded=sec.get("expanded", False)):
            if sec.get("intro"):
                st.markdown(sec["intro"])
            for group in sec.get("groups", []):
                if group.get("name"):
                    st.markdown(f"**{group['name']}**")
                for i, item in enumerate(group["items"]):
                    _render_agility_item(item, f"{cls['id']}_{sec['title']}_{group.get('name')}_{i}")

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

    st.markdown("### Select a class")
    cols = st.columns(2)
    for i, c in enumerate(sorted_cls):
        with cols[i % 2]:
            is_sel = st.session_state[sel_key] == i
            is_latest = i == 0
            label = f"{'🆕 ' if is_latest else ''}**{c['date']}**\n\n{c['topic']}"
            if st.button(
                label,
                key=f"{sel_key}_btn_{i}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state[sel_key] = i
                st.rerun()

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
        kyle_tab_classes, kyle_tab_mindmap, kyle_tab_linguo, kyle_tab_agility = st.tabs(
            ["Classes", "🧠 Mind Map", "🦜 Warm-Up Linguo", "📘 Agility Accelerator"]
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

    with tab_julia:
        _render_teacher_tab(julia_classes, "sel_julia")

    with tab_juls:
        _render_teacher_tab(juls_classes, "sel_juls")

    with tab_natural:
        _render_teacher_tab(natural_classes, "sel_natural")

    with tab_brain_buffet:
        _render_teacher_tab(brain_buffet_classes, "sel_brain_buffet")
