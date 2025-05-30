# Tuberculosis (TB) Global Visualization Dashboard

This dashboard visualizes global Tuberculosis (TB) data using interactive maps, charts, and tables. The dashboard is built using Dash, Plotly, and Folium, providing a comprehensive view of TB burden across the world.

## About Tuberculosis

Tuberculosis (TB) is an infectious disease caused by the bacterium *Mycobacterium tuberculosis*. It typically affects the lungs but can also affect other parts of the body. TB spreads through the air when people with TB cough, sneeze, or spit. Despite being preventable and curable, TB remains one of the top infectious disease killers worldwide.

## Dashboard Features

### 1. Dash Interactive Dashboard (`tb_dashboard.py`)

The main dashboard provides several interactive visualizations with optimized performance:

- **World Map**: Choropleth map showing TB prevalence, incidence, or mortality by country
- **Data Tables**: Sortable and filterable tables showing TB metrics by country
- **Trend Analysis**: Time series charts showing how TB metrics change over time for selected countries
- **Regional Analysis**: Bar charts and box plots comparing TB burden across different regions
- **Interactive Map**: Folium-based interactive map for detailed exploration

### 2. Folium Maps (`tb_folium_visualization.py`)

The Folium visualization script creates two HTML maps:

- **Global TB Map**: Shows TB prevalence across the world with interactive tooltips
- **Regional Time Series Map**: Focuses on specific regions with a year selector

## How to Use

### Running the Dashboard

1. Make sure you have the required Python packages installed:
   ```
   pip install dash plotly pandas folium flask-caching
   ```

2. Run the dashboard:
   ```
   python tb_dashboard.py
   ```

3. Open a web browser and go to `http://127.0.0.1:8050/` to view the dashboard

### Interactive Features

- **Year Slider**: Select different years to see how TB metrics changed over time
- **Region Filter**: Filter data by specific regions
- **Metric Selector**: Choose between prevalence, mortality, and incidence
- **Country Selector**: Select specific countries for trend analysis
- **Interactive Maps**: Hover over countries to see detailed information
- **Mobile Responsiveness**: Optimized for viewing on desktop and mobile devices
- **Performance Optimization**: Data caching to improve performance for large data queries
- **Educational Content**: Detailed information about TB epidemiology and public health impact

### Viewing Folium Maps

1. Run the Folium visualization script:
   ```
   python tb_folium_visualization.py
   ```

2. Open the generated HTML files in a web browser:
   - `tb_global_map.html`: Global TB prevalence map
   - `tb_region_map.html`: Region-specific map with time selector

## Data Source

The data used in this dashboard comes from the World Health Organization (WHO) TB burden dataset, which provides estimates of TB burden by country and year.

## Files Description

- `tb_dashboard.py`: Main Dash application with interactive dashboard
- `tb_folium_visualization.py`: Generates standalone Folium maps
- `1-TB_Burden_Country.csv`: The TB dataset
- `world-countries.json`: GeoJSON file with country boundaries
- `tb_global_map.html`: Generated HTML file with global TB map
- `tb_region_map.html`: Generated HTML file with region-focused TB map

## Understanding TB Metrics

- **Prevalence**: Number of TB cases per 100,000 population at a given point in time
- **Incidence**: Number of new TB cases per 100,000 population per year
- **Mortality**: Number of deaths due to TB per 100,000 population per year

These metrics help understand the TB burden in different countries and regions, identify high-risk areas, and track progress in TB prevention and control efforts.
