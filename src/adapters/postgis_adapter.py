from .base import adapter_registry
import geopandas as gpd
import pandas as pd
import sqlalchemy
from typing import Dict, Any, Optional, List, Union

from .base import StreetDataAdapter, FeatureMapper


class PostGISAdapter(StreetDataAdapter):

    def __init__(self, config: Optional[Dict[str, Any]] = None):

        super().__init__(config)

        self.connection_string = self.config.get('connection_string')
        self.table_name = self.config.get('table_name')

        if not self.connection_string:
            raise ValueError(
                "PostGISAdapter requires 'connection_string' in config")
        if not self.table_name:
            raise ValueError("PostGISAdapter requires 'table_name' in config")

        self.geometry_column = self.config.get('geometry_column', 'geom')
        self.where_clause = self.config.get('where_clause', '')
        self.limit = self.config.get('limit', None)

        default_mapping = {
            'road_type': 'highway',
            'width': 'width',
            'lane_count': 'lanes',
            'speed_limit': 'maxspeed',
            'street_name': 'name',
            'is_oneway': 'oneway',
            'service_type': 'service',
            'length': 'length',
        }

        user_mapping = self.config.get('feature_mapping', {})
        self.feature_mapping = {**default_mapping, **user_mapping}

        self.mapper = FeatureMapper(self.feature_mapping)

    def load_data(self, source: str) -> Union[Dict[str, Any], sqlalchemy.engine.Engine]:
        table_name = source if source and not source.startswith(
            'postgresql://') else self.table_name

        engine = sqlalchemy.create_engine(self.connection_string)

        try:
            with engine.connect() as conn:
                inspector = sqlalchemy.inspect(engine)
                if table_name not in inspector.get_table_names():
                    raise ValueError(
                        f"Table '{table_name}' not found in database")

                columns = [c['name']
                           for c in inspector.get_columns(table_name)]
                if self.geometry_column not in columns:
                    raise ValueError(
                        f"Geometry column '{self.geometry_column}' not found in table '{table_name}'")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")

        return {
            'engine': engine,
            'table_name': table_name,
            'geometry_column': self.geometry_column,
            'where_clause': self.where_clause,
            'limit': self.limit
        }

    def extract_edges(self, db_params: Dict[str, Any]) -> gpd.GeoDataFrame:

        engine = db_params['engine']
        table_name = db_params['table_name']
        geometry_column = db_params['geometry_column']
        where_clause = db_params['where_clause']
        limit = db_params['limit']

        sql = f"SELECT * FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        if limit:
            sql += f" LIMIT {limit}"

        gdf = gpd.read_postgis(
            sql,
            engine,
            geom_col=geometry_column,
            crs="EPSG:4326"
        )

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

        # Convert data types to match expected formats !!
        for col in ['width', 'lanes', 'maxspeed', 'length']:
            if col in standardized_gdf.columns:
                standardized_gdf[col] = pd.to_numeric(
                    standardized_gdf[col], errors='coerce')

        return standardized_gdf

    def get_supported_formats(self) -> List[str]:

        return ['postgresql://', 'postgis://']


adapter_registry.register_adapter(PostGISAdapter, 'postgis')
