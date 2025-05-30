from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import dash_ag_grid as dag
import plotly.express as px
import json

df = pd.read_csv('gapminder2007.csv')
# initialize the dash application
with open('world-countries.json', 'r') as file:
    geo_data = json.load(file)

map2 = px.choropleth_map(
    df,
    geojson=geo_data,
    color='lifeExp',
    locations = 'country',
    featureidkey='properties.name',
    center = {'lat': 35, 'lon': -104},
    zoom = 0.5
)


app = Dash()
app.layout = [
    dcc.Markdown('''
        # Data Visualization Dashboard
    '''),
    html.Div(children = "My first dashboard"),
    html.Hr(), # this horizontal line
    dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='pop', id = 'radio-item'),
    dash_table.DataTable(data=df.to_dict('records'), page_size= 10),
    dcc.Graph(figure = {}, id = 'figure-1'),

    # add new components
    dcc.Dropdown(['pop', 'lifeExp', 'gdpPercap'], value = 'pop', id = 'drop-down'),
    dcc.Graph(figure = {}, id = 'figure-2'),

    dcc.Checklist(
        ['lifeExp', 'gdpPercap'],
        ['lifeExp'],
        inline=True
    ),

    html.Div([
        html.Div([
            dcc.Graph(figure = px.box(df, x = 'continent', y = 'lifeExp'), id = 'figure-3')
        ], style = {'width': '49%', 'display': 'inline-block'}),


        html.Div([
            dcc.Graph(figure = px.box(df, x = 'continent', y = 'gdpPercap'), id = 'figure-4')
        ], style = {'width': '49%', 'display': 'inline-block'})
    ]),

    dag.AgGrid(
        id = 'ag-grid',
        rowData=df.to_dict('records'),
        columnDefs= [{'field':i} for i in df.columns], 
        dashGridOptions={'rowSelection': 'single'}
    ),

    html.Div(children="Highlight Information", style = {
        'textAlign': 'center',
        'color': 'blue', 
        'fontSize': 30}, id = 'hightlight'
    ),

    html.Iframe(id = 'map-1', srcDoc = open('chigao_map.html', 'r').read(), width = "80%", height= '660'),
    dcc.Graph(figure=map2)
]

# callback functions
@callback(
    Output(component_id='figure-1', component_property='figure'),
    Output(component_id= 'figure-2', component_property= 'figure'),
    Output(component_id= 'hightlight', component_property= 'children'),
    Input(component_id='radio-item', component_property='value'),
    Input(component_id = "drop-down", component_property= "value"),
    Input(component_id = "ag-grid", component_property= "selectedRows")
)
def update_layout(radio_item_value, drop_down_value, select_row_value):
    
    print(select_row_value)
    highlight_result = "Selected Country: "
    if select_row_value == None:
        highlight_result = "No country selected"
    else:
        highlight_result = highlight_result + select_row_value[0]['country']
    fig1 = px.histogram(df, x = 'continent', y = radio_item_value, histfunc= 'avg')
    fig2 = px.box(df, x = 'continent', y = drop_down_value)
    return fig1, fig2, highlight_result


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8050, debug=True)
    # 0.0.0.0 ask to listen to all available networks, making it more accessible