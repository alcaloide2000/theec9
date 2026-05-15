import streamlit as st
import json
import pathlib

st.set_page_config(page_title="Class Test", layout="wide")

BASE_PATH = pathlib.Path(__file__).parent
CACHE_PATH = BASE_PATH / "class_cache.json"


def _load_class_cache():
    if not CACHE_PATH.exists():
        return []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


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
    _sorted = sorted(_cache, key=lambda c: c["date"], reverse=True)

    if "class_sel_idx" not in st.session_state:
        st.session_state.class_sel_idx = 0

    st.markdown("### Select a class")
    cols = st.columns(len(_sorted))
    for i, (col, c) in enumerate(zip(cols, _sorted)):
        with col:
            is_sel = st.session_state.class_sel_idx == i
            is_latest = i == 0
            label = f"{'🆕 ' if is_latest else ''}**{c['date']}**\n\n{c['topic']}"
            if st.button(
                label,
                key=f"cls_btn_{i}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state.class_sel_idx = i
                st.rerun()

    _cls = _sorted[st.session_state.class_sel_idx]
    st.divider()
    st.subheader(f"CLASS — {_cls['title']}")
    st.markdown(f"**{_cls['date']}** · {_cls['topic']}")
    st.divider()

    for sec in _cls.get("sections", []):
        with st.expander(sec["title"], expanded=sec.get("expanded", False)):
            st.markdown(sec["content"])

    st.divider()
    st.markdown("### Tests")

    for test in _cls.get("tests", []):
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
