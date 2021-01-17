from collections import OrderedDict
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from data_module.read_data import listings_df, reviews_df
from credentials import Credentials
# ------------------------------------------------------------------------------
# Mapbox token
mapbox_access_token=Credentials.MAPBOX_API_TOKEN
# ------------------------------------------------------------------------------
# Data Cleaning

# dates df for the slider
date_slider=pd.period_range('2019-07',periods=12,freq='m').strftime('%Y-%m')

# listings df for the map
listings_reviews_df=reviews_df.groupby(['listing_id','date_ym']).count().reset_index()
listings_reviews_df.rename(columns={'date':'counts'},inplace=True)
listings_df=listings_df.merge(listings_reviews_df,how='left',left_on=['id','date_ym'],right_on=['listing_id','date_ym'])
listings_df['counts']=listings_df['counts'].fillna(0)
listings_df.drop('listing_id',axis=1,inplace=True)
listings_df['counts']=listings_df['counts'].astype(int)
def cut_counts(s):
    if s==0:
        reviews='None'
    elif s>0 and s<4:
        reviews='Low'
    elif s>=4 and s<10:
        reviews='Medium'
    elif s>=10:
        reviews='High'
    return reviews
listings_df['counts_cat']=listings_df.counts.apply(cut_counts)
color_map={'None':'#7F7F7F','Low':'#86CE00','Medium':'#FF7F0E','High':'#D62728'}
listings_df['color']=listings_df.counts_cat.map(color_map)
listings_df.drop('id',axis=1,inplace=True)

# review & room_ype df for the bar plot
reviews_type_df=listings_df.groupby(['city','date_ym','room_type']).sum().counts.reset_index()
color_map_type={'Entire home':'rgb(57,105,172)','Private room':'rgb(17,165,121)','Hotel':'rgb(242,183,1)','Shared':'rgb(127,60,141)'}
reviews_type_df['color']=reviews_type_df.room_type.map(color_map_type)

# price & room_type df for the line plot
price_type_df=listings_df.groupby(['city','date_ym','room_type']).median().price.reset_index()
price_type_df['price']=price_type_df['price'].astype('int64')
price_type_df['color']=price_type_df.room_type.map(color_map_type)

# ------------------------------------------------------------------------------
# external_stylesheets = [dbc.themes.BOOTSTRAP]
app=dash.Dash(__name__)
server = app.server
# ------------------------------------------------------------------------------
# Template
bar_bgcolor = "#b0bec5"  # material blue-gray 200
bgcolor = "#f3f3f1"  # mapbox light map land color
template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}
config_line = dict({'displaylogo': False,'displayModeBar': True,'modeBarButtonsToRemove':['zoom2d','pan2d','zoomIn2d','zoomOut2d','autoScale2d','hoverClosestCartesian','toggleSpikelines']})
config_bar = dict({'displaylogo': False,'displayModeBar': True,'modeBarButtonsToRemove':['zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','hoverClosestCartesian','toggleSpikelines']})
# config_map = dict({'displaylogo': False,'displayModeBar': True,'modeBarButtonsToRemove':['pan2d','select2d','lasso2d','zoomInGeo','zoomOutGeo','hoverClosestGeo']})
# hovertemplate_map=('<b>%{customdata[0]}</b><br>'
#                    # 'Type:%{customdata[1]}<br>'
#                    # 'Price:%{customdata[2]}<br>'
#                    ),
# ------------------------------------------------------------------------------
# Plots
fig_map=go.Figure()
fig_map.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="light",
            ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=250,
        )
def update_map(df):
    '''
    update map
    :param df: df with selected city and year
    :return: map figure
    '''
    fig_map.data=[]
    for counts in list(df.counts_cat.unique()):
        dff=df[df['counts_cat'] == counts]
        fig_map.add_trace(
            go.Scattermapbox(
                lat=dff['latitude'].values,
                lon=dff['longitude'].values,
                # 'text':,
                mode='markers',
                # 'Name':,
                visible=True,
                showlegend=False,
                marker=go.scattermapbox.Marker(
                    size=6,
                    color=dff['color'].values[0],
                    opacity=0.5),
                customdata=dff['name'].values,
                hovertemplate='<b> %{customdata}</b><br>',
            )
        )
    return fig_map

def review_counts(df):
    '''
    get the number of each review counts category
    :return: A dictionary of category number and counts
    '''
    dic = OrderedDict()
    bar_color=OrderedDict()
    dff = df.groupby('counts_cat').count().reset_index()
    if len(df.counts_cat.unique())==4:
        for i in ['None','Low','Medium','High']:
            dic[i] = dff[dff['counts_cat'] == i].color.values[0]
            bar_color[i]=df[df['counts_cat']==i].color.values[0]
    elif len(df.counts_cat.unique())==3:
        for i in ['None','Low','Medium']:
            dic[i] = dff[dff['counts_cat'] == i].color.values[0]
            bar_color[i]=df[df['counts_cat']==i].color.values[0]
    elif len(df.counts_cat.unique())==2:
        for i in ['None','Low']:
            dic[i] = dff[dff['counts_cat'] == i].color.values[0]
            bar_color[i] = df[df['counts_cat'] == i].color.values[0]

    return dic,bar_color

fig_hbar=go.Figure()
fig_hbar.update_layout(
        template=template,
        # barmode='overlay',
        dragmode='select',
        selectdirection='v',
        clickmode='event+select',
        selectionrevision=True,
        height=150,
        # width=500,
        margin={"l": 10, "r": 10, "t": 5, "b": 5},
        xaxis={
            # 'type': 'log',
            'title': {"text": "Listing Counts",'font':{'size':12}},
            # 'range': [0, np.log10(15000)],
            'automargin': True,
        },
        yaxis={
            'type': 'category',
            # 'categoryorder':'array',
            # 'categoryarray':['None', 'Low', 'Medium', 'High'],
            'side': 'left',
            'automargin': True
        }
    )

def update_hbar(df,lst):
    nums,b_color = review_counts(df)
    fig_hbar.data=[]
    fig_hbar.add_trace(
        go.Bar(
            x=[x for x in nums.values()],
            y=[y for y in nums.keys()],
            # customdata=[y for y in initial_nums.keys()],
            orientation='h',
            marker_color=[x for x in b_color.values()],
            selectedpoints=lst,
            unselected_marker_opacity=0.2,
            # hovertemplate=hovertemplate,
            showlegend=False
        )
    )

    return fig_hbar

fig_rbar=go.Figure()
fig_rbar.update_layout(
    template=template,
    barmode='stack',
    margin={"l": 10, "r": 10, "t": 5, "b": 5},
    height=220,
    xaxis_tickfont_size=10,
    yaxis={'title':{'text':'Number of Reviews/Month','font':{'size':12}},'automargin':True},
    yaxis_tickfont_size=10,
    legend=dict(orientation='h',y=-0.25, yanchor='bottom', xanchor='left', x=0,
                font=dict(
                    # family="Courier",
                    size=9,
                    # color="black"
                )
                )
)
fig_rbar.update_xaxes(showgrid=False)
def update_review_bar(df):
    fig_rbar.data=[]
    for i in list(df['room_type'].unique()):
        dff=df[df['room_type']==i]
        fig_rbar.add_trace(go.Bar(name=i,x=dff['date_ym'].values, y=dff['counts'].values,
                                  marker_color=dff['color'].values[0]
                                  ))                 # .data[0])
    return fig_rbar

fig_line=go.Figure()
fig_line.update_layout(
    template=template,
    barmode='stack',
    margin={"l": 10, "r": 10, "t": 5, "b": 5},
    height=220,
    xaxis_tickfont_size=10,
    yaxis_tickfont_size=10,
    yaxis={'title':{'text':'Price/Day ($)','font':{'size':12}},'automargin':True},
    legend=dict(orientation='h',y=-0.25,yanchor='bottom',xanchor='left',x=0,
                font=dict(
                # family="Courier",
                size=9,
                # color="black"
        )
    )
)
fig_line.update_xaxes(showgrid=False)
def update_price_line(df):
    fig_line.data=[]
    for i in list(df['room_type'].unique()):
        dff=df[df['room_type']==i]
        fig_line.add_trace(
            go.Scatter(name=i,x=dff['date_ym'].values,y=dff['price'].values,
                       mode='lines',marker_color=dff['color'].values[0])
        )
    return fig_line
# ------------------------------------------------------------------------------
app.layout=html.Div(
    children=[
        html.Div(
            html.H1(
                children='Airbnb Listings Analysis',
                style={'text-align':'left'}
            ),
        ),
        html.Div(
            children=[
                html.H4(
                    children='Listing Counts By Review Volumes',
                    className='container_title'
                ),
                dcc.Graph(id='review_slct',config={'displayModeBar': False}),
            ],
            className='twelve columns pretty_container',
            style={'width':'98%',
                   'margin-right':'0'},
            id='review-div'
        ),
        html.Div(
            children=[
                html.H4(
                    children='Listing Locations',
                    className='container_title'
                ),
                dcc.Dropdown(id='slct_city',
                             options=[
                                 {'label': 'Barossa Valley', 'value': 'Barossa Valley'},
                                 {'label': 'Barwon South West', 'value': 'Barwon South West, Vic'},
                                 {'label': 'Melbourne', 'value': 'Melbourne'},
                                 {'label': 'Northern Rivers', 'value': 'Northern Rivers'},
                                 {'label': 'Sydney', 'value': 'Sydney'},
                                 {'label': 'Tasmania', 'value': 'Tasmania'}],
                             multi=False,
                             value='Sydney',
                             style={'margin-bottom': '8px','background-color': 'transparent'},
                         ),
                dcc.Graph(id='dynamic_map',config={'displayModeBar': False}),
                # html.Button('Play', id='animation_play', n_clicks=0,className='reset-button',style={'width':'10%','margin-right':'6px'}),
                html.Button('Stepper', id='animation_step', n_clicks=0,className='reset-button',style={'width':'10%','margin-right':'6px'}),
                # html.Button('Pause', id='animation_pause', n_clicks=0,className='reset-button',style={'width':'10%'}),
                html.Button('Reset', id='animation_reset', n_clicks=0,className='reset-button',style={'width':'10%'}),
                dcc.Slider(id='year_slider',
                                       min=0,
                                       max=11,
                                       value=0,
                                       marks={
                                            0: {'label':'07/19','style':{'color': '#455A64'}},
                                            1: {'label':'08/19'},
                                            2: {'label':'09/19'},
                                            3: {'label':'10/19'},
                                            4: {'label':'11/19'},
                                            5: {'label':'12/19'},
                                            6: {'label':'01/20'},
                                            7: {'label':'02/20'},
                                            8: {'label':'03/20'},
                                            9: {'label':'04/20'},
                                            10: {'label':'05/20'},
                                            11: {'label':'06/20'},
                                       },
                                       step=None,
                                       className='slider',
                           ),
            ],
            className='twelve columns pretty_container',
            style={'width':'98%',
                   'margin-right':'0'},
            id='map-div'
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H4(
                            children='Monthly Reviews By Room Type',
                            className='container_title'
                        ),
                        dcc.Graph(id='review_barplot',config = config_bar)
                    ],
                    className='six columns pretty_container',
                    id='bar_plot_div'
                ),
                html.Div(
                    children=[
                        html.H4(
                            children='Price By Room Type',
                            className='container_title'
                        ),
                        dcc.Graph(id='price_lineplot',config=config_line)
                    ],
                    className='six columns pretty_container',
                    id='line_plot_div'
                )
            ]
        ),
        html.Div(
            children=[
                dcc.Interval(
                    id='interval-component',
                    interval=1*1000, # in milliseconds
                    max_intervals=11,
                    disabled=True,
                    n_intervals=0
                ),
            ]
        )
    ]
)
# ------------------------------------------------------------------------------
# Callback functions
@app.callback(
     [Output('review_slct','figure'),
     Output('dynamic_map','figure')],
     [Input('year_slider','value'),
     Input('slct_city','value'),
     Input('review_slct', 'selectedData')
      ])
def change_year_city(selected_year, city,review_cat):
    if city=='Sydney':
        zoom=8.2
        center={'lat':-33.8396, 'lon':151.2054}
    elif city=='Melbourne':
        zoom = 7.8
        center = {'lat': -37.8536, 'lon': 144.9631}
    elif city=='Tasmania':
        zoom=5.0
        center = {'lat': -41.7000, 'lon': 145.9707}
    elif city=='Northern Rivers':
        zoom=7.3
        center = {'lat': -28.6474, 'lon': 153.6020}
    elif city=='Barwon South West, Vic':
        zoom=7.1
        center = {'lat': -38.3410, 'lon': 143.5855}
    elif city=='Barossa Valley':
        zoom=8
        center = {'lat': -34.5333, 'lon': 138.9500}

    df=listings_df[(listings_df['city']==city)&(listings_df['date_num']==selected_year)]

    selected_review=['None', 'Low', 'Medium', 'High']
    if review_cat:
        selected_review=list(set(point['y'] for point in review_cat['points']))

    review_dict={'None':0,'Low':1,'Medium':2,'High':3}
    review_list=[review_dict[i] for i in selected_review]
    fig_hbar=update_hbar(df,review_list)

    dff = df[df['counts_cat'].isin(selected_review)]

    fig_map=update_map(dff)
    fig_map.update_layout(
        overwrite=True,
        mapbox_center=center,
        mapbox_zoom=zoom
    )
    return fig_hbar,fig_map

# @app.callback(
#     [Output('interval-component','disabled'),
#      Output('interval-component','n_intervals')],
#     [Input('animation_play','n_clicks'),
#     Input('animation_pause','n_clicks')],
#     State('year_slider','value'),
#     prevent_initial_call=True
# )
# def animation_trigger(m,n,year_slct):
#     '''
#     play and pause button for the animation
#     '''
#     changed_id=[p['prop_id'] for p in dash.callback_context.triggered][0]
#     intervals = year_slct
#     if 'animation_play' in changed_id:
#         dis=False
#     elif 'animation_pause' in changed_id:
#         dis=True
#     return dis,intervals
@app.callback(
    Output('interval-component','n_intervals'),
    [Input('animation_step','n_clicks'),
    Input('animation_reset','n_clicks')],
    State('year_slider','value'),
    prevent_initial_call=True
)
def animation_trigger(m,n,year_slct):
    '''
    stepper and reset button
    '''
    changed_id=[p['prop_id'] for p in dash.callback_context.triggered][0]
    intervals = year_slct
    if 'animation_step' in changed_id:
        step=intervals+1
    elif 'animation_reset' in changed_id:
        step=0
    return step

@app.callback(
    Output('year_slider','value'),
    Input('interval-component','n_intervals'),
    prevent_initial_call=True
)
def animation(interval):
    '''
    sync year slider
    '''
    value=interval
    return value

@app.callback(
    Output('review_barplot','figure'),
    Input('slct_city','value')
)
def create_barchart(city):
    df = reviews_type_df[reviews_type_df['city'] == city]
    fig = update_review_bar(df)
    return fig

@app.callback(
    Output('price_lineplot','figure'),
    Input('slct_city','value')
)
def create_lineplot(city):
    df=price_type_df[price_type_df['city'] == city]
    fig = update_price_line(df)
    return fig

# ------------------------------------------------------------------------------
if __name__=='__main__':
    app.run_server(debug=True)