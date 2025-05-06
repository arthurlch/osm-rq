from .base import StreetDataAdapter, FeatureMapper, adapter_registry
from .osm_adapter import OSMAdapter
from .shapefile_adapter import ShapefileAdapter
from .postgis_adapter import PostGISAdapter
from .geojson_adapter import GeoJSONAdapter


__all__ = [
    'StreetDataAdapter',
    'FeatureMapper',
    'adapter_registry',
    'OSMAdapter',
    'ShapefileAdapter',
    'PostGISAdapter',
    'GeoJSONAdapter',
    'get_adapter',
    'list_adapters'
]


def get_adapter(source: str, adapter_type: str = None, config: dict = None):
    if adapter_type:
        return adapter_registry._adapters[adapter_type](config)
    else:
        return adapter_registry.get_adapter_for_source(source, config)


def list_adapters():

    return adapter_registry.list_adapters()
