from abc import ABC, abstractmethod
import geopandas as gpd
from typing import Dict, Any, Optional, Union, List, Tuple


class StreetDataAdapter(ABC):

    def __init__(self, config: Optional[Dict[str, Any]] = None):

        self.config = config or {}

    @abstractmethod
    def load_data(self, source: str) -> Any:

        pass

    @abstractmethod
    def extract_edges(self, data: Any) -> gpd.GeoDataFrame:

        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:

        pass

    def process(self, source: str) -> gpd.GeoDataFrame:

        data = self.load_data(source)
        return self.extract_edges(data)


class FeatureMapper:

    def __init__(self, mapping: Dict[str, str]):

        self.mapping = mapping

    def map_dataframe(self, df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:

        result = df.copy()

        rename_dict = {k: v for k, v in self.mapping.items()
                       if k in df.columns}
        if rename_dict:
            result = result.rename(columns=rename_dict)

        return result


class AdapterRegistry:

    def __init__(self):
        self._adapters = {}
        self._extension_map = {}

    def register_adapter(self, adapter_class, name: str):

        adapter_instance = adapter_class()
        self._adapters[name] = adapter_class

        for fmt in adapter_instance.get_supported_formats():
            self._extension_map[fmt] = name

    def get_adapter_for_source(self, source: str, config: Optional[Dict[str, Any]] = None) -> StreetDataAdapter:

        for ext, adapter_name in self._extension_map.items():
            if source.lower().endswith(ext):
                return self._adapters[adapter_name](config)

        if source in self._adapters:
            return self._adapters[source](config)

        raise ValueError(f"No adapter found for source: {source}")

    def list_adapters(self) -> Dict[str, List[str]]:

        result = {}
        for name, adapter_class in self._adapters.items():
            adapter = adapter_class()
            result[name] = adapter.get_supported_formats()
        return result


# global registry instance
adapter_registry = AdapterRegistry()
