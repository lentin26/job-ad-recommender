from dash import Dash, dash_table, html
import dash_bootstrap_components as dbc
import pandas as pd
from collections import OrderedDict
from DataFetcher import DataFetcher
import requests
import json

ENDPOINT = "http://localhost:5000/job_ad/recommend"

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
fetcher = DataFetcher()

def get_job_ad_recs(ies_id):
    datapoint = test_data[ies_id]

    data = {
        "turbo_skill_id": datapoint[0],           
        "job_role_id": datapoint[1],              
        "years_until_grad": datapoint[2],          
        "school_id": datapoint[3],              
        "user_academic_major_id": datapoint[4]   
    }

    r = requests.post(ENDPOINT, json=data)
    return r

def fetch_data(ies_id, rec_job_ids):
    engaged_jobs_df = fetcher.fetch_engaged_jobs(ies_id)        # engaged (click bookmark, apply, details) jobs
    rec_jobs_df = fetcher.fetch_recommended_jobs(rec_job_ids)   # recommended jobs
    user_profile_df = fetcher.fetch_user_profile(ies_id)        # user profile

    return engaged_jobs_df, rec_jobs_df, user_profile_df

# initialize dashboard, request job ad recs
r = get_job_ad_recs(sample_ies_ids[2])

# engagement data, get user and job ad rec 
engaged_jobs_df, rec_jobs_df, user_profile_df = fetch_data(
    sample_ies_ids[2],
    r.json()["job_id"]
)

card = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Title", className="card-title"),
            html.H6("Card subtitle", className="card-subtitle"),
            html.P(
                "Some quick example text to build on the card title and make "
                "up the bulk of the card's content.",
                className="card-text",
            ),
            dbc.CardLink("Card link", href="#"),
            dbc.CardLink("External link", href="https://google.com"),
        ]
    ),
    style={"width": "18rem"},
)

def mk_card():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Card title", className="card-title"),
                html.P(
                    "This card also has some text content and not much else, but "
                    "it is twice as wide as the first card."
                ),
                dbc.Button("Go somewhere", color="primary"),
            ]
        ), class_name='profile-cards'
    )

cards = dbc.Row(
    [
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
    ]
)

from dash import dcc

# mk_graph
graph = dcc.Graph(
    figure={
        'data': [
            {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
            {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Montréal'},
        ],
        'layout': {
            'title': 'Dash Data Visualization'
        }
    }
)

graphs = dbc.Row(
    [
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
        dbc.Col(mk_card()),
    ]
)


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# app.layout = html.Div(
#     [
#         dbc.Row(
#             [
#                 dbc.Col(html.Div("Row 0, Column 0"),width=4),
#                 dbc.Col(html.Div("Row 0, Column 1"),width=4),
#                 dbc.Col(html.Div("Row 0, Column: 2"),width=4)
#             ]
#         )

#         ])


app.layout =  html.Div([
    # some profile cards across the top of the page
    card,
    cards,
    html.Div(children=[
        dcc.Graph(className='bar-plot'),
        dcc.Graph(className='bar-plot')
    ]),
    # job_rec_cards
    # dash_table.DataTable(
    #     style_data={
    #         'whiteSpace': 'normal',
    #         'height': 'auto',
    #     },
    #     data=df.to_dict('records'),
    #     columns=[{'id': c, 'name': c} for c in df.columns]
    # )
])

if __name__ == '__main__':
    app.run(debug=True, host = '127.0.0.1')