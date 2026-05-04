import streamlit as st
import pandas as pd
import random
import pathlib
import io
from gtts import gTTS

st.set_page_config(page_title="theec practice", layout="centered")

# --------------------------------------------------
# DATA
# --------------------------------------------------

BASE_PATH = pathlib.Path(__file__).parent
EXCEL_PATH = BASE_PATH / "the.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(EXCEL_PATH, sheet_name=None)

dithe = load_data()

dfwarm  = dithe['warm'].dropna(subset=['structure'])
dfreport = dithe['reportedsp']
dfpic   = dithe['pictures']
dfinter = dithe['question'].dropna(subset=['word'])
dfinter['word'] = dfinter['word'].astype(str).str.strip()
dftag   = dithe['tags']
dfnever = dithe['never']

didfpic   = dfpic.to_dict('records')
didftag   = dftag.to_dict('records')
didfnever = dfnever.to_dict('records')

# --------------------------------------------------
# UTILS
# --------------------------------------------------

def generate_audio(text):
    if not text:
        return None
    tts = gTTS(text=str(text), lang='en', tld='ca')
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.getvalue()

def pick_random(records):
    return random.choice(records) if records else None

# --------------------------------------------------
# SESSION STATE DEFAULTS
# --------------------------------------------------

_defaults = {
    'warm_structure': 'all',
    'warm_limit':     10,
    'warm_count':     0,
    'warm_score':     {'correct': 0, 'incorrect': 0},
    'warm_current':   None,
    'warm_esp':       '',
    'warm_eng':       '',
    'warm_audio':     None,
    'rep_story':      None,
    'rep_current':    None,
    'rep_direct':     '',
    'rep_reported':   '',
    'rep_audio':      None,
    'inter_word':     'all',
    'inter_current':  None,
    'inter_answer':   '',
    'inter_question': '',
    'inter_audio':    None,
    'pic_current':    None,
    'pic_img':        None,
    'pic_desc':       '',
    'pic_audio':      None,
    'tag_current':    None,
    'tag_sentence':   '',
    'tag_answer':     '',
    'tag_audio':      None,
    'never_current':  None,
    'never_question': '',
    'never_answer':   '',
    'never_audio':    None,
}

for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------------------------------
# TABS
# --------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    'Warm-Up',
    'Reported Speech',
    'Interrogative',
    'Pictures',
    'Question Tags',
    'Never Done',
])

# ==================================================
# TAB 1 — WARM-UP
# ==================================================

with tab1:
    st.subheader('TRANSLATION WARM-UP')

    warm_structures = ['all'] + list(dfwarm['structure'].unique())
    structure = st.selectbox('Choose a structure', warm_structures, key='warm_drop')
    limit = st.radio('Select a bunch of questions:', [10, 20, 30], horizontal=True, key='warm_radio')

    if structure != st.session_state.warm_structure or limit != st.session_state.warm_limit:
        st.session_state.warm_structure = structure
        st.session_state.warm_limit     = limit
        st.session_state.warm_count     = 0
        st.session_state.warm_score     = {'correct': 0, 'incorrect': 0}
        st.session_state.warm_current   = None
        st.session_state.warm_esp       = ''
        st.session_state.warm_eng       = ''
        st.session_state.warm_audio     = None

    warm_data = (
        dfwarm.to_dict('records')
        if structure == 'all'
        else dfwarm[dfwarm['structure'] == structure].to_dict('records')
    )
    count     = st.session_state.warm_count
    limit_val = st.session_state.warm_limit

    if count >= limit_val and count > 0:
        st.success(f"Done! {limit_val}/{limit_val} questions completed.")
    elif count > 0:
        st.caption(f"Question {count} / {limit_val}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button('SPANISH', use_container_width=True, key='btn_warm_es'):
            if count < limit_val:
                row = pick_random(warm_data)
                if row:
                    st.session_state.warm_count   += 1
                    st.session_state.warm_current  = row
                    st.session_state.warm_esp      = row['esp']
                    st.session_state.warm_eng      = ''
                    st.session_state.warm_audio    = None

    with col2:
        if st.button('ENGLISH', use_container_width=True, key='btn_warm_en'):
            if st.session_state.warm_current:
                row = st.session_state.warm_current
                st.session_state.warm_eng   = row['eng']
                st.session_state.warm_audio = generate_audio(row['eng'])

    if st.session_state.warm_esp:
        st.info(st.session_state.warm_esp)

    if st.session_state.warm_eng:
        st.success(st.session_state.warm_eng)

    if st.session_state.warm_audio:
        st.audio(st.session_state.warm_audio, format='audio/mp3')

    st.divider()

    score       = st.session_state.warm_score
    total_scored = score['correct'] + score['incorrect']

    col3, col4 = st.columns(2)

    with col3:
        if st.button('✓ CORRECT', use_container_width=True, type='primary', key='btn_warm_correct'):
            if total_scored < limit_val:
                st.session_state.warm_score['correct'] += 1
                score       = st.session_state.warm_score
                total_scored = score['correct'] + score['incorrect']

    with col4:
        if st.button('✗ INCORRECT', use_container_width=True, key='btn_warm_incorrect'):
            if total_scored < limit_val:
                st.session_state.warm_score['incorrect'] += 1
                score       = st.session_state.warm_score
                total_scored = score['correct'] + score['incorrect']

    if total_scored > 0:
        color = 'green' if score['correct'] >= score['incorrect'] else 'red'
        st.markdown(
            f"<b style='color:{color}'>Score: {score['correct']} correct, "
            f"{score['incorrect']} incorrect ({total_scored}/{limit_val})</b>",
            unsafe_allow_html=True,
        )

# ==================================================
# TAB 2 — REPORTED SPEECH
# ==================================================

with tab2:
    st.subheader('REPORTED SPEECH')

    rep_stories = list(dfreport['story'].unique())
    story = st.selectbox('Choose a story', rep_stories, key='rep_drop')

    if story != st.session_state.rep_story:
        st.session_state.rep_story    = story
        st.session_state.rep_current  = None
        st.session_state.rep_direct   = ''
        st.session_state.rep_reported = ''
        st.session_state.rep_audio    = None

    rep_data = dfreport[dfreport['story'] == story].to_dict('records')

    col1, col2 = st.columns(2)

    with col1:
        if st.button('DIRECT', use_container_width=True, key='btn_rep_direct'):
            row = pick_random(rep_data)
            if row:
                st.session_state.rep_current  = row
                st.session_state.rep_direct   = row['direct']
                st.session_state.rep_reported = ''
                st.session_state.rep_audio    = None

    with col2:
        if st.button('REPORTED', use_container_width=True, key='btn_rep_reported'):
            if st.session_state.rep_current:
                row = st.session_state.rep_current
                st.session_state.rep_reported = row['reported']
                st.session_state.rep_audio    = generate_audio(row['reported'])

    if st.session_state.rep_direct:
        st.info(st.session_state.rep_direct)

    if st.session_state.rep_reported:
        st.success(st.session_state.rep_reported)

    if st.session_state.rep_audio:
        st.audio(st.session_state.rep_audio, format='audio/mp3')

# ==================================================
# TAB 3 — INTERROGATIVE
# ==================================================

with tab3:
    st.subheader('INTERROGATIVE CHALLENGE')

    inter_words = ['all'] + sorted(dfinter['word'].unique().tolist())
    word = st.selectbox('Filter by question word', inter_words, key='inter_drop')

    if word != st.session_state.inter_word:
        st.session_state.inter_word     = word
        st.session_state.inter_current  = None
        st.session_state.inter_answer   = ''
        st.session_state.inter_question = ''
        st.session_state.inter_audio    = None

    inter_data = (
        dfinter.to_dict('records')
        if word == 'all'
        else dfinter[dfinter['word'] == word].to_dict('records')
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button('ANSWER', use_container_width=True, key='btn_inter_answer'):
            row = pick_random(inter_data)
            if row:
                st.session_state.inter_current  = row
                st.session_state.inter_answer   = row['answer']
                st.session_state.inter_question = ''
                st.session_state.inter_audio    = None

    with col2:
        if st.button('QUESTION', use_container_width=True, key='btn_inter_question'):
            if st.session_state.inter_current:
                row = st.session_state.inter_current
                st.session_state.inter_question = row['question']
                st.session_state.inter_audio    = generate_audio(row['question'])

    if st.session_state.inter_answer:
        st.info(st.session_state.inter_answer)

    if st.session_state.inter_question:
        st.success(st.session_state.inter_question)

    if st.session_state.inter_audio:
        st.audio(st.session_state.inter_audio, format='audio/mp3')

# ==================================================
# TAB 4 — PICTURES
# ==================================================

with tab4:
    st.subheader('DESCRIBE THE PICTURES')

    col1, col2 = st.columns(2)

    with col1:
        if st.button('PICTURE', use_container_width=True, key='btn_pic_show'):
            row = pick_random(didfpic)
            if row:
                st.session_state.pic_current = row
                st.session_state.pic_img     = str(row['name']).strip()
                st.session_state.pic_desc    = ''
                st.session_state.pic_audio   = None

    with col2:
        if st.button('DESCRIPTION', use_container_width=True, key='btn_pic_desc'):
            if st.session_state.pic_current:
                row = st.session_state.pic_current
                st.session_state.pic_desc  = row['eng']
                st.session_state.pic_audio = generate_audio(row['eng'])

    if st.session_state.pic_img:
        img_path = BASE_PATH / 'assets' / st.session_state.pic_img
        st.image(str(img_path), width=320)

    if st.session_state.pic_desc:
        st.success(st.session_state.pic_desc)

    if st.session_state.pic_audio:
        st.audio(st.session_state.pic_audio, format='audio/mp3')

# ==================================================
# TAB 5 — QUESTION TAGS
# ==================================================

with tab5:
    st.subheader('GUESS THE QUESTION TAG')

    col1, col2 = st.columns(2)

    with col1:
        if st.button('SENTENCE', use_container_width=True, key='btn_tag_sentence'):
            row = pick_random(didftag)
            if row:
                st.session_state.tag_current  = row
                st.session_state.tag_sentence = row['sentence']
                st.session_state.tag_answer   = ''
                st.session_state.tag_audio    = None

    with col2:
        if st.button('TAG', use_container_width=True, key='btn_tag_answer'):
            if st.session_state.tag_current:
                row = st.session_state.tag_current
                full = f"{row['sentence']} {row['tag']}"
                st.session_state.tag_answer = row['tag']
                st.session_state.tag_audio  = generate_audio(full)

    if st.session_state.tag_sentence:
        st.info(st.session_state.tag_sentence)

    if st.session_state.tag_answer:
        st.success(st.session_state.tag_answer)

    if st.session_state.tag_audio:
        st.audio(st.session_state.tag_audio, format='audio/mp3')

# ==================================================
# TAB 6 — NEVER DONE
# ==================================================

with tab6:
    st.subheader('THINGS YOU HAVE NEVER DONE')

    col1, col2 = st.columns(2)

    with col1:
        if st.button('THING', use_container_width=True, key='btn_never_question'):
            row = pick_random(didfnever)
            if row:
                st.session_state.never_current  = row
                st.session_state.never_question = row['question']
                st.session_state.never_answer   = ''
                st.session_state.never_audio    = None

    with col2:
        if st.button('ANSWER', use_container_width=True, key='btn_never_answer'):
            if st.session_state.never_current:
                row = st.session_state.never_current
                st.session_state.never_answer = row['answer']
                st.session_state.never_audio  = generate_audio(row['answer'])

    if st.session_state.never_question:
        st.info(st.session_state.never_question)

    if st.session_state.never_answer:
        st.success(st.session_state.never_answer)

    if st.session_state.never_audio:
        st.audio(st.session_state.never_audio, format='audio/mp3')
