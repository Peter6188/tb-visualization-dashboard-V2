import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
from flask_caching import Cache
import datetime

# Load the TB data
tb_data = pd.read_csv('1-TB_Burden_Country.csv')

# Load the geographic data
with open('world-countries.json', 'r') as file:
    geo_data = json.load(file)

# Clean and preprocess the data
tb_data.rename(columns={
    'Country or territory name': 'country',
    'ISO 3-character country/territory code': 'iso_code',
    'Region': 'region',
    'Year': 'year',
    'Estimated total population number': 'population',
    'Estimated prevalence of TB (all forms) per 100 000 population': 'prevalence_per_100k',
    'Estimated prevalence of TB (all forms) per 100 000 population, low bound': 'prevalence_per_100k_low',
    'Estimated prevalence of TB (all forms) per 100 000 population, high bound': 'prevalence_per_100k_high',
    'Estimated mortality of TB cases (all forms, excluding HIV) per 100 000 population': 'mortality_per_100k',
    'Estimated mortality of TB cases (all forms, excluding HIV), per 100 000 population, low bound': 'mortality_per_100k_low',
    'Estimated mortality of TB cases (all forms, excluding HIV), per 100 000 population, high bound': 'mortality_per_100k_high',
    'Estimated incidence (all forms) per 100 000 population': 'incidence_per_100k',
    'Estimated incidence (all forms) per 100 000 population, low bound': 'incidence_per_100k_low',
    'Estimated incidence (all forms) per 100 000 population, high bound': 'incidence_per_100k_high',
}, inplace=True)

# Get the list of available years
years = sorted(tb_data['year'].unique())
latest_year = years[-1]
prev_year = years[-2] if len(years) > 1 else years[-1]

# Get the list of regions and countries
regions = sorted(tb_data['region'].unique())
countries = sorted(tb_data['country'].unique())

# Create a function to calculate percent change
def calc_percent_change(df, country, metric, year1, year2):
    try:
        val1 = df[(df['country'] == country) & (df['year'] == year1)][metric].iloc[0]
        val2 = df[(df['country'] == country) & (df['year'] == year2)][metric].iloc[0]
        if val1 == 0:
            return "N/A"
        return ((val2 - val1) / val1) * 100
    except:
        return "N/A"

# External stylesheets
external_stylesheets = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css',
]

# Create a Dash application
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True,
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5"},
                    {"name": "description", "content": "Interactive tuberculosis (TB) epidemiological dashboard"},
                    {"name": "keywords", "content": "tuberculosis, TB, WHO, health, epidemiology, data visualization"},
                ])

# Add custom CSS for the sidebar layout
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Custom styles for sidebar layout */
            .sidebar-container {
                position: sticky;
                top: 20px;
                height: fit-content;
                max-height: calc(100vh - 40px);
                overflow-y: auto;
                overflow-x: visible;
            }
            
            .sidebar-filters {
                border-left: 3px solid #005b82;
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: visible !important;
            }
            
            .main-content {
                min-height: 100vh;
            }
            
            .filter-label {
                color: #333;
                font-weight: 600;
                margin-bottom: 8px;
                display: block;
            }
            
            /* Dropdown specific styles */
            .Select-menu-outer {
                z-index: 9999 !important;
                max-height: 200px !important;
                overflow-y: auto !important;
            }
            
            .dropdown .Select-menu-outer {
                z-index: 9999 !important;
            }
            
            /* Dash dropdown specific styles */
            .dash-dropdown .Select-menu-outer,
            .dash-dropdown .VirtualizedSelectFocusedOption {
                z-index: 9999 !important;
            }
            
            /* Country dropdown gets higher priority */
            #country-filter .Select-menu-outer {
                z-index: 10000 !important;
            }
            
            /* Region dropdown has lower priority */
            #region-filter .Select-menu-outer {
                z-index: 9999 !important;
            }
            
            .sidebar-filters .Select-control {
                border-color: #ddd;
            }
            
            .sidebar-filters .Select-control:hover {
                border-color: #005b82;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .sidebar-container {
                    position: relative;
                    width: 100% !important;
                    margin-right: 0 !important;
                    margin-bottom: 20px;
                }
                
                .main-content {
                    width: 100% !important;
                }
                
                .flex-container {
                    flex-direction: column !important;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Setup cache for performance optimization
cache = Cache(app.server, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600  # 1 hour cache timeout
})

# Cache the expensive data processing operations
@cache.memoize()
def get_filtered_data(start_year, end_year, regions=None):
    # Filter data by year range
    filtered_data = tb_data[(tb_data['year'] >= start_year) & (tb_data['year'] <= end_year)]
    
    # Filter by regions if selected
    if regions and len(regions) > 0:
        filtered_data = filtered_data[filtered_data['region'].isin(regions)]
        
    return filtered_data

# App layout with WHO-inspired design and left sidebar
app.layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H2("Tuberculosis (TB) Epidemiological Dashboard", 
                   style={'color': '#005b82', 'fontWeight': 'bold'}),
            html.P("Interactive visualization of global tuberculosis burden and trends", 
                  style={'fontSize': '16px', 'color': '#666'})
        ], className="col-md-8"),
        html.Div([
            html.Div([
                html.Img(src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMTAwIDYwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjUwIiB5PSIzNSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzAwNWI4MiIgdGV4dC1hbmNob3I9Im1pZGRsZSI+V0hPPC90ZXh0Pjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5EYXRhIFNvdXJjZTwvdGV4dD48L3N2Zz4=", 
                        height="60px", 
                        style={'float': 'right'},
                        title="World Health Organization - Data Source")
            ], style={'textAlign': 'right'})
        ], className="col-md-4"),
    ], className="row mb-4 p-3 bg-white rounded shadow-sm"),
    
    # Main container with sidebar and content
    html.Div([
        # Left Sidebar for Filters
        html.Div([
            html.Div([
                html.H5("Filters", className="text-secondary mb-3 border-bottom pb-2"),
                
                # Country Filter
                html.Div([
                    html.Label("Select Country", className="filter-label"),
                    dcc.Dropdown(
                        id='country-filter',
                        options=[{'label': country, 'value': country} for country in countries],
                        value='Global',
                        style={'width': '100%', 'zIndex': '10000'},
                        placeholder="Select a country",
                        optionHeight=35,
                        maxHeight=200
                    ),
                ], className="mb-3", style={'zIndex': '10000', 'position': 'relative'}),
                
                # Region Filter
                html.Div([
                    html.Label("Filter by Region", className="filter-label"),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': region, 'value': region} for region in regions],
                        value=None,
                        placeholder="All Regions",
                        multi=True,
                        style={'width': '100%', 'zIndex': '9999'},
                        optionHeight=35,
                        maxHeight=200
                    ),
                ], className="mb-3", style={'zIndex': '9999', 'position': 'relative'}),
                
                # Year Range Filter
                html.Div([
                    html.Label("Year Range", className="filter-label"),
                    dcc.RangeSlider(
                        id='year-slider',
                        min=int(min(years)),
                        max=int(max(years)),
                        value=[int(min(years)), int(latest_year)],
                        marks={int(year): str(year) if year % 5 == 0 else "" for year in years},
                        step=1,
                        className="mt-2",
                    ),
                ], className="mb-3"),
                
            ], className="p-3 sidebar-filters rounded shadow-sm sidebar-container", style={'overflow': 'visible'})
        ], style={'width': '280px', 'minWidth': '280px', 'marginRight': '20px', 'overflow': 'visible'}, className="sidebar-container"),
        
        # Main Content Area
        html.Div([
            # Summary metrics section - WHO style
            html.Div([
                html.H4(id='key-indicators-title', className="mb-3 text-secondary"),
                html.Div(id='key-metrics', className="row"),
                html.Div([
                    html.P("Note: % changes compare the selected end year with the previous year (end year - 1).", 
                          className="text-muted small mt-2 mb-0")
                ], className="row mt-2 pl-3")
            ], className="mb-4 p-3 bg-white rounded shadow-sm"),
            
            # Metric selector (moved outside of tabs to apply globally)
            html.Div([
                html.H5("Select TB Metric", className="text-secondary mb-2"),
                dcc.RadioItems(
                    id='metric-selector',
                    options=[
                        {'label': 'TB Prevalence', 'value': 'prevalence_per_100k'},
                        {'label': 'TB Mortality', 'value': 'mortality_per_100k'},
                        {'label': 'TB Incidence', 'value': 'incidence_per_100k'}
                    ],
                    value='prevalence_per_100k',
                    inline=True,
                    className="mb-3"
                )
            ], className="mb-3 p-3 bg-white rounded shadow-sm"),
            
            # Main content tabs
            dcc.Tabs([
                # Epidemiological Profile Tab
                dcc.Tab(label='Epidemiological Profile', children=[
                    html.Div([
                        # Trend charts
                        html.Div([
                            html.H5("TB Burden Trends", className="text-secondary mb-3"),
                            dcc.Graph(id='trend-chart')
                        ], className="col-md-8 mb-4"),
                        
                        # Age/gender distribution
                        html.Div([
                            html.H5("Regional Distribution", className="text-secondary mb-3"),
                            dcc.Graph(id='region-distribution')
                        ], className="col-md-4 mb-4"),
                        
                        # Map
                        html.Div([
                            html.H5("Geographical Distribution", className="text-secondary mb-3"),
                            dcc.Graph(id='choropleth-map'),
                        ], className="col-md-12 mb-4"),
                    ], className="row")
                ]),
                
                # Data Explorer Tab
                dcc.Tab(label='Data Explorer', children=[
                    html.Div([
                        html.Div([
                            html.H5(id='data-table-title', className="text-secondary mb-3"),
                            dash_table.DataTable(
                                id='data-table',
                                columns=[
                                    {"name": "Country", "id": "country"},
                                    {"name": "Region", "id": "region"},
                                    {"name": "TB Prevalence (per 100K)", "id": "prevalence_per_100k"},
                                    {"name": "TB Mortality (per 100K)", "id": "mortality_per_100k"},
                                    {"name": "TB Incidence (per 100K)", "id": "incidence_per_100k"},
                                ],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px',
                                    'fontSize': '12px',
                                    'fontFamily': 'Arial'
                                },
                                style_header={
                                    'backgroundColor': '#005b82',
                                    'color': 'white',
                                    'fontWeight': 'bold'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    }
                                ],
                                page_size=15,
                                sort_action="native",
                                sort_mode="multi",
                                filter_action="native",
                            ),
                        ], className="col-md-12 mb-4"),
                        
                        # Comparative analysis
                        html.Div([
                            html.H5("Country Comparison", className="text-secondary mb-3"),
                            dcc.Dropdown(
                                id='comparison-countries',
                                options=[{'label': country, 'value': country} for country in countries],
                                value=['Afghanistan', 'Brazil', 'China', 'India', 'South Africa'],
                                multi=True,
                                style={'width': '100%', 'marginBottom': '20px'}
                            ),
                            dcc.Graph(id='comparison-chart'),
                        ], className="col-md-12"),
                    ], className="row")
                ]),
                
                # Analysis & Insights Tab
                dcc.Tab(label='Analysis & Insights', children=[
                    html.Div([
                        html.Div([
                            html.H5("Regional TB Burden Analysis", className="text-secondary mb-3"),
                            dcc.Graph(id='region-bar-chart'),
                        ], className="col-md-6 mb-4"),
                        
                        html.Div([
                            html.H5("TB Metrics Distribution", className="text-secondary mb-3"),
                            dcc.Graph(id='region-box-plot'),
                        ], className="col-md-6 mb-4"),
                        
                        html.Div([
                            html.H5("Year-over-Year TB Changes", className="text-secondary mb-3"),
                            dcc.Graph(id='yoy-changes'),
                        ], className="col-md-12 mb-4"),
                        
                        html.Div([
                            html.H4("Understanding the Data", className="mb-3 text-secondary"),
                            html.P([
                                html.Strong("Prevalence: "),
                                "The total number of people who have TB at a given point in time per 100,000 population."
                            ]),
                            html.P([
                                html.Strong("Incidence: "),
                                "The number of new TB cases per 100,000 population per year."
                            ]),
                            html.P([
                                html.Strong("Mortality: "),
                                "The number of deaths caused by TB per 100,000 population per year."
                            ]),
                            html.P([
                                "Data shown includes 95% confidence intervals where available, indicated by the shaded areas around trend lines."
                            ]),
                            html.Hr(),
                            html.H4("About Tuberculosis (TB)", className="mb-3 text-secondary"),
                            html.P("Tuberculosis (TB) is an infectious disease caused by the bacterium Mycobacterium tuberculosis that primarily affects the lungs."),
                            
                            html.H5("Key Facts", className="mt-4"),
                            html.Ul([
                                html.Li("TB is one of the top 10 causes of death worldwide and the leading cause from a single infectious agent."),
                                html.Li("In 2023, an estimated 10 million people fell ill with TB worldwide."),
                                html.Li("TB is present in all countries and age groups, but is curable and preventable."),
                                html.Li("Multidrug-resistant TB (MDR-TB) remains a public health crisis with an estimated 500,000 new cases with resistance to rifampicin, the most effective first-line drug."),
                                html.Li("Ending the TB epidemic by 2030 is among the health targets of the United Nations Sustainable Development Goals (SDGs).")
                            ]),
                            
                            html.H5("Transmission", className="mt-4"),
                            html.P("TB spreads from person to person through the air when people with lung TB cough, sneeze, or spit. A person needs to inhale only a few of these germs to become infected."),
                            
                            html.H5("Risk Factors", className="mt-4"),
                            html.P("People infected with TB bacteria have a 5-10% lifetime risk of falling ill with TB. Those with compromised immune systems, such as people living with HIV, malnutrition, or diabetes, or people who use tobacco, have a higher risk of falling ill."),
                            
                            html.Div([
                                html.A("Source: World Health Organization", 
                                       href="https://www.who.int/health-topics/tuberculosis", 
                                       target="_blank",
                                       className="text-secondary")
                            ], className="mt-4 text-right")
                        ], className="col-md-12 p-4 bg-light rounded shadow-sm")
                    ], className="row")
                ]),
                
            ], className="mb-4"),
            
            # Footer with WHO region information
            html.Div([
                html.Hr(),
                html.H5("WHO Region Definitions", className="text-secondary"),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Strong("AFR"), " - African Region (Sub-Saharan Africa)",
                        ], className="col-md-4 mb-2"),
                        html.Div([
                            html.Strong("AMR"), " - Region of the Americas (North, Central, and South America)",
                        ], className="col-md-4 mb-2"),
                        html.Div([
                            html.Strong("EMR"), " - Eastern Mediterranean Region (Middle East, North Africa, parts of Asia)",
                        ], className="col-md-4 mb-2"),
                        html.Div([
                            html.Strong("EUR"), " - European Region (Europe and some Central Asian nations)",
                        ], className="col-md-4 mb-2"),
                        html.Div([
                            html.Strong("SEAR"), " - South-East Asia Region (South and South-East Asia)",
                        ], className="col-md-4 mb-2"),
                        html.Div([
                            html.Strong("WPR"), " - Western Pacific Region (East Asia and Pacific Islands)",
                        ], className="col-md-4 mb-2"),
                    ], className="row"),
                ]),
                html.Hr(),
                html.Div([
                    html.P("Data Source: World Health Organization (WHO) TB Burden Dataset",
                        className="text-muted"),
                    html.P("Dashboard created with Dash, Plotly, and Python",
                        className="text-muted"),
                ], className="text-center")
            ], className="mt-4"),
            
        ], style={'flex': '1'}, className="main-content")  # flex: 1 to take remaining space
    ], style={'display': 'flex', 'flexDirection': 'row'}, className="flex-container"),  # Flexbox container
    
], className="container-fluid px-4 py-4 bg-light")

# Callback for dynamic title
@callback(
    Output('key-indicators-title', 'children'),
    [Input('country-filter', 'value')]
)
def update_key_indicators_title(country):
    if not country or country == 'Global':
        return "Global TB Indicators"
    else:
        return f"TB Indicators - {country}"

# Callback for key metrics
@callback(
    Output('key-metrics', 'children'),
    [Input('country-filter', 'value'),
     Input('year-slider', 'value')]
)
def update_key_metrics(country, years_range):
    start_year, end_year = int(years_range[0]), int(years_range[1])
    
    filtered_data = get_filtered_data(start_year, end_year)
    
    # For global stats
    if not country or country == 'Global':
        latest_year_data = filtered_data[filtered_data['year'] == end_year]
        prev_year_data = filtered_data[filtered_data['year'] == end_year-1] if end_year > start_year else None
        
        # Calculate global averages
        avg_prevalence = latest_year_data['prevalence_per_100k'].mean()
        avg_mortality = latest_year_data['mortality_per_100k'].mean()
        avg_incidence = latest_year_data['incidence_per_100k'].mean()
        
        # Calculate year-over-year changes
        if prev_year_data is not None:
            prev_avg_prevalence = prev_year_data['prevalence_per_100k'].mean()
            prev_avg_mortality = prev_year_data['mortality_per_100k'].mean()
            prev_avg_incidence = prev_year_data['incidence_per_100k'].mean()
            
            prevalence_change = ((avg_prevalence - prev_avg_prevalence) / prev_avg_prevalence * 100) if prev_avg_prevalence > 0 else 0
            mortality_change = ((avg_mortality - prev_avg_mortality) / prev_avg_mortality * 100) if prev_avg_mortality > 0 else 0
            incidence_change = ((avg_incidence - prev_avg_incidence) / prev_avg_incidence * 100) if prev_avg_incidence > 0 else 0
        else:
            prevalence_change = mortality_change = incidence_change = 0
    else:
        # For specific country
        country_data = filtered_data[filtered_data['country'] == country]
        latest_country_data = country_data[country_data['year'] == end_year]
        prev_year_country_data = country_data[country_data['year'] == end_year-1] if end_year > start_year else None
        
        if latest_country_data.empty:
            return [html.Div("No data available for the selected country and year range.", className="col-12")]
        
        avg_prevalence = latest_country_data['prevalence_per_100k'].iloc[0] if not latest_country_data.empty else 0
        avg_mortality = latest_country_data['mortality_per_100k'].iloc[0] if not latest_country_data.empty else 0
        avg_incidence = latest_country_data['incidence_per_100k'].iloc[0] if not latest_country_data.empty else 0
        
        # Calculate year-over-year changes
        if prev_year_country_data is not None and not prev_year_country_data.empty:
            prev_avg_prevalence = prev_year_country_data['prevalence_per_100k'].iloc[0]
            prev_avg_mortality = prev_year_country_data['mortality_per_100k'].iloc[0]
            prev_avg_incidence = prev_year_country_data['incidence_per_100k'].iloc[0]
            
            prevalence_change = ((avg_prevalence - prev_avg_prevalence) / prev_avg_prevalence * 100) if prev_avg_prevalence > 0 else 0
            mortality_change = ((avg_mortality - prev_avg_mortality) / prev_avg_mortality * 100) if prev_avg_mortality > 0 else 0
            incidence_change = ((avg_incidence - prev_avg_incidence) / prev_avg_incidence * 100) if prev_avg_incidence > 0 else 0
        else:
            prevalence_change = mortality_change = incidence_change = 0
    
    # Create metric cards
    metrics = [
        html.Div([
            html.Div([
                html.H2(f"{avg_prevalence:.1f}", className="mb-0 font-weight-bold text-primary"),
                html.Div([
                    html.Span(f"{prevalence_change:.1f}% ", className="mr-1"),
                    html.I(className="fas fa-arrow-down text-success" if prevalence_change < 0 else "fas fa-arrow-up text-danger")
                ]) if prevalence_change != 0 else html.Span("No change")
            ], className="d-flex justify-content-between"),
            html.P("Prevalence per 100,000", className="text-muted mb-0")
        ], className="col-md-4 mb-3"),
        
        html.Div([
            html.Div([
                html.H2(f"{avg_mortality:.1f}", className="mb-0 font-weight-bold text-danger"),
                html.Div([
                    html.Span(f"{mortality_change:.1f}% ", className="mr-1"),
                    html.I(className="fas fa-arrow-down text-success" if mortality_change < 0 else "fas fa-arrow-up text-danger")
                ]) if mortality_change != 0 else html.Span("No change")
            ], className="d-flex justify-content-between"),
            html.P("Mortality per 100,000", className="text-muted mb-0")
        ], className="col-md-4 mb-3"),
        
        html.Div([
            html.Div([
                html.H2(f"{avg_incidence:.1f}", className="mb-0 font-weight-bold text-warning"),
                html.Div([
                    html.Span(f"{incidence_change:.1f}% ", className="mr-1"),
                    html.I(className="fas fa-arrow-down text-success" if incidence_change < 0 else "fas fa-arrow-up text-danger")
                ]) if incidence_change != 0 else html.Span("No change")
            ], className="d-flex justify-content-between"),
            html.P("Incidence per 100,000", className="text-muted mb-0")
        ], className="col-md-4 mb-3"),
    ]
    
    return metrics

# Callback for choropleth map
@callback(
    Output('choropleth-map', 'figure'),
    [Input('metric-selector', 'value'),
     Input('region-filter', 'value'),
     Input('year-slider', 'value')]
)
def update_map(selected_metric, selected_regions, selected_years):
    start_year, end_year = int(selected_years[0]), int(selected_years[1])
    
    # Get filtered data using cached function
    filtered_data = get_filtered_data(start_year, end_year, selected_regions)
    
    # Group by country and calculate the mean for the selected metric
    agg_data = filtered_data.groupby('country')[selected_metric].mean().reset_index()
    
    # Create colorscale based on the selected metric
    if selected_metric == 'prevalence_per_100k':
        colorscale = 'YlOrBr'
        base_title = f'TB Prevalence per 100,000 population ({start_year}-{end_year})'
    elif selected_metric == 'mortality_per_100k':
        colorscale = 'Reds'
        base_title = f'TB Mortality per 100,000 population ({start_year}-{end_year})'
    else:
        colorscale = 'YlOrRd'
        base_title = f'TB Incidence per 100,000 population ({start_year}-{end_year})'
    
    # Add region information to title if specific regions are selected
    if selected_regions and len(selected_regions) > 0:
        if len(selected_regions) == 1:
            title = f'{base_title} - {selected_regions[0]}'
        elif len(selected_regions) <= 3:
            regions_str = ', '.join(selected_regions)
            title = f'{base_title} - {regions_str}'
        else:
            title = f'{base_title} - {len(selected_regions)} Selected Regions'
    else:
        title = base_title
    
    # Create the choropleth map
    fig = px.choropleth(
        agg_data, 
        locations="country", 
        locationmode="country names",
        color=selected_metric,
        hover_name="country",
        hover_data={selected_metric: True},
        color_continuous_scale=colorscale,
        projection="natural earth",
        title=title
    )
    
    # Update layout
    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="white",
        showocean=True,
        oceancolor="lightblue",
        showlakes=True,
        lakecolor="lightblue",
        showrivers=True,
        rivercolor="lightblue"
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(
            title=selected_metric.replace('_', ' ').capitalize(),
            ticksuffix=' per 100K',
            len=0.8
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='#333')
        )
    )
    
    return fig

# Callback for trend chart
@callback(
    Output('trend-chart', 'figure'),
    [Input('country-filter', 'value'),
     Input('metric-selector', 'value')]
)
def update_trend_chart(selected_country, selected_metric):
    # If no country selected or "Global", show global trend
    if not selected_country or selected_country == 'Global':
        # Group by year and calculate mean for all countries
        trend_data = tb_data.groupby('year')[
            [selected_metric, f"{selected_metric}_low", f"{selected_metric}_high"]
        ].mean().reset_index()
        title = f'Global TB {selected_metric.split("_")[0].capitalize()} Trend'
    else:
        # Filter data for selected country
        country_data = tb_data[tb_data['country'] == selected_country]
        if country_data.empty:
            # Return empty figure if no data
            return go.Figure()
        
        trend_data = country_data
        title = f'TB {selected_metric.split("_")[0].capitalize()} Trend for {selected_country}'
    
    # Create figure with confidence interval
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=trend_data['year'],
        y=trend_data[selected_metric],
        mode='lines+markers',
        name=selected_metric.replace('_per_100k', '').capitalize(),
        line=dict(color='#005b82', width=2),
        marker=dict(size=6)
    ))
    
    # Add confidence interval
    if f"{selected_metric}_low" in trend_data.columns and f"{selected_metric}_high" in trend_data.columns:
        fig.add_trace(go.Scatter(
            x=trend_data['year'],
            y=trend_data[f"{selected_metric}_high"],
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['year'],
            y=trend_data[f"{selected_metric}_low"],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(0, 91, 130, 0.2)',
            name='95% Confidence Interval'
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Year',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=f"{selected_metric.replace('_', ' ').capitalize()}",
            gridcolor='lightgray'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5
        ),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=60),
        hovermode='x unified'
    )
    
    return fig

# Callback for region distribution
@callback(
    Output('region-distribution', 'figure'),
    [Input('year-slider', 'value'),
     Input('metric-selector', 'value')]
)
def update_region_distribution(selected_years, selected_metric):
    start_year, end_year = int(selected_years[0]), int(selected_years[1])
    
    # Get filtered data using cached function
    filtered_data = get_filtered_data(start_year, end_year)
    
    # Group by region and calculate the mean for the selected metric
    agg_data = filtered_data.groupby('region')[selected_metric].mean().reset_index()
    
    # Sort by value
    agg_data = agg_data.sort_values(by=selected_metric, ascending=True)
    
    # Create the bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=agg_data['region'],
        x=agg_data[selected_metric],
        orientation='h',
        marker=dict(
            color='#005b82',
            line=dict(color='#003a52', width=1)
        )
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'TB {selected_metric.split("_")[0].capitalize()} by Region',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=f"{selected_metric.replace('_', ' ').capitalize()}",
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='WHO Region',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=30),
    )
    
    return fig

# Callback for data table
@callback(
    Output('data-table', 'data'),
    Output('data-table-title', 'children'),
    [Input('region-filter', 'value'),
     Input('year-slider', 'value')]
)
def update_table(selected_regions, selected_years):
    start_year, end_year = int(selected_years[0]), int(selected_years[1])
    
    # Get filtered data using cached function
    filtered_data = get_filtered_data(start_year, end_year, selected_regions)
    
    # Group by country and calculate means
    agg_data = filtered_data.groupby(['country', 'region']).agg({
        'prevalence_per_100k': 'mean',
        'mortality_per_100k': 'mean',
        'incidence_per_100k': 'mean'
    }).reset_index()
    
    # Round values to 1 decimal place
    agg_data['prevalence_per_100k'] = agg_data['prevalence_per_100k'].round(1)
    agg_data['mortality_per_100k'] = agg_data['mortality_per_100k'].round(1)
    agg_data['incidence_per_100k'] = agg_data['incidence_per_100k'].round(1)
    
    # Create dynamic title based on selected regions
    if selected_regions and len(selected_regions) > 0:
        if len(selected_regions) == 1:
            title = f'Data Table - {selected_regions[0]}'
        elif len(selected_regions) <= 3:
            regions_str = ', '.join(selected_regions)
            title = f'Data Table - {regions_str}'
        else:
            title = f'Data Table - {len(selected_regions)} Selected Regions'
    else:
        title = 'Data Table - All Regions'
    
    return agg_data.to_dict('records'), title

# Callback for comparison chart
@callback(
    Output('comparison-chart', 'figure'),
    [Input('comparison-countries', 'value'),
     Input('metric-selector', 'value')]
)
def update_comparison_chart(selected_countries, selected_metric):
    if not selected_countries:
        return go.Figure()
    
    # Filter data for selected countries
    filtered_data = tb_data[tb_data['country'].isin(selected_countries)]
    
    # Create figure
    fig = go.Figure()
    
    # Add a line for each country
    for country in selected_countries:
        country_data = filtered_data[filtered_data['country'] == country]
        
        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data[selected_metric],
            mode='lines+markers',
            name=country,
            marker=dict(size=6)
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Country Comparison: {selected_metric.replace("_", " ").capitalize()}',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Year',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=f"{selected_metric.replace('_', ' ').capitalize()}",
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=60),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5
        ),
        hovermode='closest'
    )
    
    return fig

# Callback for region bar chart
@callback(
    Output('region-bar-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('metric-selector', 'value')]
)
def update_region_bar_chart(selected_years, selected_metric):
    start_year, end_year = int(selected_years[0]), int(selected_years[1])
    
    # Get filtered data using cached function
    filtered_data = get_filtered_data(start_year, end_year)
    
    # Group by region and calculate the mean for all metrics
    agg_data = filtered_data.groupby('region').agg({
        'prevalence_per_100k': 'mean',
        'mortality_per_100k': 'mean',
        'incidence_per_100k': 'mean'
    }).reset_index()
    
    # Sort by the selected metric
    agg_data = agg_data.sort_values(by=selected_metric, ascending=False)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=agg_data['region'],
        y=agg_data['prevalence_per_100k'],
        name='Prevalence',
        marker_color='#FFA15A'
    ))
    
    fig.add_trace(go.Bar(
        x=agg_data['region'],
        y=agg_data['mortality_per_100k'],
        name='Mortality',
        marker_color='#FF6692'
    ))
    
    fig.add_trace(go.Bar(
        x=agg_data['region'],
        y=agg_data['incidence_per_100k'],
        name='Incidence',
        marker_color='#B6E880'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'TB Burden by WHO Region ({start_year}-{end_year})',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='WHO Region',
            tickangle=-45,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Rate per 100,000 population',
            gridcolor='lightgray'
        ),
        barmode='group',
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=120),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.25,
            xanchor='center',
            x=0.5
        )
    )
    
    return fig

# Callback for region box plot
@callback(
    Output('region-box-plot', 'figure'),
    [Input('year-slider', 'value'),
     Input('metric-selector', 'value')]
)
def update_region_box_plot(selected_years, selected_metric):
    start_year, end_year = int(selected_years[0]), int(selected_years[1])
    
    # Get filtered data using cached function
    filtered_data = get_filtered_data(start_year, end_year)
    
    # Create the box plot
    fig = px.box(
        filtered_data,
        x='region',
        y=selected_metric,
        color='region',
        title=f'Distribution of {selected_metric.replace("_", " ").capitalize()} by Region ({start_year}-{end_year})'
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            title='WHO Region',
            tickangle=-45,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=f"{selected_metric.replace('_', ' ').capitalize()}",
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=80),
        showlegend=False
    )
    
    return fig

# Callback for year-over-year changes
@callback(
    Output('yoy-changes', 'figure'),
    [Input('region-filter', 'value'),
     Input('metric-selector', 'value')]
)
def update_yoy_changes(selected_regions, selected_metric):
    # Get all years of data but filter by region if selected
    filtered_data = get_filtered_data(min(years), max(years), selected_regions)
    
    # Group by year and calculate global means
    yearly_data = filtered_data.groupby('year')[selected_metric].mean().reset_index()
    
    # Calculate year-over-year changes
    yearly_data['prev_value'] = yearly_data[selected_metric].shift(1)
    yearly_data['yoy_change'] = ((yearly_data[selected_metric] - yearly_data['prev_value']) / yearly_data['prev_value'] * 100)
    
    # Remove first row with NaN
    yearly_data = yearly_data.dropna()
    
    # Create the bar chart
    fig = go.Figure()
    
    # Add bars with color based on positive/negative change
    for i, row in yearly_data.iterrows():
        color = '#00AA00' if row['yoy_change'] <= 0 else '#AA0000'
        fig.add_trace(go.Bar(
            x=[row['year']],
            y=[row['yoy_change']],
            marker_color=color,
            showlegend=False
        ))
    
    # Add reference line at y=0
    fig.add_shape(
        type="line",
        x0=yearly_data['year'].min(),
        y0=0,
        x1=yearly_data['year'].max(),
        y1=0,
        line=dict(color="black", width=1, dash="dot")
    )
    
    # Create dynamic title based on selected regions
    base_title = f'Year-over-Year % Change in {selected_metric.replace("_", " ").capitalize()}'
    if selected_regions and len(selected_regions) > 0:
        if len(selected_regions) == 1:
            title = f'{base_title} - {selected_regions[0]}'
        elif len(selected_regions) <= 3:
            regions_str = ', '.join(selected_regions)
            title = f'{base_title} - {regions_str}'
        else:
            title = f'{base_title} - {len(selected_regions)} Selected Regions'
    else:
        title = base_title
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Year',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Percent Change (%)',
            gridcolor='lightgray',
            ticksuffix='%'
        ),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=30),
        hovermode='x unified'
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8050)