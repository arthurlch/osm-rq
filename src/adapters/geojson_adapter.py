from .base import adapter_registry
import geopandas as gpd
import pandas as pd
import os
import json
from typing import Dict, Any, Optional, List, Union
from shapely.geometry import LineString

from .base import StreetDataAdapter, FeatureMapper


class GeoJSONAdapter(StreetDataAdapter):
    """
    That is the adapter for GeoJSON (.geojson, .json) data containing street networks.

    Handles the mapping of various GeoJSON property schemas to the 
    standardized OSM-like format used by the street quality tools
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):

        super().__init__(config)

        default_mapping = {
            'roadType': 'highway',
            'road_type': 'highway',
            'type': 'highway',
            'streetType': 'highway',

            'width': 'width',
            'roadWidth': 'width',
            'road_width': 'width',
            'width_m': 'width',

            'lanes': 'lanes',
            'laneCount': 'lanes',
            'lane_count': 'lanes',
            'num_lanes': 'lanes',

            'speedLimit': 'maxspeed',
            'speed_limit': 'maxspeed',
            'maxSpeed': 'maxspeed',
            'max_speed': 'maxspeed',

            'name': 'name',
            'roadName': 'name',
            'road_name': 'name',
            'street_name': 'name',

            'oneway': 'oneway',
            'oneWay': 'oneway',
            'one_way': 'oneway',
            'isOneway': 'oneway',

            'service': 'service',
            'serviceType': 'service',
            'service_type': 'service',

            'length': 'length',
            'length_m': 'length',
            'roadLength': 'length',
        }

        user_mapping = self.config.get('feature_mapping', {})
        self.feature_mapping = {**default_mapping, **user_mapping}

        self.mapper = FeatureMapper(self.feature_mapping)

        self.crs = self.config.get('crs', 'EPSG:4326')
        self.geometry_key = self.config.get('geometry_key', 'geometry')
        self.properties_key = self.config.get('properties_key', 'properties')
        self.filter_property = self.config.get('filter_by', {})

    def load_data(self, source: str) -> Union[gpd.GeoDataFrame, Dict[str, Any]]:

        if not (source.lower().endswith('.geojson') or source.lower().endswith('.json')):
            if os.path.exists(f"{source}.geojson"):
                source = f"{source}.geojson"
            elif os.path.exists(f"{source}.json"):
                source = f"{source}.json"
            else:
                raise FileNotFoundError(
                    f"GeoJSON file not found: {source}, {source}.geojson, or {source}.json")

        if source.startswith(('http://', 'https://')):
            import requests
            response = requests.get(source)
            response.raise_for_status()
            geojson_data = response.json()

            try:
                gdf = gpd.GeoDataFrame.from_features(
                    geojson_data['features'], crs=self.crs)
                return gdf
            except (KeyError, TypeError):
                return geojson_data

        if not os.path.exists(source):
            raise FileNotFoundError(f"GeoJSON file not found: {source}")

        try:
            gdf = gpd.read_file(source)
            if gdf.crs is None:
                gdf.set_crs(self.crs, inplace=True)
            elif gdf.crs != self.crs:
                gdf = gdf.to_crs(self.crs)
            return gdf
        except Exception as e:
            print(f"Warning: Could not directly load with GeoPandas: {e}")

            with open(source, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)

            try:
                if 'features' in geojson_data:
                    gdf = gpd.GeoDataFrame.from_features(
                        geojson_data['features'], crs=self.crs)
                    return gdf
                else:
                    return geojson_data
            except Exception as e2:
                print(f"Warning: Error converting to GeoDataFrame: {e2}")
                return geojson_data

    def extract_edges(self, data: Union[gpd.GeoDataFrame, Dict[str, Any]]) -> gpd.GeoDataFrame:
        if isinstance(data, gpd.GeoDataFrame):
            gdf = data.copy()
        else:
            features = []

            if 'features' in data:
                feature_list = data['features']
            elif 'type' in data and data['type'] == 'Feature':
                feature_list = [data]
            else:
                raise ValueError(
                    "Invalid GeoJSON format: must contain 'features' array or be a Feature")

            for feature in feature_list:
                geom = feature.get(self.geometry_key, {})
                if geom.get('type') not in ('LineString', 'MultiLineString'):
                    continue

                props = feature.get(self.properties_key, {})

                if self.filter_property:
                    key = list(self.filter_property.keys())[0]
                    value = list(self.filter_property.values())[0]
                    if props.get(key) != value:
                        continue

                features.append({
                    'geometry': geom,
                    **props
                })

            if not features:
                raise ValueError(
                    "No suitable LineString features found in GeoJSON")

            gdf = gpd.GeoDataFrame(features, crs=self.crs)

        line_mask = gdf.geometry.type.isin(['LineString', 'MultiLineString'])
        if not line_mask.all():
            print(
                f"Warning: Filtering out {(~line_mask).sum()} non-line geometries")
            gdf = gdf[line_mask].copy()

        if len(gdf) == 0:
            raise ValueError("No line geometries found in GeoJSON")

        standardized_gdf = self.mapper.map_dataframe(gdf)

        required_columns = ['geometry', 'highway',
                            'width', 'lanes', 'maxspeed']
        for col in required_columns:
            if col not in standardized_gdf.columns and col != 'geometry':
                standardized_gdf[col] = None

        if 'u' not in standardized_gdf.columns:
            standardized_gdf['u'] = range(len(standardized_gdf))
        if 'v' not in standardized_gdf.columns:
            standardized_gdf['v'] = range(
                len(standardized_gdf), 2*len(standardized_gdf))
        if 'key' not in standardized_gdf.columns:
            standardized_gdf['key'] = 0

        for col in ['width', 'lanes', 'maxspeed', 'length']:
            if col in standardized_gdf.columns:
                standardized_gdf[col] = pd.to_numeric(
                    standardized_gdf[col], errors='coerce')

        self._normalize_highway_values(standardized_gdf)

        if 'length' not in standardized_gdf.columns or standardized_gdf['length'].isna().all():
            standardized_gdf['length'] = standardized_gdf.geometry.length

        return standardized_gdf

    def _normalize_highway_values(self, gdf: gpd.GeoDataFrame) -> None:

        if 'highway' not in gdf.columns:
            return

        highway_mapping = {
            # Numeric codes ""sometimes""" used right ?
            '1': 'motorway',
            '2': 'trunk',
            '3': 'primary',
            '4': 'secondary',
            '5': 'tertiary',
            '6': 'residential',
            '7': 'service',
            '8': 'track',
            '9': 'path',

            # Text mappings
            'interstate': 'motorway',
            'freeway': 'motorway',
            'highway': 'trunk',
            'major': 'primary',
            'arterial': 'primary',
            'collector': 'secondary',
            'minor': 'tertiary',
            'local': 'residential',
            'neighborhood': 'residential',
            'access': 'service',
            'driveway': 'service',
            'alley': 'service',
            'dirt': 'track',
            'trail': 'path',
            'footway': 'footway',
            'sidewalk': 'footway',
            'bike': 'cycleway',
            'bikeway': 'cycleway',
        }

        custom_mapping = self.config.get('highway_mapping', {})
        highway_mapping.update(custom_mapping)

        gdf['highway'] = gdf['highway'].astype(str).str.lower()
        gdf['highway'] = gdf['highway'].map(
            lambda x: highway_mapping.get(x, x))

    def get_supported_formats(self) -> List[str]:

        return ['.geojson', '.json']


adapter_registry.register_adapter(GeoJSONAdapter, 'geojson')
