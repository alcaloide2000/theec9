import base64
import streamlit as st
import streamlit.components.v1 as components
import json
import pathlib

st.set_page_config(page_title="Class Test", layout="wide")

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


def _load_class_cache():
    if not CACHE_PATH.exists():
        return []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _render_class(cls):
    st.subheader(f"CLASS — {cls['title']}")
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
    cols = st.columns(len(sorted_cls))
    for i, (col, c) in enumerate(zip(cols, sorted_cls)):
        with col:
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


_cache = _load_class_cache()

for _cls in _cache:
    for _t in _cls.get("tests", []):
        _tk = _t.get("key", "")
        if _tk and st.session_state.pop(f"{_tk}_reset_pending", False):
            st.session_state[f"{_tk}_sub"] = False
            for _qi in range(len(_t.get("qs", []))):
                st.session_state.pop(f"{_tk}_q{_qi}", None)
            st.rerun()

if not _cache:
    st.info("No class content available.")
else:
    kyle_classes = [c for c in _cache if c.get("teacher", "kyle") == "kyle"]
    julia_classes = [c for c in _cache if c.get("teacher") == "julia"]

    tab_kyle, tab_julia = st.tabs(["English with Kyle", "Essential English · Julia"])

    with tab_kyle:
        _render_teacher_tab(kyle_classes, "sel_kyle")

    with tab_julia:
        _render_teacher_tab(julia_classes, "sel_julia")
