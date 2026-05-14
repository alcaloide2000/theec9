import streamlit as st
import pandas as pd
import random
import pathlib
import io
import json
import hashlib
import secrets
import os
from datetime import datetime
from gtts import gTTS

st.set_page_config(page_title="theec practice", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 3rem 2rem 1.5rem; max-width: 100%; }
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.75rem; }
    }
    div[data-testid="column"] { min-width: 0; }
    div[data-testid="stTabs"] { width: 100%; }
    div[data-testid="stTabsBarContainer"] {
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: none;
    }
    div[data-testid="stTabsBarContainer"]::-webkit-scrollbar { display: none; }
    button[data-baseweb="tab"] { white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATA
# --------------------------------------------------

BASE_PATH = pathlib.Path(__file__).parent
EXCEL_PATH = BASE_PATH / "the.xlsx"
USERS_PATH = BASE_PATH / "users.json"
PROGRESS_PATH = BASE_PATH / "progress.json"
HISTORY_PATH  = BASE_PATH / "history.json"
CACHE_PATH    = BASE_PATH / "class_cache.json"

# Keys persisted per user (audio bytes are excluded — regenerated on demand)
_PERSIST_KEYS = [
    'warm_structure', 'warm_limit', 'warm_count', 'warm_score',
    'warm_current', 'warm_esp', 'warm_eng', 'warm_scored', 'warm_result_saved',
    'rep_story', 'rep_current', 'rep_direct', 'rep_reported',
    'inter_word', 'inter_current', 'inter_answer', 'inter_question',
    'pic_current', 'pic_img', 'pic_desc',
    'tag_current', 'tag_sentence', 'tag_answer',
    'never_current', 'never_question', 'never_answer',
]

# --------------------------------------------------
# AUTH HELPERS
# --------------------------------------------------

def _load_users():
    if USERS_PATH.exists():
        with open(USERS_PATH, 'r') as f:
            return json.load(f)
    return {}

def _save_users(users):
    with open(USERS_PATH, 'w') as f:
        json.dump(users, f)

def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, digest

def _register(email, password):
    users = _load_users()
    if email in users:
        return False, "Email already registered."
    salt, digest = _hash_password(password)
    users[email] = {'salt': salt, 'hash': digest}
    _save_users(users)
    return True, "Account created!"

def _login(email, password):
    users = _load_users()
    if email not in users:
        return False, "Email not found."
    u = users[email]
    _, digest = _hash_password(password, u['salt'])
    if digest == u['hash']:
        return True, "Welcome!"
    return False, "Incorrect password."

# --------------------------------------------------
# PROGRESS PERSISTENCE
# --------------------------------------------------

def _to_json_safe(obj):
    """Convert numpy/pandas scalars to plain Python types for JSON serialisation."""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(i) for i in obj]
    if hasattr(obj, 'item'):
        return obj.item()
    return obj

def _load_progress(email):
    if not PROGRESS_PATH.exists():
        return {}
    with open(PROGRESS_PATH, 'r') as f:
        return json.load(f).get(email, {})

def _save_progress(email, state):
    all_progress = {}
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, 'r') as f:
            all_progress = json.load(f)
    all_progress[email] = _to_json_safe(
        {k: state[k] for k in _PERSIST_KEYS if k in state}
    )
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(all_progress, f)

def _load_history(email):
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, 'r') as f:
        return json.load(f).get(email, [])

def _load_class_cache():
    if not CACHE_PATH.exists():
        return []
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _append_result(email, structure, limit, correct, incorrect):
    all_history = {}
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, 'r') as f:
            all_history = json.load(f)
    entry = {
        'date':      datetime.now().strftime('%Y-%m-%d %H:%M'),
        'structure': structure,
        'limit':     limit,
        'correct':   correct,
        'incorrect': incorrect,
    }
    all_history.setdefault(email, []).append(entry)
    with open(HISTORY_PATH, 'w') as f:
        json.dump(all_history, f)

# --------------------------------------------------
# AUTH GATE
# --------------------------------------------------

if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.title("theec9 English Practice")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        l_email = st.text_input("Email", key="l_email")
        l_pass  = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login", use_container_width=True, key="btn_login"):
            ok, msg = _login(l_email.strip().lower(), l_pass)
            if ok:
                st.session_state.auth_user = l_email.strip().lower()
                st.rerun()
            else:
                st.error(msg)

    with register_tab:
        r_email   = st.text_input("Email", key="r_email")
        r_pass    = st.text_input("Password", type="password", key="r_pass")
        r_confirm = st.text_input("Confirm password", type="password", key="r_confirm")
        if st.button("Register", use_container_width=True, key="btn_register"):
            if not r_email or not r_pass:
                st.error("Email and password are required.")
            elif r_pass != r_confirm:
                st.error("Passwords do not match.")
            elif len(r_pass) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = _register(r_email.strip().lower(), r_pass)
                if ok:
                    st.session_state.auth_user = r_email.strip().lower()
                    st.rerun()
                else:
                    st.error(msg)

    st.stop()

with st.sidebar:
    st.markdown(f"Logged in as **{st.session_state.auth_user}**")
    if st.button("Logout", key="btn_logout"):
        _save_progress(st.session_state.auth_user, st.session_state)
        st.session_state.auth_user = None
        st.session_state._progress_loaded = False
        st.rerun()

# Load saved progress once per login session
if not st.session_state.get('_progress_loaded'):
    saved = _load_progress(st.session_state.auth_user)
    for k, v in saved.items():
        st.session_state[k] = v
    st.session_state._progress_loaded = True

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
    'warm_audio':        None,
    'warm_scored':       False,
    'warm_result_saved': False,
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    'Warm-Up',
    'Reported Speech',
    'Interrogative',
    'Pictures',
    'Question Tags',
    'Never Done',
    'Class',
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
        st.session_state.warm_structure      = structure
        st.session_state.warm_limit          = limit
        st.session_state.warm_count          = 0
        st.session_state.warm_score          = {'correct': 0, 'incorrect': 0}
        st.session_state.warm_current        = None
        st.session_state.warm_esp            = ''
        st.session_state.warm_eng            = ''
        st.session_state.warm_audio          = None
        st.session_state.warm_scored         = False
        st.session_state.warm_result_saved   = False

    warm_data = (
        dfwarm.to_dict('records')
        if structure == 'all'
        else dfwarm[dfwarm['structure'] == structure].to_dict('records')
    )
    count        = st.session_state.warm_count
    limit_val    = st.session_state.warm_limit
    score        = st.session_state.warm_score
    total_scored = score['correct'] + score['incorrect']

    if total_scored >= limit_val and limit_val > 0:
        if not st.session_state.warm_result_saved:
            _append_result(
                st.session_state.auth_user,
                st.session_state.warm_structure,
                limit_val,
                score['correct'],
                score['incorrect'],
            )
            st.session_state.warm_result_saved = True

        st.success(f"Test complete! Your score: **{score['correct']}/{limit_val}**")
        st.write("Would you like to try another set of questions?")
        if st.button('New Set', use_container_width=True, key='btn_warm_reset'):
            st.session_state.warm_count        = 0
            st.session_state.warm_score        = {'correct': 0, 'incorrect': 0}
            st.session_state.warm_current      = None
            st.session_state.warm_esp          = ''
            st.session_state.warm_eng          = ''
            st.session_state.warm_audio        = None
            st.session_state.warm_scored       = False
            st.session_state.warm_result_saved = False
            st.rerun()
    else:
        if count > 0:
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

        col3, col4 = st.columns(2)
        english_revealed = bool(st.session_state.warm_eng)

        scored_this_question = st.session_state.warm_scored
        with col3:
            if st.button('✓ CORRECT', use_container_width=True, type='primary', key='btn_warm_correct', disabled=not english_revealed or scored_this_question):
                if not st.session_state.warm_scored:
                    st.session_state.warm_score['correct'] += 1
                    st.session_state.warm_scored = True

        with col4:
            if st.button('✗ INCORRECT', use_container_width=True, key='btn_warm_incorrect', disabled=not english_revealed or scored_this_question):
                if not st.session_state.warm_scored:
                    st.session_state.warm_score['incorrect'] += 1
                    st.session_state.warm_scored = True

        score        = st.session_state.warm_score
        total_scored = score['correct'] + score['incorrect']

        if total_scored > 0:
            color = 'green' if score['correct'] >= score['incorrect'] else 'red'
            st.markdown(
                f"<b style='color:{color}'>Score: {score['correct']} correct, "
                f"{score['incorrect']} incorrect ({total_scored}/{limit_val})</b>",
                unsafe_allow_html=True,
            )

        if st.button('NEXT ▶', use_container_width=True, key='btn_warm_next', disabled=not st.session_state.warm_scored):
            if st.session_state.warm_scored:
                st.session_state.warm_scored = False
                row = pick_random(warm_data)
                if row:
                    st.session_state.warm_count   += 1
                    st.session_state.warm_current  = row
                    st.session_state.warm_esp      = row['esp']
                    st.session_state.warm_eng      = ''
                    st.session_state.warm_audio    = None
                st.rerun()

    st.divider()
    with st.expander('Edit questions'):
        edited = st.data_editor(
            dithe['warm'][['structure', 'esp', 'eng']],
            num_rows='dynamic',
            use_container_width=True,
            key='warm_editor',
        )
        if st.button('Save changes', key='btn_warm_save'):
            with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                edited.to_excel(writer, sheet_name='warm', index=False)
            load_data.clear()
            st.success('Saved!')
            st.rerun()

    st.divider()
    with st.expander('My test history'):
        history = _load_history(st.session_state.auth_user)
        if not history:
            st.caption('No completed tests yet.')
        else:
            df_hist = pd.DataFrame(history[::-1])  # newest first
            df_hist.columns = ['Date', 'Structure', 'Questions', 'Correct', 'Incorrect']
            df_hist['%'] = (df_hist['Correct'] / df_hist['Questions'] * 100).round(0).astype(int).astype(str) + '%'
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

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

# ==================================================
# TAB 7 — CLASS
# ==================================================

with tab7:
    _cache = _load_class_cache()

    for _cls in _cache:
        for _t in _cls.get('tests', []):
            _tk = _t.get('key', '')
            if _tk and st.session_state.pop(f'{_tk}_reset_pending', False):
                st.session_state[f'{_tk}_sub'] = False
                for _qi in range(len(_t.get('qs', []))):
                    st.session_state.pop(f'{_tk}_q{_qi}', None)
                st.rerun()

    if not _cache:
        st.info('No class content available.')
    else:
        _cls_options = {f"{c['date']} · {c['topic']}": c for c in _cache}
        _sel_label = st.selectbox('Select class', list(_cls_options.keys()), key='class_sel')
        _cls = _cls_options[_sel_label]
        st.subheader(f"CLASS — {_cls['title']}")
        st.markdown(f"**{_cls['date']}** · {_cls['topic']}")
        st.divider()

        for sec in _cls.get('sections', []):
            with st.expander(sec['title'], expanded=sec.get('expanded', False)):
                st.markdown(sec['content'])

        st.divider()
        st.markdown('### Tests')

        for test in _cls.get('tests', []):
            key = test['key']
            sub_key = f'{key}_sub'
            if sub_key not in st.session_state:
                st.session_state[sub_key] = False

            with st.expander(test['title'], expanded=False):
                for i, q in enumerate(test['qs']):
                    qk = f'{key}_q{i}'
                    st.radio(q['q'], q['opts'], key=qk, index=None)
                    if st.session_state[sub_key]:
                        sel = st.session_state.get(qk)
                        if sel == q['ans']:
                            st.success('✓ Correct')
                        elif sel:
                            st.error(f'✗ Correct answer: **{q["ans"]}**')
                        else:
                            st.warning(f'Not answered · Correct answer: **{q["ans"]}**')

                c1, c2 = st.columns(2)
                with c1:
                    if st.button('Check answers', key=f'{key}_check', use_container_width=True):
                        st.session_state[sub_key] = True
                        st.rerun()
                with c2:
                    if st.button('Reset', key=f'{key}_reset_btn', use_container_width=True):
                        st.session_state[f'{key}_reset_pending'] = True
                        st.rerun()

                if st.session_state[sub_key]:
                    score = sum(
                        1 for i2, q2 in enumerate(test['qs'])
                        if st.session_state.get(f'{key}_q{i2}') == q2['ans']
                    )
                    total = len(test['qs'])
                    color = 'green' if score >= total * 0.6 else 'red'
                    st.markdown(
                        f"<b style='color:{color}'>Score: {score} / {total}</b>",
                        unsafe_allow_html=True,
                    )

# Persist progress on every render so closing the browser tab saves state
_save_progress(st.session_state.auth_user, st.session_state)
