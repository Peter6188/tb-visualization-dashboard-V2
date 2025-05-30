import pandas as pd
import folium
import json
from folium.plugins import HeatMap, MarkerCluster

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
    'Estimated mortality of TB cases (all forms, excluding HIV) per 100 000 population': 'mortality_per_100k',
    'Estimated incidence (all forms) per 100 000 population': 'incidence_per_100k'
}, inplace=True)

# Get the latest available year in the dataset
latest_year = tb_data['year'].max()

# Filter data for the latest year
latest_data = tb_data[tb_data['year'] == latest_year]

# Create a base map
map_center = [20, 0]  # Center of the world
tb_map = folium.Map(location=map_center, zoom_start=2, tiles="CartoDB positron")

# Add a title to the map
title_html = '''
             <h3 align="center" style="font-size:16px"><b>Tuberculosis (TB) Global Prevalence - {}</b></h3>
             '''.format(latest_year)

tb_map.get_root().html.add_child(folium.Element(title_html))

# Create a choropleth layer
choropleth = folium.Choropleth(
    geo_data=geo_data,
    name='TB Prevalence',
    data=latest_data,
    columns=['country', 'prevalence_per_100k'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='TB Prevalence per 100,000 population',
    highlight=True
).add_to(tb_map)

# Add tooltip to the choropleth
choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(
        fields=['name'],
        aliases=['Country'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    )
)

# Create a marker cluster
marker_cluster = MarkerCluster().add_to(tb_map)

# Add markers for countries with high TB prevalence (top 20)
top_countries = latest_data.sort_values(by='prevalence_per_100k', ascending=False).head(20)

# We need to get approximate coordinates for these countries (this is a simplification)
# In a real application, you would use a geocoding service or a proper dataset with coordinates
country_coords = {
    'Afghanistan': [33.93911, 67.709953],
    'Angola': [-11.202692, 17.873887],
    'Bangladesh': [23.684994, 90.356331],
    'Brazil': [-14.235004, -51.92528],
    'China': [35.86166, 104.195397],
    'Democratic Republic of the Congo': [-4.038333, 21.758664],
    'Ethiopia': [9.145, 40.489673],
    'India': [20.593684, 78.96288],
    'Indonesia': [-0.789275, 113.921327],
    'Kenya': [-0.023559, 37.906193],
    'Mozambique': [-18.665695, 35.529562],
    'Myanmar': [21.913965, 95.956223],
    'Nigeria': [9.081999, 8.675277],
    'Pakistan': [30.375321, 69.345116],
    'Philippines': [12.879721, 121.774017],
    'Russian Federation': [61.52401, 105.318756],
    'South Africa': [-30.559482, 22.937506],
    'Thailand': [15.870032, 100.992541],
    'United Republic of Tanzania': [-6.369028, 34.888822],
    'Vietnam': [14.058324, 108.277199],
    # Add more countries if needed
}

for _, row in top_countries.iterrows():
    country = row['country']
    if country in country_coords:
        folium.Marker(
            location=country_coords[country],
            popup=folium.Popup(f"""
                <b>Country:</b> {row['country']}<br>
                <b>Region:</b> {row['region']}<br>
                <b>TB Prevalence:</b> {row['prevalence_per_100k']:.1f} per 100,000<br>
                <b>TB Mortality:</b> {row['mortality_per_100k']:.1f} per 100,000<br>
                <b>TB Incidence:</b> {row['incidence_per_100k']:.1f} per 100,000<br>
            """, max_width=300),
            tooltip=f"{country}: {row['prevalence_per_100k']:.1f} per 100,000",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(marker_cluster)

# Add a layer control panel
folium.LayerControl().add_to(tb_map)

# Add a legend for WHO region abbreviations
region_info_html = """
<div style='position: fixed; 
            bottom: 50px; left: 10px; 
            z-index: 9999; 
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial;
            font-size: 12px;
            max-width: 300px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);'>
    <h4>WHO Region Abbreviations:</h4>
    <ul style="padding-left: 20px; margin-bottom: 0;">
        <li><strong>AFR</strong> - African Region</li>
        <li><strong>AMR</strong> - Region of the Americas</li>
        <li><strong>EMR</strong> - Eastern Mediterranean Region</li>
        <li><strong>EUR</strong> - European Region</li>
        <li><strong>SEAR</strong> - South-East Asia Region</li>
        <li><strong>WPR</strong> - Western Pacific Region</li>
    </ul>
</div>
"""
tb_map.get_root().html.add_child(folium.Element(region_info_html))

# Save the map to an HTML file
tb_map.save('tb_global_map.html')

# Create a time series map for a specific region (e.g., AFR)
region_data = tb_data[tb_data['region'] == 'AFR']
years = sorted(region_data['year'].unique())

# Create a base map for the region
region_map = folium.Map(location=[0, 20], zoom_start=3, tiles="CartoDB positron")

# Add year selector
year_selector_html = """
<div style='position: fixed; 
            top: 10px; right: 10px; 
            z-index: 9999; 
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);'>
    <h4>Select Year:</h4>
    <select id="year-selector" onchange="updateYear(this.value)">
"""

for year in years:
    year_selector_html += f'<option value="{year}">{year}</option>'

year_selector_html += """
    </select>
</div>

<script>
    var layers = {};
"""

for year in years:
    year_data = region_data[region_data['year'] == year]
    year_selector_html += f'layers["{year}"] = L.layerGroup();'

year_selector_html += """
    function updateYear(year) {
        for (var y in layers) {
            map.removeLayer(layers[y]);
        }
        map.addLayer(layers[year]);
    }
    
    updateYear(\"""" + str(years[-1]) + """\");
</script>
"""

region_map.get_root().html.add_child(folium.Element(year_selector_html))

# Add the WHO region information to the regional map too
region_info_html = """
<div style='position: fixed; 
            bottom: 50px; left: 10px; 
            z-index: 9999; 
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial;
            font-size: 12px;
            max-width: 300px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);'>
    <h4>WHO Region Abbreviations:</h4>
    <ul style="padding-left: 20px; margin-bottom: 0;">
        <li><strong>AFR</strong> - African Region (Sub-Saharan Africa)</li>
        <li><strong>AMR</strong> - Region of the Americas (North, Central, and South America)</li>
        <li><strong>EMR</strong> - Eastern Mediterranean Region (Middle East, North Africa, parts of Asia)</li>
        <li><strong>EUR</strong> - European Region (Europe and some Central Asian nations)</li>
        <li><strong>SEAR</strong> - South-East Asia Region (South and South-East Asia)</li>
        <li><strong>WPR</strong> - Western Pacific Region (East Asia and Pacific Islands)</li>
    </ul>
</div>
"""
region_map.get_root().html.add_child(folium.Element(region_info_html))

# Save the region map to an HTML file
region_map.save('tb_region_map.html')

print("Maps created successfully! Open tb_global_map.html and tb_region_map.html in your browser to view them.")
