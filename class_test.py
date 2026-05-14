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
    _cls_options = {f"{c['date']} · {c['topic']}": c for c in _cache}
    _sel_label = st.selectbox("Select class", list(_cls_options.keys()), key="class_sel")
    _cls = _cls_options[_sel_label]
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
