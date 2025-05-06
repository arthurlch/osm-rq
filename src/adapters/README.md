# Data Source Adapters

This module provides a flexible adapter framework that allows the Street Quality Predictor to work with various data sources and formats beyond standard OpenStreetMap data.

## Overview

The adapter system enables:

1. **Format Compatibility**: Import street data from various formats (OSM, GeoJSON, shapefiles, databases, etc.)
2. **Schema Mapping**: Map custom data schemas to the standardized format used by the quality assessment tools
3. **Source Flexibility**: Use data from local files, URLs, or databases
4. **Configuration**: Customize adapter behavior without code changes

## Available Adapters

| Adapter | Supported Formats | Description |
|---------|-------------------|-------------|
| `OSMAdapter` | `.osm`, `.osm.pbf`, `.pbf` | For standard OpenStreetMap data using OSMnx |
| `GeoJSONAdapter` | `.geojson`, `.json` | For GeoJSON files with street network features |
| `ShapefileAdapter` | `.shp` | For ESRI Shapefiles with street network data |
| `PostGISAdapter` | `postgresql://` | For PostgreSQL/PostGIS databases with street data |

## Using Adapters

### CLI Usage

```bash
# Using the default OSM adapter
python cli.py extract --source "Tokyo, JP"

# Using a GeoJSON adapter
python cli.py extract --source "streets.geojson" --adapter geojson

# Using a shapefile adapter
python cli.py extract --source "streets.shp" --adapter shapefile

# Using a custom configuration
python cli.py extract --source "streets.geojson" --adapter geojson --config geojson_config.json

# Listing available adapters
python cli.py list-adapters
```

### Python API Usage

```python
from src.extract import load_and_process
from src.adapters import get_adapter

# Basic usage with automatic adapter selection
results = load_and_process("Tokyo, JP")

# Using explicit adapter with configuration
config = {
    "feature_mapping": {
        "roadWidth": "width",
        "roadType": "highway"
    }
}
results = load_and_process("streets.geojson", adapter_type="geojson", adapter_config=config)

# Working directly with adapters
adapter = get_adapter("geojson", config=config)
data = adapter.load_data("streets.geojson")
edges = adapter.extract_edges(data)
```

## Custom Configuration

### OSM Adapter

```json
{
    "network_type": "drive",  // 'drive', 'bike', 'walk', or 'all'
    "simplify": true,         // Whether to simplify the network topology
    "retain_all": false       // Whether to retain all nodes or only those in the largest component
}
```

### GeoJSON Adapter

```json
{
    "feature_mapping": {
        "roadWidth": "width",
        "roadType": "highway",
        "speedLimit": "maxspeed",
        "laneCount": "lanes",
        "roadName": "name"
    },
    "crs": "EPSG:4326",           // Coordinate reference system
    "geometry_key": "geometry",   // Key where geometry is stored in the GeoJSON
    "properties_key": "properties", // Key where properties are stored
    "filter_by": {                // Optional filter to select specific features
        "class": "road"
    },
    "highway_mapping": {          // Custom mapping for highway types
        "freeway": "motorway",
        "arterial": "primary",
        "local": "residential"
    }
}
```

### Shapefile Adapter

```json
{
    "feature_mapping": {
        "road_width": "width",
        "road_type": "highway",
        "speed_limit": "maxspeed",
        "lane_count": "lanes",
        "street_name": "name"
    },
    "crs": "EPSG:4326",        // Coordinate reference system
    "encoding": "utf-8",       // Character encoding
    "highway_mapping": {       // Custom mapping for highway types
        "interstate": "motorway",
        "highway": "trunk",
        "major": "primary"
    }
}
```

### PostGIS Adapter

```json
{
    "connection_string": "postgresql://user:password@host:port/dbname",
    "table_name": "streets",
    "geometry_column": "geom",
    "feature_mapping": {
        "road_width": "width",
        "road_type": "highway",
        "speed_limit": "maxspeed"
    },
    "where_clause": "road_type IS NOT NULL",
    "limit": 10000
}
```

## Implementing Custom Adapters

To create a custom adapter for a new data source:

1. Create a new Python module in the `src/adapters` directory
2. Subclass `StreetDataAdapter` and implement the required methods
3. Register your adapter with the registry

Example:

```python
from .base import StreetDataAdapter, adapter_registry

class MyCustomAdapter(StreetDataAdapter):
    def load_data(self, source):
        # Implementation...
        
    def extract_edges(self, data):
        # Implementation...
        
    def get_supported_formats(self):
        return ['.custom', '.myformat']

# Register the adapter
adapter_registry.register_adapter(MyCustomAdapter, 'custom')
```

## Feature Mapping

The `FeatureMapper` class helps map between custom data schemas and the standardized format:

```python
from src.adapters.base import FeatureMapper

# Define mapping between custom field names and OSM tag names
mapping = {
    'roadWidth': 'width',
    'roadType': 'highway',
    'speedLimit': 'maxspeed'
}

# Create mapper and apply to a dataframe
mapper = FeatureMapper(mapping)
standardized_df = mapper.map_dataframe(custom_df)
```