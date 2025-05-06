import pandas as pd
import geopandas as gpd
import networkx as nx
from typing import Optional, Dict, Any, Union

from .adapters import get_adapter


def load_network(source: str, network_type: str = 'drive',
                 adapter_type: Optional[str] = None,
                 adapter_config: Optional[Dict[str, Any]] = None) -> Union[Any, nx.MultiDiGraph]:
    """
    Load a street network from a source using the appropriate adapter  (see readme for adapter)
    """
    if adapter_config is None:
        adapter_config = {}
    if 'network_type' not in adapter_config:
        adapter_config['network_type'] = network_type

    adapter = get_adapter(source, adapter_type, adapter_config)
    return adapter.load_data(source)


def extract_edges(data: Any, adapter_type: Optional[str] = None,
                  adapter_config: Optional[Dict[str, Any]] = None) -> gpd.GeoDataFrame:
    if isinstance(data, gpd.GeoDataFrame):
        return data

    if adapter_type is None:
        if isinstance(data, nx.MultiDiGraph):
            adapter_type = 'osm'
        elif hasattr(data, 'crs'):
            adapter_type = 'shapefile'
        else:
            raise ValueError(
                "Could not determine adapter type for data. Please specify adapter_type.")

    adapter = get_adapter(adapter_type, adapter_type, adapter_config)
    return adapter.extract_edges(data)


def assess_street_quality(edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Identify edges meeting quality street criteria and assign a quality score
    """
    df = edges.copy()
    for col in ['width', 'lanes', 'maxspeed']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

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
    quality_streets = df[mask].copy()
    met = pd.concat(crit, axis=1).sum(axis=1)
    quality_streets['quality_score'] = met[mask] / len(crit)
    return quality_streets


def load_and_process(source: str, network_type: str = 'drive',
                     adapter_type: Optional[str] = None,
                     adapter_config: Optional[Dict[str, Any]] = None) -> Dict[str, gpd.GeoDataFrame]:
    """
    Complete pipeline to load, extract, and assess street quality in one steps
    """
    data = load_network(source, network_type, adapter_type, adapter_config)

    edges = extract_edges(data, adapter_type, adapter_config)

    quality_streets = assess_street_quality(edges)

    return {
        'edges': edges,
        'quality_streets': quality_streets
    }
