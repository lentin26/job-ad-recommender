from dash import Dash, dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import json
from DataFetcher import DataFetcher

ENDPOINT = "http://localhost:5000/job_ad/recommend"

# some sample user ids for the demo
sample_ies_ids = [
    '01f4bfc980a9448ab82e16eaf8c59d01',
    '02f84f625ffd49b99f56fc7adf8914c5',
    '03b4314b8b8e48d0afedab0210a13fd2',
    '04608de15ffa4914b347016f0e577cf4',
    '0471ffcda697430282f9272540276bde',
    '04f5382f6fb34f998d13598ecaa86019',
    '04fe48232e5245faabba48a29464aa37',
    '05be64f4c2da4bbca939d5ce5f67a56b',
    '06a3ca94826a4065bb0582781efe0d3d',
    '08ac33f1949a41568b0368f2900dd73a'
]

############################## test data #############################
with open('data/test_data.json') as f:
    test_data = json.load(f)


############################## fetch data #############################
# get data from data warehouses
fetcher = DataFetcher()

def get_job_ad_recs(ies_id):
    datapoint = test_data[ies_id]

    # cols = ['person_id', 'job_id', 'turbo_skill_id', 'job_role_id',
    #    'years_until_grad', 'school_id', 'user_academic_major_id', 'job_type',
    #    'job_title', 'company_name', 'skill_title']
    json_data = {str(k): v for k,v in enumerate(datapoint)}

    r = requests.post(ENDPOINT, json=json_data)
    return r

def fetch_data(ies_id, rec_job_ids):
    engaged_jobs_df = fetcher.fetch_engaged_jobs(ies_id)        # engaged (click bookmark, apply, details) jobs
    rec_jobs_df = fetcher.fetch_recommended_jobs(rec_job_ids)   # recommended jobs
    user_profile_df = fetcher.fetch_user_profile(ies_id)        # user profile

    return engaged_jobs_df, rec_jobs_df, user_profile_df

# initialize dashboard, request job ad recs
r = get_job_ad_recs(sample_ies_ids[0])

# engagement data, get user and job ad rec 
engaged_jobs_df, rec_jobs_df, user_profile_df = fetch_data(
    sample_ies_ids[0],
    r.json()["job_id"]
)


################# bar charts - skill frequency counts #################
def mk_bar_plot(data, title):
    return {
        'data': [
            {'x': data.index, 'y': data.values, 'type': 'bar', 'name': 'SF'}
        ],
        'layout': {
            'title': title
        }
    }

# make figures
engaged_job_skill_fig = mk_bar_plot(
    engaged_jobs_df.skill_title.value_counts().head(),
    title='Top 5 Skills from Engaged Job Ads')
rec_job_ad_skills_fig = mk_bar_plot(
    rec_jobs_df.skill_title.value_counts().head(),
    title='Top 5 Skills from Top 5 Recommended Job')


########################### rec job cards ###########################
def mk_card(title, desc, i=0):
    """
    Make recommended job ad cards with job title and company name.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.P(
                    desc
                ),
                # dbc.Button("Go somewhere", color="primary"),
            ]
        ), class_name='job-rec-cards', id='job-rec-card-{}'.format(i)
    )

# format cards horizontally in a row
cols = ['job_id', 'job_title', 'job_type', 'inferred_seniority_level', 'company_name']
ds = rec_jobs_df[cols].drop_duplicates().drop('job_id', axis=1).head().to_numpy()
cards = []
for i, d in enumerate(ds):
    cards += [dbc.Col(mk_card(d[0], d[1] + ' - ' + d[2] + ' - ' + d[3], i))]

job_rec_cards = dbc.Row(cards)

# format cards horizontally in a row
def mk_job_rec_card_body(rec_jobs_df):

    # get data to display on card
    ds = rec_jobs_df[cols]\
        .drop_duplicates().drop('job_id', axis=1)\
            .head().to_numpy()

    # build card bodies
    card_bodies = []
    for d in ds:
        title = d[0]
        desc = d[1] + ' - ' + d[2] + ' - ' + d[3]
        card_bodies.append(
            dbc.CardBody([html.H5(title, className="card-title"), html.P(desc)])
        )

    return card_bodies

######################### rec job confidence #########################
# card to give confidenced, normalised Faethm title
def mk_confidence_card(scores, i=0):
    """
    Make cared below corresponding recommended job ad cards with recommendation confidence.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                html.P("Confidence: " + str(round(float(scores[i]), 3))),
            ]
        ), class_name='job-confidence-cards', id='job-confidence-card-{}'.format(i)
    )

def mk_confidence_cards(scores, i=0):
    cards = []
    for i, d in enumerate(scores):
        cards += [dbc.Col(mk_confidence_card(scores, i))]

    return cards

def mk_confidence_card_bodies(scores):

    # build card bodies
    card_bodies = []
    for score in scores:
        card_bodies.append(
            dbc.CardBody(html.P("Confidence: " + str(round(float(score), 3))), className='confidence-card-p')
        )

    return card_bodies

scores = r.json()["score"]
cards = mk_confidence_cards(scores)
confidence_cards = dbc.Row(cards)

########################### profile card ############################

def mk_profile(user_profile_df, engaged_jobs_df):
    card_body = []
    card_body += [html.H5('User Profile', className="card-title")]

    for k, v in user_profile_df.to_dict(orient='records')[0].items():
        # bold [attribute name]: [values]
        card_body += [html.P(
            children=[
                html.Strong(k + ': '),
                html.Span(v)
            ], className='text-profile-card')
        ]

    # takes up too much space?
    card_body += [html.P(
        children=[
            html.Strong('Engaged Jobs: '),
            html.Span(", ".join(engaged_jobs_df.job_title.unique()).rstrip(','))
        ])
    ]
    
    return dbc.CardBody(card_body)

card_body = mk_profile(user_profile_df, engaged_jobs_df)

profile_card = dbc.Card(
        dbc.CardBody(card_body), 
        id='profile-card'
    )

########################## skill bar plots ##########################

skill_bar_plots = html.Div([
    dcc.Graph(figure=engaged_job_skill_fig, className='bar-plot', id='engaged-job-skill-bar-plot'),
    dcc.Graph(figure=rec_job_ad_skills_fig, className='bar-plot', id='rec-job-ad-skill-bar-plot'),
])

########################## page structure ###########################

page_structure = html.Div([
    dbc.Row(
        [ 
            dbc.Col(
                [profile_card],
                id='profile-column',
                width=2
            ),
            dbc.Col([
                dbc.Row(
                    [job_rec_cards],
                ),
                dbc.Row(
                    [confidence_cards],
                ),
                dbc.Row(
                    [skill_bar_plots],
                )]
            ),
        ],
        class_name="g-0",
    )
], id='dashboard-div')


############################ application ############################
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout =  html.Div([
    html.Div([
        html.H3("Turbo - Job Ad Recommender"),
    ], id='page-header'),
    html.Div([
        "Choose an IES ID: ",
        dcc.Dropdown(sample_ies_ids, sample_ies_ids[0], id='sample-ies-dropdown'),
    ]),
    html.Br(),
    page_structure,
    html.Br(),
    html.Div([
        html.P("Team: Consumer Profile and Data Analytics", className='text-footer'),
        html.P("Division: Direct to Consumer", className='text-footer'),
        html.P("Data Analyst: Maria Lentini", className='text-footer')
    ], id='page-footer')
], id='div-page')

# app.layout =  html.Div([
#     html.Div([
#         html.H3("Turbo - Job Ad Recommender"),
#     ], id='page-header'),
#     html.Div([
#         "Choose an IES ID: ",
#         dcc.Dropdown(sample_ies_ids, sample_ies_ids[0], id='sample-ies-dropdown'),
#     ]),
#     html.Br(),
#     job_rec_cards,
#     html.Br(),
#     # bar plots
#     skill_bar_plots,
#     # display profile attributes
#     profile_card,
#     html.Div([
#         html.P("Team: Consumer Profile and Data Analytics", className='text-footer'),
#         html.P("Division: Direct to Consumer", className='text-footer'),
#         html.P("Data Analyst: Maria Lentini", className='text-footer')
#     ], id='page-footer')
# ], id='div-page')


job_rec_card_outputs = [
    Output(component_id='job-rec-card-{}'.format(i), component_property='children')
    for i in range(5)  # change num to variable num_job_rec_cards
]

confidence_card_outputs = [
    Output(component_id='job-confidence-card-{}'.format(i), component_property='children')
    for i in range(5)  # change num to variable num_job_rec_cards
]


@callback(
    [Output(component_id='engaged-job-skill-bar-plot', component_property='figure'),
    Output(component_id='rec-job-ad-skill-bar-plot', component_property='figure'),
    Output(component_id='profile-card', component_property='children')] + job_rec_card_outputs + confidence_card_outputs,
    Input(component_id='sample-ies-dropdown', component_property='value')
)
def update_output_div(ies_id):
    # request new recommendations
    r = get_job_ad_recs(ies_id)

    # engagement data, get user and job ad rec 
    engaged_jobs_df, rec_jobs_df, user_profile_df = fetch_data(
        ies_id,
        r.json()["job_id"]
    )

    # make figures
    engaged_job_skill_fig = mk_bar_plot(
        engaged_jobs_df.skill_title.value_counts().head(),
        title='Top 5 Skills from Engaged Job Ads')
    rec_job_ad_skills_fig = mk_bar_plot(
        rec_jobs_df.skill_title.value_counts().head(),
        title='Top 5 Skills from Top 5 Recommended Job')

    # make profile card
    profile_card_body = mk_profile(user_profile_df, engaged_jobs_df)

    # make recommended job add card bodies
    rec_card_bodies = mk_job_rec_card_body(rec_jobs_df)
    confidence_score_bodies = mk_confidence_card_bodies(r.json()["score"])

    return engaged_job_skill_fig, rec_job_ad_skills_fig, profile_card_body, \
        rec_card_bodies[0], rec_card_bodies[1], rec_card_bodies[2], rec_card_bodies[3], rec_card_bodies[4], \
        confidence_score_bodies[0], confidence_score_bodies[1], confidence_score_bodies[3], confidence_score_bodies[3], confidence_score_bodies[4]


if __name__ == '__main__':
    app.run(debug=True, host = '127.0.0.1')