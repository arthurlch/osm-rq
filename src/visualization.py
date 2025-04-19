import folium
import osmnx as ox


def plot_narrow(graph: ox.graph.Graph, narrow_gdf, filename: str) -> folium.Map:
    """
    plot an interactive map highlighting narrow streets
    === based in folium which is leaflet ===
    """
    center = narrow_gdf.geometry.unary_union.centroid.coords[0][::-1]
    m = folium.Map(location=center, zoom_start=14, tiles='cartodbpositron')

    # base streets in light gray
    edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)
    for _, row in edges.iterrows():
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        folium.PolyLine(coords, color='lightgray',
                        weight=1, opacity=0.5).add_to(m)

    # draw narrow streets colored by score (from extract)
    for _, row in narrow_gdf.iterrows():
        intensity = int(255 * row.score)
        color = f"#{intensity:02x}{255-intensity:02x}00"
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        folium.PolyLine(
            coords,
            color=color,
            weight=3,
            opacity=0.8,
            popup=f"{row.name} | {row.highway} | {row.score:.2f}"
        ).add_to(m)

    path = f"{filename}.html"
    m.save(path)
    print(f"Map saved: {path}")
    return m
