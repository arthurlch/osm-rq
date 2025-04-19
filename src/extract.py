import osmnx as ox
import pandas as pd
import geopandas as gpd
from .pbf_loader import load_pbf_network

ox.config(use_cache=True, log_console=True)


def load_network(source: str, network_type: str = 'drive') -> ox.graph.Graph:
    if source.lower().endswith('.pbf'):
        return load_pbf_network(source, network_type)
    return ox.graph_from_place(source, network_type=network_type)


def extract_edges(graph: ox.graph.Graph) -> gpd.GeoDataFrame:
    """
    convert a graph's edges into a GeoDataFrame with key attr
    """
    gdf = ox.graph_to_gdfs(graph, nodes=False, edges=True)
    records = []
    for u, v, key, data in graph.edges(keys=True, data=True):
      # main attrs
        records.append({
            'u': u, 'v': v, 'key': key,
            'name': data.get('name', 'Unnamed'),
            'highway': data.get('highway'),
            'lanes': data.get('lanes'),
            'width': data.get('width'),
            'maxspeed': data.get('maxspeed'),
            'service': data.get('service'),
            'geometry': data.get('geometry')
        })
    df = pd.DataFrame(records)
    if not df.empty:
        gdf = gdf.merge(df, on=['u', 'v', 'key'], how='left')
    return gdf


def flag_narrow_streets(edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    identify edges meeting narrow‑street criteria and assign a score 
    """
    df = edges.copy()
    # convert numeric fields
    for col in ['width', 'lanes', 'maxspeed']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # define criterias !
    crit = []
    crit.append(df['width'] < 6 if 'width' in df else pd.Series(
        False, index=df.index))
    crit.append(df['lanes'] == 1 if 'lanes' in df else pd.Series(
        False, index=df.index))
    crit.append(df['highway'].isin([
        'residential', 'living_street', 'service', 'track', 'path', 'footway'
    ]))
    if 'service' in df:
        crit.append(df['service'] == 'alley')
    crit.append(df['maxspeed'] < 30 if 'maxspeed' in df else pd.Series(
        False, index=df.index))

    mask = pd.concat(crit, axis=1).any(axis=1)
    narrow = df[mask].copy()
    met = pd.concat(crit, axis=1).sum(axis=1)
    narrow['score'] = met[mask] / len(crit)
    return narrow
