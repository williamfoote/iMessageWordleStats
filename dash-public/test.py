import dash
from dash import Dash, dcc, html, Input, Output, State, callback_context
# import dash_core_components as dcc
# import dash_html_components as html

# import dash_table
# from dash_table import DataTable, FormatTemplate
# from dash.dependencies import Input, Output
# import dash_daq as daq

import plotly.express as px
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import re
import numpy as np

test = pd.read_csv("test_data_public.csv", parse_dates = ['date', 'timestamp'])

#################################################
######## These are links for logos later ########
#################################################

group_logo_link = "https://clipart.world/wp-content/uploads/2020/08/happy-group-of-students-png-transparent.png"
trophy_logo_link = "https://www.onlygfx.com/wp-content/uploads/2020/02/trophy-drawing-4-1.png"
efficiency_logo_link = "https://valleyindustrialtrucks.com/wp-content/uploads/2017/12/Energy-Efficiency.png.pagespeed.ce.8EaUDGAHkO.png"
speed_logo_link = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Angular_lightningbolt.svg/348px-Angular_lightningbolt.svg.png"


mean_score = test.score.mean(skipna=True)
lowest_scorer = test.groupby('name')['score'].describe().sort_values('mean').index[0]
lowest_score = test.groupby('name')['score'].describe().sort_values('mean').iloc[0, 1]
fastest = test.groupby('name')['time_from_mid'].describe().sort_values('mean').index[0]
fastest_time = test.groupby('name')['time_from_mid'].describe().sort_values('mean').iloc[0, 1]


# For the checklist, need to format the options and labels
names = test['name'].unique().tolist()

scatter_fig = px.scatter(test, x="score", y="time_from_mid", color="name",
                                     title = 'Speed vs Efficiency',
                         hover_data=['date'])\
                         .update_layout({'paper_bgcolor':'#6bab64', 'font': {'color':'white'}})

scatter_3d_fig = px.scatter_3d(data_frame = test, x='date',
                               y='score', z='time_from_mid',
                                     title = 'Speed vs Efficiency vs Date',
                               color='name',
                              labels={
                     "date": "Date",
                     "score": "Efficiency (Wordle Score)",
                     "time_from_mid": "Speed (Hours Since Midnight)"
                 }).update_scenes(xaxis_autorange="reversed")\
                    .update_layout({'paper_bgcolor':'#fcba03', 'font': {'color':'white'}})
    
app = dash.Dash(__name__, title='Wordle Analytics')

# Create the dash layout and overall div
app.layout = html.Div(children=[
    html.Br(),
    html.Br(),
    html.Br(),
    html.H1("A Deep Dive into YOUR Friends' Wordle Scores!"),
    html.Div(children = [
        html.Img(src = group_logo_link,
               style={'display': 'inline-block', 'height': '400px',
                      'width':'auto', 'vertical-align':'middle'}),
        html.H1(["The group's overall average Wordle score is", html.Br(),
                 '{:.2f} as of {:%B %d, %Y}.'''.format(mean_score, test['date'].max())],
               style={'display': 'inline-block', 'height': '600px',
                      'justify':'center', 'align':'center'})     
    ]),
    html.Div(children = [
       html.H1('A look at the current champions...',
               style={'display': 'inline-block', 'height': '600px',
                      'justify':'center', 'align':'center'}),
       html.Img(src = trophy_logo_link,
                style={'display': 'inline-block', 'height': '600px', 'vertical-align':'middle'})
    ]), 
    html.Div(children = [
        html.Img(src = efficiency_logo_link,
                style={'display': 'inline-block', 'width': '250px', 'height':'auto',
                       'vertical-align':'middle'}),
        html.H2("The most efficient Wordler is {0} with a mean score of {1:.2f}."\
            .format(lowest_scorer, lowest_score),
                style={'display': 'inline-block', 'height': '600px',
                      'justify':'center', 'align':'center'})    
    ]),
     html.Div(children = [
        html.H3('''The fastest Wordler is {0} who finishes {1:.2f}
                hours after midnight on average.'''.format(fastest, fastest_time),
                style={'display': 'inline-block', 'height': '600px',
                      'justify':'center', 'align':'center'}),
        html.Img(src = speed_logo_link,
                style={'display': 'inline-block', 'width': '250px', 'height':'auto',
                       'vertical-align':'middle'})
    ]),
    html.H1("Let's visualize your friends' progress in performance over time!"),
    # Add a div containing the line figure
    html.Br(),
    html.H2("Choose the metric to explore."),
    # dcc.Checklist(options = [{'label': i, 'value': i} for i in test.name.unique()]),
    html.Div(dcc.Dropdown(options = [{'label': 'Score', 'value': 'Score'},
                            {'label': 'Speed', 'value': 'Speed'}],
                value = 'Score', searchable = False, clearable = False,
                 id='sp_sc-dropdown'),
             style={'width': '50%', 'display': 'inline-block',
                    'align-items': 'center', 'justify-content': 'center'}
            ),
    html.H5("Select which players to look at."),
    html.Div(
            [
                dcc.Checklist(["All"], [], id="all2-checklist", inline=True),
                dcc.Checklist(names, [], id="name2-checklist", inline=True),
            ]
        ),
    html.Br(),
    html.Div(dcc.Graph(id='rolling_line-fig'),
            style={'width': '49%', 'margin':'auto'}), 
    # Add a div containing the bar figure
    html.Br(),
    html.Div(dcc.Graph(id='bar-fig'),
            style={'width': '49%', 'margin':'auto'}), 
    html.H2("Who's the best at both?"),
    html.Div(dcc.Graph(id='score-time-scatter-fig', figure=scatter_fig),
            style={'width': '49%', 'margin':'auto'}),
    html.Br(),
    html.Div(dcc.Graph(id='3d-fig', figure=scatter_3d_fig),
            style={'width': '49%', 'margin':'auto'})
    ])

#################################################
#### Checklist callback - synchronizing both ####
#################################################

@app.callback(
    Output("name2-checklist", "value"),
    Output("all2-checklist", "value"),
    Input("name2-checklist", "value"),
    Input("all2-checklist", "value"),
)
def sync_checklists(cities_selected, all_selected):
    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == "name2-checklist":
        all_selected = ["All"] if set(cities_selected) == set(names) else []
    else:
        cities_selected = names if all_selected else []
    return cities_selected, all_selected
    

@app.callback(Output(component_id = 'rolling_line-fig',
                     component_property = 'figure'),
              [Input(component_id = 'sp_sc-dropdown',
                    component_property = 'value')])
    
# Create function that updates whether to display speed or score stats

def choose_speed_score_line(input_value):
    if input_value == 'Score':
        rolling_line_fig = px.line(data_frame=test.sort_values('date'),
                           x='date', y='score_7',
                           title='Rolling Weekly Mean for Score', color = 'name')\
                            .update_layout({'paper_bgcolor':'#6bab64',
                                            'font': {'color':'white'}})
    else:
        rolling_line_fig = px.line(data_frame=test.sort_values('date'),
                           x='date', y='time_fm_7',
                           title='Rolling Weekly Mean for Speed', color = 'name')\
                            .update_layout({'paper_bgcolor':'#6bab64',
                                            'font': {'color':'white'}})
    return rolling_line_fig

@app.callback(Output(component_id = 'bar-fig',
                     component_property = 'figure'),
              [Input(component_id = 'sp_sc-dropdown',
                    component_property = 'value')])

def choose_speed_score_line(input_value):
    if input_value == 'Score':
        score_bar_fig = px.histogram(data_frame = test, x="score",
                                     title = 'Distribution of Score by Person', 
                                     color = 'name')\
                            .update_layout({'paper_bgcolor':'#fcba03',
                                            'font': {'color':'white'}})
    else:
        score_bar_fig = px.histogram(data_frame = test, x="time_from_mid",
                                     title = 'Distribution of Score by Person',
                                     color = 'name')\
                            .update_layout({'paper_bgcolor':'#fcba03',
                                            'font': {'color':'white'}})
    return score_bar_fig

if __name__ == '__main__':
    app.run_server(debug=True)