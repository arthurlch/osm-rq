import os
import networkx as nx
from pyrosm import OSM
import osmnx as ox


def load_pbf_network(source: str, network_type: str = 'drive') -> nx.MultiDiGraph:

    if not os.path.isfile(source):
        raise FileNotFoundError(f"PBF file not found: {source}")
    osm = OSM(source)
    nodes, edges = osm.get_network(network_type=network_type)
    return ox.graph_from_gdfs(nodes, edges, node_key='id')
