from dash import html, dcc
from dash import Dash, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import random
import pandas as pd
import pathlib
from gtts import gTTS
import base64
import io
import os

# --------------------------------------------------
# APP INIT
# --------------------------------------------------

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ]
)

server = app.server
app.title = "theec practice"

# --------------------------------------------------
# LOAD EXCEL SAFELY
# --------------------------------------------------

BASE_PATH = pathlib.Path(__file__).parent
EXCEL_PATH = BASE_PATH / "the.xlsx"
dithe = pd.read_excel(EXCEL_PATH, sheet_name=None)

# --------------------------------------------------
# UTILS
# --------------------------------------------------

def generate_audio(text):
    if not text:
        return ""
    tts = gTTS(text=str(text), lang='en', tld='ca')
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    audio_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:audio/mp3;base64,{audio_base64}"

def pick_random(records):
    if not records:
        return None
    return random.choice(records)

# --------------------------------------------------
# DATA
# --------------------------------------------------

dfwarm = dithe['warm'].dropna(subset=['structure'])
dfreport = dithe['reportedsp']
dfpic = dithe['pictures']
dfinter = dithe['question'].dropna(subset=['word'])
dfinter['word'] = dfinter['word'].astype(str).str.strip()
dftag = dithe['tags']
dfnever = dithe['never']

warm_options = [{'label': 'all', 'value': 'all'}] + [
    {'label': str(x), 'value': x} for x in dfwarm['structure'].unique()
]

rep_options = [
    {'label': str(x), 'value': x} for x in dfreport['story'].unique()
]

inter_options = [{'label': 'all', 'value': 'all'}] + [
    {'label': x, 'value': x} for x in sorted(dfinter['word'].unique())
]

didfpic = dfpic.to_dict('records')
didftag = dftag.to_dict('records')
didfnever = dfnever.to_dict('records')

# --------------------------------------------------
# STYLE
# --------------------------------------------------

card_style = {
    "width": "100%",
    "margin": "auto",
    "padding": "10px",
    "borderColor": "#d9534f",
    "borderWidth": "2px"
}

# --------------------------------------------------
# CARDS
# --------------------------------------------------

def make_card(title, icon, body):
    return dbc.Card([
        html.H6([
            html.I(className=f"fas {icon} fa-3x", style={'color': 'grey'}),
            f" {title} ",
            html.I(className=f"fas {icon} fa-3x", style={'color': 'grey'})
        ], className="class-subtitle"),
        dbc.CardBody(body)
    ], style=card_style)

# Warm
card_warm = make_card(
    "TRANSLATION WARM-UP",
    "fa-running",
    [
        html.H4('CHOOSE A STRUCTURE'),
        dcc.Dropdown(warm_options, value='all', id='mydrop'),
        html.Div(id='container-button-timestamp0'),
        dbc.Button('SPANISH', id='btn-warm-es', color="info"),
        html.Div(id='container-button-timestamp'),
        dbc.Button('ENGLISH', id='btn-warm-en', color="primary"),
        html.Div(id='container-button-timestamp2'),
        html.Audio(id='tts-audiowarm', controls=True, style={'width': '100%'})
    ]
)

# Reported
card_rep = make_card(
    "REPORTED SPEECH",
    "fa-comments",
    [
        dcc.Dropdown(rep_options, value=rep_options[0]['value'], id='mydroprep'),
        html.Div(id='rep-info'),
        dbc.Button('DIRECT', id='btn-rep-direct', color="info"),
        html.Div(id='rep-direct'),
        dbc.Button('REPORTED', id='btn-rep-reported', color="primary"),
        html.Div(id='rep-reported'),
        html.Audio(id='tts-audiorep', controls=True, style={'width': '100%'})
    ]
)

# Interrogative
card_inter = make_card(
    "INTERROGATIVE CHALLENGE",
    "fa-question",
    [
        dcc.Dropdown(inter_options, value='all', id='mydropinter'),
        html.Div(id='inter-info'),
        dbc.Button('ANSWER', id='btn-inter-answer', color="info"),
        html.Div(id='inter-answer'),
        dbc.Button('QUESTION', id='btn-inter-question', color="primary"),
        html.Div(id='inter-question'),
        html.Audio(id='tts-audiointer', controls=True, style={'width': '100%'})
    ]
)

# Pictures
card_pic = make_card(
    "DESCRIBE THE PICTURES",
    "fa-camera",
    [
        dbc.Button('PICTURE', id='btn-pic-show', color="info"),
        html.Div(id='pic-img'),
        dbc.Button('DESCRIPTION', id='btn-pic-desc', color="primary"),
        html.Div(id='pic-desc'),
        html.Audio(id='tts-audiopic', controls=True, style={'width': '100%'})
    ]
)

# Tags
card_tag = make_card(
    "GUESS THE QUESTION TAG",
    "fa-tag",
    [
        dbc.Button('SENTENCE', id='btn-tag-sentence', color="info"),
        html.Div(id='tag-sentence'),
        dbc.Button('TAG', id='btn-tag-answer', color="primary"),
        html.Div(id='tag-answer'),
        html.Audio(id='tts-audiotag', controls=True, style={'width': '100%'})
    ]
)

# Never
card_never = make_card(
    "THINGS YOU HAVE NEVER DONE",
    "fa-icons",
    [
        dbc.Button('THING', id='btn-never-question', color="info"),
        html.Div(id='never-question'),
        dbc.Button('ANSWER', id='btn-never-answer', color="primary"),
        html.Div(id='never-answer'),
        html.Audio(id='tts-audionever', controls=True, style={'width': '100%'})
    ]
)

# --------------------------------------------------
# LAYOUT
# --------------------------------------------------

app.layout = dbc.Container([

    dcc.Tabs([

        dcc.Tab(label='Warm-Up', children=[dbc.Row(dbc.Col(card_warm))]),
        dcc.Tab(label='Reported Speech', children=[dbc.Row(dbc.Col(card_rep))]),
        dcc.Tab(label='Interrogative', children=[dbc.Row(dbc.Col(card_inter))]),
        dcc.Tab(label='Pictures', children=[dbc.Row(dbc.Col(card_pic))]),
        dcc.Tab(label='Question Tags', children=[dbc.Row(dbc.Col(card_tag))]),
        dcc.Tab(label='Never Done', children=[dbc.Row(dbc.Col(card_never))]),

    ]),

    dcc.Store(id='warm-store'),
    dcc.Store(id='warm-current'),
    dcc.Store(id='rep-store'),
    dcc.Store(id='rep-index'),
    dcc.Store(id='inter-store'),
    dcc.Store(id='inter-current'),
    dcc.Store(id='pic-current'),
    dcc.Store(id='tag-current'),
    dcc.Store(id='never-current')

], fluid=True)

# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

# Warm
@app.callback(
    Output('warm-store', 'data'),
    Input('mydrop', 'value')
)
def filter_warm(value):
    if value == 'all':
        return dfwarm.to_dict('records')
    return dfwarm[dfwarm['structure'] == value].to_dict('records')


@app.callback(
    [Output('container-button-timestamp', 'children'),
     Output('warm-current', 'data'),
     Output('container-button-timestamp2', 'children'),
     Output('tts-audiowarm', 'src')],
    [Input('btn-warm-es', 'n_clicks'),
     Input('btn-warm-en', 'n_clicks')],
    [State('warm-store', 'data'),
     State('warm-current', 'data')],
    prevent_initial_call=True
)
def warm_actions(btn1, btn2, data, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-warm-es':
        row = pick_random(data)
        if not row:
            return "No data", [], "", ""
        return row['esp'], [row], "", ""

    if button == 'btn-warm-en' and current:
        row = current[0]
        return no_update, current, row['eng'], generate_audio(row['eng'])

    return "", [], "", ""

# Pictures
@app.callback(
    [Output('pic-img', 'children'),
     Output('pic-current', 'data'),
     Output('pic-desc', 'children'),
     Output('tts-audiopic', 'src')],
    [Input('btn-pic-show', 'n_clicks'),
     Input('btn-pic-desc', 'n_clicks')],
    [State('pic-current', 'data')],
    prevent_initial_call=True
)
def picture_actions(btn1, btn2, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-pic-show':
        row = pick_random(didfpic)
        if not row:
            return "No data", [], "", ""
        filename = str(row['name']).strip()
        return html.Img(src=f"/assets/{filename}",
                        style={'width': '40%', 'display': 'block', 'margin': 'auto'}), [row], "", ""

    if button == 'btn-pic-desc' and current:
        row = current[0]
        return no_update, current, row['eng'], generate_audio(row['eng'])

    return "", [], "", ""

# Reported Speech
@app.callback(
    Output('rep-store', 'data'),
    Input('mydroprep', 'value')
)
def filter_rep(value):
    return dfreport[dfreport['story'] == value].to_dict('records')


@app.callback(
    [Output('rep-direct', 'children'),
     Output('rep-index', 'data'),
     Output('rep-reported', 'children'),
     Output('tts-audiorep', 'src')],
    [Input('btn-rep-direct', 'n_clicks'),
     Input('btn-rep-reported', 'n_clicks')],
    [State('rep-store', 'data'),
     State('rep-index', 'data')],
    prevent_initial_call=True
)
def rep_actions(btn1, btn2, data, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-rep-direct':
        row = pick_random(data)
        if not row:
            return "", [], "", ""
        return row['direct'], [row], "", ""

    if button == 'btn-rep-reported' and current:
        row = current[0]
        return no_update, current, row['reported'], generate_audio(row['reported'])

    return "", [], "", ""


# Interrogative
@app.callback(
    Output('inter-store', 'data'),
    Input('mydropinter', 'value')
)
def filter_inter(value):
    if value == 'all':
        return dfinter.to_dict('records')
    return dfinter[dfinter['word'] == value].to_dict('records')


@app.callback(
    [Output('inter-answer', 'children'),
     Output('inter-current', 'data'),
     Output('inter-question', 'children'),
     Output('tts-audiointer', 'src')],
    [Input('btn-inter-answer', 'n_clicks'),
     Input('btn-inter-question', 'n_clicks')],
    [State('inter-store', 'data'),
     State('inter-current', 'data')],
    prevent_initial_call=True
)
def inter_actions(btn1, btn2, data, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-inter-answer':
        row = pick_random(data)
        if not row:
            return "", [], "", ""
        return row['answer'], [row], "", ""

    if button == 'btn-inter-question' and current:
        row = current[0]
        return no_update, current, row['question'], generate_audio(row['question'])

    return "", [], "", ""


# Question Tags
@app.callback(
    [Output('tag-sentence', 'children'),
     Output('tag-current', 'data'),
     Output('tag-answer', 'children'),
     Output('tts-audiotag', 'src')],
    [Input('btn-tag-sentence', 'n_clicks'),
     Input('btn-tag-answer', 'n_clicks')],
    [State('tag-current', 'data')],
    prevent_initial_call=True
)
def tag_actions(btn1, btn2, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-tag-sentence':
        row = pick_random(didftag)
        if not row:
            return "", [], "", ""
        return row['sentence'], [row], "", ""

    if button == 'btn-tag-answer' and current:
        row = current[0]
        full = f"{row['sentence']} {row['tag']}"
        return no_update, current, row['tag'], generate_audio(full)

    return "", [], "", ""


# Never Done
@app.callback(
    [Output('never-question', 'children'),
     Output('never-current', 'data'),
     Output('never-answer', 'children'),
     Output('tts-audionever', 'src')],
    [Input('btn-never-question', 'n_clicks'),
     Input('btn-never-answer', 'n_clicks')],
    [State('never-current', 'data')],
    prevent_initial_call=True
)
def never_actions(btn1, btn2, current):
    ctx = callback_context
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    if button == 'btn-never-question':
        row = pick_random(didfnever)
        if not row:
            return "", [], "", ""
        return row['question'], [row], "", ""

    if button == 'btn-never-answer' and current:
        row = current[0]
        return no_update, current, row['answer'], generate_audio(row['answer'])

    return "", [], "", ""

# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 871))
    app.run_server(debug=False, port=port)
