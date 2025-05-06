from .base import adapter_registry
import geopandas as gpd
import pandas as pd
import os
from typing import Dict, Any, Optional, List

from .base import StreetDataAdapter, FeatureMapper


class ShapefileAdapter(StreetDataAdapter):

    def __init__(self, config: Optional[Dict[str, Any]] = None):

        super().__init__(config)

        default_mapping = {
            'rd_type': 'highway',
            'road_type': 'highway',
            'type': 'highway',
            'streettype': 'highway',

            'rd_width': 'width',
            'roadwidth': 'width',
            'width_m': 'width',

            'lanes_cnt': 'lanes',
            'num_lanes': 'lanes',
            'lane_count': 'lanes',

            'speed_lim': 'maxspeed',
            'max_speed': 'maxspeed',
            'speed': 'maxspeed',

            'rd_name': 'name',
            'street_nam': 'name',
            'streetname': 'name',

            'oneway': 'oneway',
            'one_way': 'oneway',
            'direction': 'oneway',

            'rd_service': 'service',
            'serv_type': 'service',

            'length_m': 'length',
            'segment_le': 'length',
        }

        user_mapping = self.config.get('feature_mapping', {})
        self.feature_mapping = {**default_mapping, **user_mapping}

        self.mapper = FeatureMapper(self.feature_mapping)

        self.crs = self.config.get('crs', 'EPSG:4326')
        self.encoding = self.config.get('encoding', 'utf-8')

    def load_data(self, source: str) -> gpd.GeoDataFrame:

        if not source.lower().endswith('.shp'):
            source = f"{source}.shp"

        if not os.path.exists(source):
            raise FileNotFoundError(f"Shapefile not found: {source}")

        gdf = gpd.read_file(source, encoding=self.encoding)

        if gdf.crs is None:
            gdf.set_crs(self.crs, inplace=True)
        elif gdf.crs != self.crs:
            gdf = gdf.to_crs(self.crs)

        return gdf

    def extract_edges(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:

        # ensure we have LineString geometries
        line_mask = gdf.geometry.type.isin(['LineString', 'MultiLineString'])
        if not line_mask.all():
            print(
                f"Warning: Filtering out {(~line_mask).sum()} non-line geometries")
            gdf = gdf[line_mask].copy()

        if len(gdf) == 0:
            raise ValueError("No line geometries found in shapefile")

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

        return standardized_gdf

    def _normalize_highway_values(self, gdf: gpd.GeoDataFrame) -> None:

        if 'highway' not in gdf.columns:
            return

        highway_mapping = {
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

        return ['.shp']


adapter_registry.register_adapter(ShapefileAdapter, 'shapefile')
