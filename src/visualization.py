import folium
from folium.plugins import HeatMap
import pandas as pd
import geopandas as gpd
from shapely import wkt


def plot_quality_streets(graph, quality_gdf, filename: str) -> folium.Map:

    if isinstance(quality_gdf, str) and quality_gdf.endswith('.csv'):
        df = pd.read_csv(quality_gdf)
        if 'geometry' in df.columns and isinstance(df['geometry'].iloc[0], str):
            df['geometry'] = df['geometry'].apply(wkt.loads)
        quality_gdf = gpd.GeoDataFrame(
            df, geometry='geometry', crs="EPSG:4326")
    elif isinstance(quality_gdf, pd.DataFrame) and not isinstance(quality_gdf, gpd.GeoDataFrame):
        if 'geometry' in quality_gdf.columns:
            if isinstance(quality_gdf['geometry'].iloc[0], str):
                quality_gdf['geometry'] = quality_gdf['geometry'].apply(
                    wkt.loads)
            quality_gdf = gpd.GeoDataFrame(
                quality_gdf, geometry='geometry', crs="EPSG:4326")

    center = [35.6895, 139.6917]

    m = folium.Map(
        location=center,
        zoom_start=14,
        tiles='CartoDB dark_matter',
        control_scale=True
    )

    if graph is not None:
        base_layer = folium.FeatureGroup(name="All Streets")
        for u, v, data in graph.edges(data=True):
            if 'geometry' in data:
                try:
                    coords = [(lat, lon)
                              for lon, lat in data['geometry'].coords]
                    folium.PolyLine(coords, color='#404040',
                                    weight=2, opacity=0.6).add_to(base_layer)
                except:
                    continue
        base_layer.add_to(m)

    score_col = next(
        (c for c in quality_gdf.columns if 'score' in c.lower()), None)
    if score_col is None:
        quality_gdf['score'] = 0.5
        score_col = 'score'

    streets_layer = folium.FeatureGroup(name="Quality Streets")

    attribute_descriptions = {
        'u': 'Start Node ID',
        'v': 'End Node ID',
        'key': 'Edge Key',
        'osmid': 'OpenStreetMap ID',
        'highway': 'Road Type',
        'maxspeed': 'Speed Limit (km/h)',
        'name': 'Street Name',
        'oneway': 'One-way Street',
        'ref': 'Reference Number',
        'reversed': 'Direction Reversed',
        'length': 'Street Length (m)',
        'lanes': 'Number of Lanes',
        'access': 'Access Restrictions',
        'bridge': 'Bridge Structure',
        'tunnel': 'Tunnel Structure',
        'width': 'Street Width (m)',
        'est_width': 'Estimated Width (m)',
        'service': 'Service Type',
        'score': 'Quality Score'
    }

    for _, row in quality_gdf.iterrows():
        try:
            if not hasattr(row.geometry, 'coords'):
                continue

            score = 0.5
            try:
                score = max(0, min(1, float(row[score_col])))
            except:
                pass

            r = int(255 - (117 * score))
            g = int(209 - (209 * score))
            b = int(220 - (81 * score))
            color = f"#{r:02x}{g:02x}{b:02x}"

            coords = [(lat, lon) for lon, lat in row.geometry.coords]

            html = """
            <div style="font-family: Arial, sans-serif; color: #e0e0e0;">
                <h3 style="color: #FFD1DC; margin: 0 0 8px 0; text-align: center; border-bottom: 1px solid #444; padding-bottom: 6px;">
                    Street Details
                </h3>
                <table style="width:100%; border-collapse: collapse;">
            """

            for key, value in row.drop('geometry').items():
                if isinstance(value, float):
                    value = f"{value:.2f}" if key != score_col else f"{value:.2f}"
                elif value is None or (isinstance(value, str) and value.lower() == 'nan'):
                    value = "N/A"

                label = attribute_descriptions.get(key, key.capitalize())

                html += f"""
                <tr style="border-bottom: 1px solid #333;">
                    <th style="text-align:left; padding:4px; color: #FFD1DC;">{label}</th>
                    <td style="padding:4px;">{value}</td>
                </tr>"""

            html += """
                </table>
            </div>
            """

            popup = folium.Popup(html, max_width=300)

            folium.PolyLine(
                coords,
                color=color,
                weight=8,
                opacity=0.3,
                interactive=False
            ).add_to(streets_layer)

            folium.PolyLine(
                coords,
                color=color,
                weight=4,
                opacity=0.9,
                tooltip=f"Score: {score:.2f} - Click for details",
                popup=popup,
                interactive=True
            ).add_to(streets_layer)

        except:
            continue

    streets_layer.add_to(m)

    # NOTE: that is ugly and temporary
    custom_html = """
    <style>
    /* Dark mode enhancements */
    body {
        background-color: #121212;
        color: #e0e0e0;
    }
    
    /* Force map to use dark theme with improved contrast */
    .leaflet-container {
        background-color: #121212 !important;
    }
    
    .leaflet-tile-pane {
        opacity: 1 !important;
        filter: contrast(1.15) brightness(1.1); /* Subtle contrast enhancement */
    }
    
    /* Improve visibility of map features */
    .leaflet-tile-loaded {
        filter: contrast(1.2);
    }
    
    /* Enhanced dark popup styling */
    .leaflet-popup-content-wrapper {
        background-color: #1a1a1a;
        color: #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(255, 209, 220, 0.3);
    }
    
    .leaflet-popup-tip {
        background-color: #1a1a1a;
    }
    
    /* Make popups slightly larger and more readable */
    .leaflet-popup-content {
        margin: 14px;
    }
    
    /* Title box styling */
    .title-box {
        position: fixed;
        top: 10px;
        left: 50px;
        width: 300px;
        background-color: rgba(12, 12, 12, 0.8);
        border-radius: 10px; 
        border: 2px solid #FFD1DC;
        padding: 10px;
        z-index: 900;
        box-shadow: 0 0 15px rgba(255, 209, 220, 0.4);
    }
    .title-text {
        color: #FFD1DC;
        font-family: Arial, sans-serif;
        text-align: center;
        margin: 0;
    }
    .subtitle-text {
        color: #e0e0e0;
        font-family: Arial, sans-serif;
        text-align: center;
        font-size: 12px;
        margin: 5px 0 0 0;
    }
    
    /* Legend styling */
    .legend-box {
        position: fixed;
        bottom: 30px;
        right: 10px;
        background-color: rgba(12, 12, 12, 0.8);
        border-radius: 10px; 
        border: 2px solid #FFD1DC;
        padding: 10px;
        z-index: 900;
        box-shadow: 0 0 15px rgba(255, 209, 220, 0.4);
    }
    .legend-title {
        color: #FFD1DC;
        font-family: Arial, sans-serif;
        text-align: center;
        margin: 0 0 8px 0;
        font-size: 16px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin: 4px 0;
    }
    .legend-color {
        width: 20px;
        height: 4px;
        margin-right: 8px;
    }
    .legend-label {
        color: #e0e0e0;
        font-family: Arial, sans-serif;
        font-size: 12px;
    }
    
    /* Make map container fill viewport */
    .folium-map {
        position: absolute;
        width: 100%;
        height: 100%;
        left: 0;
        top: 0;
    }
    </style>
    
    <!-- Title Panel -->
    <div class="title-box">
        <h2 class="title-text">Street Quality Analysis</h2>
        <p class="subtitle-text">Analyzing urban street connectivity and quality metrics</p>
        <p class="subtitle-text">Click on streets to view detailed information</p>
    </div>
    
    <!-- Legend Panel -->
    <div class="legend-box">
        <h3 class="legend-title">Quality Score</h3>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFD1DC;"></div>
            <span class="legend-label">Low (0.0) - Limited connectivity</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #D980B0;"></div>
            <span class="legend-label">Medium (0.5) - Average quality</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #8B008B;"></div>
            <span class="legend-label">High (1.0) - Optimal connectivity</span>
        </div>
    </div>
    """

    # Save map with custom HTML
    path = f"{filename}.html"
    try:
        html_content = m._repr_html_().replace(
            '</head>', f'{custom_html}</head>')
        with open(path, 'w') as f:
            f.write(html_content)
        print(f"Visualization saved to: {path}")
    except Exception as e:
        print(f"Error: Could not save visualization: {e}")

    return m
