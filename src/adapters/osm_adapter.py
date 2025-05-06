from .base import adapter_registry
import osmnx as ox
import pandas as pd
import geopandas as gpd
import networkx as nx
from typing import Dict, Any, Optional, Union, List

from .base import StreetDataAdapter
from ..pbf_loader import load_pbf_network


class OSMAdapter(StreetDataAdapter):

    def __init__(self, config: Optional[Dict[str, Any]] = None):

        super().__init__(config)
        self.network_type = self.config.get('network_type', 'drive')
        self.simplify = self.config.get('simplify', True)
        self.retain_all = self.config.get('retain_all', False)

        ox.config(use_cache=True, log_console=True)

    def load_data(self, source: str) -> nx.MultiDiGraph:

        if source.lower().endswith('.pbf') or source.lower().endswith('.osm.pbf'):
            return load_pbf_network(
                source,
                network_type=self.network_type,
                simplify=self.simplify,
                retain_all=self.retain_all
            )
        elif source.lower().endswith('.osm'):
            return ox.graph_from_xml(
                source,
                network_type=self.network_type,
                simplify=self.simplify,
                retain_all=self.retain_all
            )
        else:
            return ox.graph_from_place(
                source,
                network_type=self.network_type,
                simplify=self.simplify,
                retain_all=self.retain_all
            )

    def extract_edges(self, graph: nx.MultiDiGraph) -> gpd.GeoDataFrame:

        gdf = ox.graph_to_gdfs(graph, nodes=False, edges=True)

        records = []
        for u, v, key, data in graph.edges(keys=True, data=True):
            records.append({
                'u': u,
                'v': v,
                'key': key,
                'name': data.get('name', 'Unnamed'),
                'highway': data.get('highway'),
                'lanes': data.get('lanes'),
                'width': data.get('width'),
                'maxspeed': data.get('maxspeed'),
                'service': data.get('service'),
                'oneway': data.get('oneway'),
                'access': data.get('access'),
                'bridge': data.get('bridge'),
                'tunnel': data.get('tunnel'),
                'length': data.get('length'),
                'geometry': data.get('geometry')
            })

        df = pd.DataFrame(records)
        if not df.empty:
            gdf = gdf.merge(df, on=['u', 'v', 'key'], how='left')

        return gdf

    def get_supported_formats(self) -> List[str]:

        return ['.osm', '.osm.pbf', '.pbf']


adapter_registry.register_adapter(OSMAdapter, 'osm')
